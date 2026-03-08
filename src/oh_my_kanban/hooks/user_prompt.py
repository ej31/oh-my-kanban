"""UserPromptSubmit 훅: 프롬프트 카운트, 스코프 초기화, 드리프트 감지.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
stdin: {"session_id": "...", "prompt": "...", ...}
stdout: JSON (additionalContext 주입용 — 드리프트 경고 시)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import (
    PLANE_API_TIMEOUT,
    exit_fail_open,
    get_session_id,
    output_context,  # noqa: F401 — 테스트에서 패치 대상으로 사용
    output_system_message,
    validate_plane_url_params,
    read_hook_input,
)
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.scope import (
    compute_drift_score,
    expand_scope,
    init_scope,
    should_suppress_warning,
)
from oh_my_kanban.session.state import TimelineEvent, now_iso

# ST-20: 댓글 폴링 상수
_COMMENT_POLL_INTERVAL_SEC = 120   # 2분 throttle
_COMMENT_POLL_MAX_FAILURES = 3     # 연속 실패 circuit breaker 임계값
_SUBTASK_CHECK_INTERVAL_SEC = 120
_SUBTASK_CHECK_MAX_FAILURES = 3


def _poll_comments(state, cfg) -> None:
    """Plane WI 댓글을 폴링하여 새 댓글이 있으면 사용자에게 알린다 (ST-20).

    - 2분 throttle: last_comment_check 이후 2분 미경과 시 건너뜀
    - Circuit breaker: comment_poll_failures >= 3이면 건너뜀
    - 새 댓글 발견 시 output_system_message로 사용자에게 알림
    """
    plane_ctx = state.plane_context
    # auto_created_task_id가 있으면 Main Task를 폴링 대상으로 우선 사용
    focused_id = getattr(plane_ctx, "auto_created_task_id", None) or plane_ctx.focused_work_item_id
    if not focused_id:
        return

    # circuit breaker
    if plane_ctx.comment_poll_failures >= _COMMENT_POLL_MAX_FAILURES:
        return

    # 2분 throttle
    now_dt = datetime.now(timezone.utc)
    if plane_ctx.last_comment_check:
        try:
            last_dt = datetime.fromisoformat(plane_ctx.last_comment_check)
            elapsed = (now_dt - last_dt).total_seconds()
            if elapsed < _COMMENT_POLL_INTERVAL_SEC:
                return
        except (ValueError, TypeError):
            pass

    project_id = plane_ctx.project_id or cfg.project_id
    if not project_id or not cfg.api_key or not cfg.workspace_slug:
        return

    workspace_slug = cfg.workspace_slug
    if not validate_plane_url_params(workspace_slug, project_id, focused_id):
        return

    try:
        import httpx
    except ImportError:
        return

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key}
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/issues/{focused_id}/comments/"
    )
    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            plane_ctx.comment_poll_failures += 1
            plane_ctx.last_comment_check = now_dt.isoformat()
            return

        data = resp.json()
        comments = data.get("results", [])
        known_ids = set(plane_ctx.known_comment_ids)

        new_comments = [c for c in comments if str(c.get("id", "")) not in known_ids]
        # omk 자체 댓글은 알림에서 제외 (## omk로 시작하는 댓글)
        new_comments = [
            c for c in new_comments
            if not str(
                c.get("comment_stripped", "") or c.get("comment_html", "")
            ).startswith("## omk")
        ]

        if new_comments:
            # 사용자에게 새 댓글 알림
            for comment in new_comments[:3]:
                actor = comment.get("actor_detail", {})
                author = actor.get("display_name") or actor.get("email") or "팀원"
                body = str(comment.get("comment_stripped", "") or "")[:100]
                msg = (
                    f"[omk] 새로운 의견이 접수되었습니다.\n"
                    f"  💬 {author}: \"{body}\""
                )
                output_system_message(msg)

        # known_comment_ids 및 폴링 타임스탬프 업데이트
        plane_ctx.known_comment_ids = list(known_ids | {str(c.get("id", "")) for c in comments})
        plane_ctx.last_comment_check = now_dt.isoformat()
        plane_ctx.comment_poll_failures = 0  # 성공 시 circuit breaker 초기화

    except Exception as e:
        plane_ctx.comment_poll_failures += 1
        plane_ctx.last_comment_check = now_dt.isoformat()
        print(
            "[omk] 댓글 폴링 실패"
            f" ({plane_ctx.comment_poll_failures}/{_COMMENT_POLL_MAX_FAILURES}): "
            f"{type(e).__name__}: {e}",
            file=sys.stderr,
        )


def _check_subtask_completion(state, cfg) -> None:
    """현재 WI의 모든 sub-task가 완료됐으면 사용자에게 알린다 (ST-26).

    - subtask_completion_nudged_ids에 focused WI가 있으면 중복 알림 방지
    - sub-task 없으면 알리지 않음
    - API 실패 시 fail-open
    """
    plane_ctx = state.plane_context
    # auto_created_task_id가 있으면 Main Task를 폴링 대상으로 우선 사용
    focused_id = getattr(plane_ctx, "auto_created_task_id", None) or plane_ctx.focused_work_item_id
    if not focused_id:
        return
    if focused_id in plane_ctx.subtask_completion_nudged_ids:
        return
    if plane_ctx.subtask_check_failures >= _SUBTASK_CHECK_MAX_FAILURES:
        return

    now_dt = datetime.now(timezone.utc)
    if plane_ctx.last_subtask_check:
        try:
            last_dt = datetime.fromisoformat(plane_ctx.last_subtask_check)
            elapsed = (now_dt - last_dt).total_seconds()
            if elapsed < _SUBTASK_CHECK_INTERVAL_SEC:
                return
        except (ValueError, TypeError):
            pass

    project_id = plane_ctx.project_id or cfg.project_id
    if not project_id or not cfg.api_key or not cfg.workspace_slug:
        return

    workspace_slug = cfg.workspace_slug
    if not validate_plane_url_params(workspace_slug, project_id, focused_id):
        return

    try:
        import httpx
    except ImportError:
        return

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key}
    # 현재 WI의 하위 이슈(sub-tasks) 조회
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/issues/{focused_id}/sub-issues/"
    )
    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code != 200:
            plane_ctx.last_subtask_check = now_dt.isoformat()
            plane_ctx.subtask_check_failures += 1
            return

        data = resp.json()
        sub_issues = data.get("results", data if isinstance(data, list) else [])
        if not sub_issues:
            return  # sub-task 없으면 알리지 않음

        # 모두 완료 그룹인지 확인
        all_done = all(
            isinstance(s, dict)
            and s.get("state_detail", {}).get("group") in ("completed", "cancelled")
            for s in sub_issues
        )
        if not all_done:
            return

        # 모두 완료됨 → 사용자에게 알림
        count = len(sub_issues)
        output_system_message(
            f"[omk] 연결된 Work Item의 하위 Task {count}개가 모두 완료되었습니다!\n"
            f"  /oh-my-kanban:done 으로 메인 Task를 완료 처리할 수 있습니다."
        )
        plane_ctx.subtask_completion_nudged_ids = [
            *plane_ctx.subtask_completion_nudged_ids,
            focused_id,
        ]
        plane_ctx.last_subtask_check = now_dt.isoformat()
        plane_ctx.subtask_check_failures = 0

    except Exception as e:
        plane_ctx.last_subtask_check = now_dt.isoformat()
        plane_ctx.subtask_check_failures += 1
        print(
            f"[omk] sub-task 완료 체크 실패 (fail-open): {type(e).__name__}: {e}",
            file=sys.stderr,
        )


def main() -> None:
    """UserPromptSubmit 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
    try:
        hook_input = read_hook_input()
        session_id = get_session_id(hook_input)
        if not session_id:
            exit_fail_open()
            return

        state = load_session(session_id)
        if state is None:
            exit_fail_open()
            return
        if state.opted_out:
            exit_fail_open()
            return

        # 1. 프롬프트 카운트
        prompt_text = str(hook_input.get("prompt", ""))
        state.stats.total_prompts += 1

        # 2. 스코프 초기화 시도 (첫 번째 또는 scope가 비어있을 때)
        if not state.scope.tokens:
            init_scope(state, prompt_text)

        # 3. 쿨다운 처리
        if state.stats.cooldown_remaining > 0:
            state.stats.cooldown_remaining -= 1
            state.timeline.append(
                TimelineEvent(
                    timestamp=now_iso(),
                    type="prompt",
                    summary=prompt_text[:100] if prompt_text else "(빈 프롬프트)",
                )
            )
            save_session(state)
            sys.exit(0)

        # 4. 스코프가 충분히 초기화되지 않으면 바로 저장 후 종료
        if not state.scope.tokens:
            state.timeline.append(
                TimelineEvent(
                    timestamp=now_iso(),
                    type="prompt",
                    summary=prompt_text[:100] if prompt_text else "(빈 프롬프트)",
                )
            )
            save_session(state)
            sys.exit(0)

        # 5. 설정 로드 (드리프트 처리 및 폴링에서 공통 사용)
        cfg = load_config()

        # 6. 드리프트 감지 (세션 sensitivity 값 전달)
        drift = compute_drift_score(
            state.scope,
            prompt_text,
            state.stats.files_touched,
            sensitivity=state.config.sensitivity,
        )

        # suppressed 판정: 프롬프트에 명시적 전환 패턴이 있으면 경고 억제
        if drift.level in ("significant", "major"):
            drift.suppressed = should_suppress_warning(prompt_text)

        # 7. 드리프트 레벨별 처리
        if drift.level == "none":
            pass  # 정상
        elif drift.level == "minor":
            if state.config.auto_expand:
                expand_scope(state, prompt_text)
                state.stats.scope_expansions += 1
                state.timeline.append(
                    TimelineEvent(
                        timestamp=now_iso(),
                        type="scope_expanded",
                        summary=f"스코프 확장 (minor drift, score={drift.score:.3f})",
                        drift_score=drift.score,
                        drift_level="minor",
                    )
                )
        elif drift.level in ("significant", "major"):
            if drift.suppressed:
                # suppressed -> minor처럼 scope 확장, 이력은 남김
                if state.config.auto_expand:
                    expand_scope(state, prompt_text)
                    state.stats.scope_expansions += 1
                    state.timeline.append(
                        TimelineEvent(
                            timestamp=now_iso(),
                            type="scope_expanded",
                            summary=(
                                f"스코프 확장 (suppressed {drift.level},"
                                f" score={drift.score:.3f})"
                            ),
                            drift_score=drift.score,
                            drift_level=drift.level,
                        )
                    )
            else:
                # ST-21: 경고 주입 — 사용자 + Claude 이중 채널
                state.stats.drift_warnings += 1
                state.stats.cooldown_remaining = state.config.cooldown
                state.timeline.append(
                    TimelineEvent(
                        timestamp=now_iso(),
                        type="drift_detected",
                        summary=f"드리프트 감지 (level={drift.level}, score={drift.score:.3f})",
                        drift_score=drift.score,
                        drift_level=drift.level,
                    )
                )
                # 사용자에게 보이는 메시지 (systemMessage)
                scope_short = state.scope.summary[:50] if state.scope.summary else "미설정"
                user_msg = (
                    f"[omk] 현재 작업이 원래 목표({scope_short})에서 벗어난 것 같습니다.\n"
                    f"  별도 Task로 등록할까요? (계속 진행하셔도 됩니다)"
                )
                # Claude에게 주입할 상세 프로토콜 (additionalContext)
                scope_full = state.scope.summary[:100] if state.scope.summary else "미설정"
                claude_protocol = (
                    f"[omk drift 경고] 현재 요청이 세션 범위에서 벗어났습니다.\n"
                    f"level={drift.level}, score={drift.score:.2f}. 범위: {scope_full}.\n\n"
                    "사용자에게 새 Task 생성을 이미 제안했습니다 (systemMessage로 표시됨).\n"
                    "사용자 응답에 따라 아래를 실행하세요:\n\n"
                    "■ 긍정 응답 시 (응/네/좋아/만들어/별도로 등):\n"
                    "  1. 기존 WI 상태 → 'On Hold' (mcp__plane__list_states로 동적 조회)\n"
                    "  2. 기존 WI에 'omk 작업 일시 중단 (드리프트)' 댓글\n"
                    "  3. 새 WI 생성 (프롬프트에서 작업명 추론, In Progress)\n"
                    "  4. relates_to 관계 설정\n"
                    "  5. 새 WI에 'omk 세션 연결 (드리프트 전환)' 댓글\n"
                    "  결과를 [omk] 형식으로 보고\n\n"
                    "■ 부정 응답 시 (아니/괜찮아/그냥 계속/무시 등):\n"
                    "  scope 확장 + '[omk] 현재 작업 범위를 확장합니다.' 안내"
                )
                output_system_message(user_msg, "UserPromptSubmit", claude_protocol)

                # Sub Task WI 자동 생성 (main-sub 모드 + Main Task 존재 시)
                try:
                    if (
                        cfg.task_mode == "main-sub"
                        and getattr(state.plane_context, "auto_created_task_id", None)
                    ):
                        from oh_my_kanban.session.task_format import apply_task_format
                        from oh_my_kanban.providers import get_provider_client, get_provider_name
                        _provider = get_provider_client(get_provider_name(cfg, state), cfg)
                        apply_task_format(state, cfg, _provider, "drift_detected", prompt_text)
                except Exception as _e:
                    print(
                        f"[omk] Sub Task WI 생성 실패 (fail-open): {type(_e).__name__}",
                        file=sys.stderr,
                    )

        # 7. ST-20: 팀원 댓글 폴링 (2분 throttle + circuit breaker)
        try:
            if cfg.api_key:
                _poll_comments(state, cfg)
                # ST-26: sub-task 전체 완료 → 완료 처리 유도
                _check_subtask_completion(state, cfg)
        except Exception as e:
            print(
                f"[omk] 댓글 폴링 중 예외 (fail-open): {type(e).__name__}: {e}",
                file=sys.stderr,
            )

        # 8. 타임라인에 prompt 이벤트 추가
        state.timeline.append(
            TimelineEvent(
                timestamp=now_iso(),
                type="prompt",
                summary=prompt_text[:100] if prompt_text else "(빈 프롬프트)",
                drift_score=drift.score if state.scope.tokens else None,
            )
        )

        save_session(state)

    except Exception as e:
        print(
            f"[omk] UserPromptSubmit 훅 예외 (fail-open): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        exit_fail_open()


if __name__ == "__main__":
    main()
