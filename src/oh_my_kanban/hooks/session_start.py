"""SessionStart 훅: 세션 초기화/복원 및 /compact 후 컨텍스트 재주입.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
stdin: {"session_id": "...", "source": "startup|resume|compact", ...}
stdout: JSON (additionalContext 주입용)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import sys
from typing import Any

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import (
    PLANE_API_TIMEOUT,
    SuccessNudge,
    build_wi_identifier,
    build_wi_url,
    exit_fail_open,
    get_session_id,
    notify_success,
    output_context,
    output_system_message,
    read_hook_input,
    sanitize_comment,
    update_hud,
)
from oh_my_kanban.session.manager import create_session, load_session, save_session
from oh_my_kanban.session.plane_context_builder import build_plane_context
from oh_my_kanban.session.state import (
    FILES_COMPACT_MAX,
    SUMMARY_COMPACT_MAX,
    SUMMARY_RESUME_MAX,
    WORK_ITEMS_DISPLAY_MAX,
    WORK_ITEMS_RESUME_MAX,
    SessionState,
    TimelineEvent,
    now_iso,
)


def _fetch_active_work_items(cfg: Any) -> list[dict]:
    """Plane에서 진행 중인 Work Item 목록을 조회한다. 실패 시 빈 리스트 반환 (fail-open)."""
    try:
        import httpx
    except ImportError:
        return []

    if not cfg.api_key or not cfg.workspace_slug or not cfg.project_id:
        return []

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key}
    url = (
        f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
        f"/projects/{cfg.project_id}/issues/"
    )
    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.get(url, headers=headers, params={"per_page": 10})
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                # In Progress 상태 WI만 반환 (state_detail.group == "started")
                return [
                    r for r in results
                    if isinstance(r, dict)
                    and r.get("state_detail", {}).get("group") in ("started", "in_progress")
                ]
    except Exception as e:
        print(
            f"[omk] 활성 WI 목록 조회 실패 (fail-open): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
    return []


def _inject_new_session_wi_guidance(cfg: Any) -> None:
    """신규 세션 시작 시 진행 중인 WI 목록을 사용자와 Claude에게 안내한다 (ST-18)."""
    active_wis = _fetch_active_work_items(cfg)

    if not active_wis:
        # WI가 없거나 조회 실패: 안내 없이 진행
        return

    # 사용자에게 보이는 systemMessage
    lines = ["[omk] 세션이 시작되었습니다.", "  현재 진행 중인 Task:"]
    for wi in active_wis[:5]:
        seq = wi.get("sequence_id", "")
        name = wi.get("name", "Work Item")[:60]
        state_name = wi.get("state_detail", {}).get("name", "In Progress")
        identifier = f"OMK-{seq}" if seq else "OMK-?"
        lines.append(f"    {identifier}: {name} ({state_name})")
    lines.append(
        "  작업할 Task의 번호를 알려주시거나, 새로운 작업을 시작하시면 자동으로 Task가 생성됩니다."
    )
    user_msg = "\n".join(lines)

    # Claude에게 주입할 additionalContext
    wi_summaries = " | ".join(
        f"OMK-{wi.get('sequence_id', '?')}: {wi.get('name', '')[:40]}"
        for wi in active_wis[:5]
    )
    claude_ctx = (
        f"[omk] 프로젝트에 진행 중인 Work Item이 있습니다.\n"
        f"{wi_summaries}.\n"
        "사용자가 특정 Task를 언급하면 해당 WI에 세션을 연결하세요 (/oh-my-kanban:focus).\n"
        "새로운 주제로 작업을 시작하면 자동으로 새 Task를 생성합니다 (/oh-my-kanban:create-task)."
    )
    output_system_message(user_msg, "SessionStart", claude_ctx)


def _check_blocked_and_cycle_deadline(state: SessionState, cfg: Any) -> None:
    """차단 WI와 Cycle 마감 임박을 감지하여 사용자에게 알린다 (ST-28).

    - 현재 WI가 blocked_by 관계를 가지면 차단 WI 알림
    - 현재 프로젝트에 활성 Cycle이 있고 마감이 3일 이내이면 마감 알림
    - 모두 fail-open
    """
    from datetime import datetime, timezone

    try:
        import httpx
    except ImportError:
        return

    focused_id = state.plane_context.focused_work_item_id
    project_id = state.plane_context.project_id or cfg.project_id
    if not project_id or not cfg.api_key or not cfg.workspace_slug:
        return

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key}

    # 1. 차단 WI 조회 (blocked_by 관계)
    if focused_id:
        try:
            rel_url = (
                f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
                f"/projects/{project_id}/issues/{focused_id}/issue-relations/"
            )
            relations = []
            with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
                resp = client.get(rel_url, headers=headers)
                if resp.status_code == 200:
                    relations = resp.json()
                    if isinstance(relations, dict):
                        relations = relations.get("results", [])
                blocked_by = [
                    r for r in relations
                    if isinstance(r, dict) and r.get("relation_type") == "blocked_by"
                ]
                if blocked_by:
                    blocker_names = []
                    for r in blocked_by[:3]:
                        related = r.get("related_issue", r.get("issue_detail", {}))
                        seq = related.get("sequence_id", "?") if isinstance(related, dict) else "?"
                        name = (
                            related.get("name", "Work Item")
                            if isinstance(related, dict)
                            else "Work Item"
                        )
                        blocker_names.append(f"OMK-{seq} ({name[:40]})")
                    blockers_str = "\n".join(f"  - {b}" for b in blocker_names)
                    output_system_message(
                        f"[omk] 주의: 현재 Task가 차단되어 있습니다.\n"
                        f"  차단 중인 Work Item:\n{blockers_str}"
                    )
        except Exception as e:
            print(
                f"[omk] 차단 WI 조회 실패 (fail-open): {type(e).__name__}: {e}",
                file=sys.stderr,
            )

    # 2. Cycle 마감 임박 조회 (3일 이내)
    try:
        cycle_url = (
            f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
            f"/projects/{project_id}/cycles/"
        )
        data = {}
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.get(cycle_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
        cycles = data.get("results", []) if isinstance(data, dict) else (data if data else [])
        if cycles:
            now = datetime.now(timezone.utc)

            for cycle in cycles:
                if not isinstance(cycle, dict):
                    continue
                status = cycle.get("status", "")
                if status not in ("current", "in_progress", ""):
                    continue
                end_date_str = cycle.get("end_date") or cycle.get("end_at")
                if not end_date_str:
                    continue
                try:
                    # end_date는 "2026-03-10" 또는 "2026-03-10T..." 형식
                    if "T" not in end_date_str:
                        end_date_str += "T23:59:59+00:00"
                    end_dt = datetime.fromisoformat(end_date_str)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    days_left = (end_dt - now).days
                    if 0 <= days_left <= 3:
                        cycle_name = cycle.get("name", "Sprint")
                        output_system_message(
                            f"[omk] {cycle_name} 마감 {days_left}일 전입니다.\n"
                            f"  미완료 Task 상태를 확인해보세요."
                        )
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        print(
            f"[omk] Cycle 마감 조회 실패 (fail-open): {type(e).__name__}: {e}",
            file=sys.stderr,
        )


def _get_task_mode(cfg: Any) -> str:
    """설정에서 task_mode를 읽는다. 기본값: 'main-sub'."""
    return getattr(cfg, "task_mode", "main-sub") or "main-sub"


def _apply_task_labels(
    wi_id: str,
    cfg: Any,
    *,
    project_id: str = "",
    is_main: bool = True,
) -> None:
    """WI에 omk 표준 라벨(omk:session, omk:type:main/sub)을 적용한다.

    실패 시 fail-open으로 처리 — 라벨 적용 실패가 훅을 실패시키지 않는다.

    Args:
        wi_id: 라벨을 적용할 WI UUID.
        cfg: Config 객체.
        is_main: True면 omk:type:main, False면 omk:type:sub 라벨 적용.
    """
    try:
        import httpx

        from oh_my_kanban.hooks.label_conventions import get_label_id_by_name
    except ImportError:
        return

    project_id = project_id or cfg.project_id
    if not project_id or not cfg.api_key or not cfg.workspace_slug:
        return

    # 적용할 라벨 이름 목록
    label_names = ["omk:session"]
    label_names.append("omk:type:main" if is_main else "omk:type:sub")

    # 라벨 ID 조회
    label_ids = []
    for name in label_names:
        label_id = get_label_id_by_name(name, project_id, cfg)
        if label_id:
            label_ids.append(label_id)

    if not label_ids:
        return

    # WI에 라벨 적용 (PATCH)
    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key, "Content-Type": "application/json"}
    url = (
        f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
        f"/projects/{project_id}/issues/{wi_id}/"
    )
    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.patch(url, headers=headers, json={"label_ids": label_ids})
        if resp.status_code not in (200, 201):
            print(
                f"[omk] WI 라벨 PATCH HTTP {resp.status_code} (wi_id={wi_id!r})",
                file=sys.stderr,
            )
    except Exception as e:
        print(
            f"[omk] WI 라벨 적용 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )


def _get_git_info() -> tuple[str, str]:
    """현재 git 브랜치명과 저장소 이름을 반환한다. 실패 시 빈 문자열 반환."""
    import subprocess
    branch = ""
    repo = ""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False, timeout=3,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False, timeout=3,
        )
        if result.returncode == 0:
            raw = result.stdout.strip()
            # "git@github.com:org/repo.git" 또는 "https://github.com/org/repo.git" 형식 파싱
            import re as _re
            m = _re.search(r'[:/]([^/]+/[^/]+?)(?:\.git)?$', raw)
            repo = m.group(1) if m else raw.split("/")[-1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return branch, repo


def _post_session_start_comment(state: SessionState, cfg: Any) -> None:
    """Plane Work Item에 세션 시작 댓글을 추가한다. 실패 시 무시 (fail-open)."""
    # ST-25: format_preset=eco이면 세션 시작 댓글 생략
    format_preset = getattr(cfg, "format_preset", "normal")
    if format_preset == "eco":
        return

    try:
        import httpx
    except ImportError:
        return

    wi_ids = state.plane_context.work_item_ids
    focused_id = state.plane_context.focused_work_item_id
    target_ids = [focused_id] if focused_id else wi_ids[:1]
    project_id = state.plane_context.project_id or cfg.project_id

    if not target_ids or not project_id or not cfg.api_key or not cfg.workspace_slug:
        return

    session_id_short = state.session_id[:8]
    start_time = state.created_at[:19].replace("T", " ")  # YYYY-MM-DD HH:MM:SS

    # OMK-7: git 브랜치/저장소 정보 조회
    branch, repo = _get_git_info()

    if format_preset == "detailed":
        # detailed: 더 많은 정보 포함
        files_str = ", ".join(f"`{f}`" for f in state.stats.files_touched[:5]) or "없음"
        lines = [
            "## omk 세션 시작",
            "",
            f"**세션 ID**: `{session_id_short}...`",
            f"**시작 시각**: {start_time} UTC",
            f"**목표**: {state.scope.summary[:200] if state.scope.summary else '미설정'}",
            f"**이전 수정 파일**: {files_str}",
            f"**누적 요청 수**: {state.stats.total_prompts}회",
        ]
        if branch:
            lines.append(f"**브랜치**: `{branch}`")
        if repo:
            lines.append(f"**저장소**: `{repo}`")
        comment_body = "\n".join(lines)
    else:
        # normal: 기본 정보
        lines = [
            "## omk 세션 시작",
            "",
            f"**세션 ID**: `{session_id_short}...`",
            f"**시작 시각**: {start_time} UTC",
            f"**목표**: {state.scope.summary[:200] if state.scope.summary else '미설정'}",
        ]
        if branch:
            lines.append(f"**브랜치**: `{branch}`")
        if repo:
            lines.append(f"**저장소**: `{repo}`")
        comment_body = "\n".join(lines)
    comment_html = sanitize_comment(comment_body)

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key, "Content-Type": "application/json"}

    for wi_id in target_ids:
        url = (
            f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
            f"/projects/{project_id}/issues/{wi_id}/comments/"
        )
        try:
            with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
                resp = client.post(url, headers=headers, json={"comment_html": comment_html})
            if resp.status_code not in (200, 201):
                print(
                    f"[omk] 세션 시작 댓글 HTTP {resp.status_code} (wi_id={wi_id!r})",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"[omk] 세션 시작 댓글 추가 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
                file=sys.stderr,
            )
            continue


def _notify_wi_connected(state: SessionState, cfg: Any) -> None:
    """WI 연결 성공을 사용자에게 알린다 (systemMessage)."""
    wi_ids = state.plane_context.work_item_ids
    focused_id = state.plane_context.focused_work_item_id or (wi_ids[0] if wi_ids else None)
    if not focused_id:
        return

    # WI 정보 조회 시도 (실패 시 기본값 사용)
    wi_name = "Work Item"
    wi_sequence = 0
    try:
        import httpx
        project_id = state.plane_context.project_id or cfg.project_id
        if project_id and cfg.api_key and cfg.workspace_slug:
            base_url = cfg.base_url.rstrip("/")
            headers = {"X-API-Key": cfg.api_key}
            url = (
                f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
                f"/projects/{project_id}/issues/{focused_id}/"
            )
            with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    wi_name = data.get("name", "Work Item")
                    wi_sequence = data.get("sequence_id", 0)
    except Exception as e:
        print(
            f"[omk] WI 정보 조회 실패 (fail-open, 기본값 사용): {type(e).__name__}: {e}",
            file=sys.stderr,
        )

    project_id = state.plane_context.project_id or cfg.project_id
    wi_url = (
        build_wi_url(cfg.base_url, cfg.workspace_slug, project_id, wi_sequence)
        if wi_sequence
        else ""
    )
    wi_identifier = build_wi_identifier(wi_sequence) if wi_sequence else "WI"

    update_hud(wi_identifier, wi_name, "연결됨")

    nudge = SuccessNudge(
        wi_identifier=wi_identifier,
        wi_name=wi_name,
        wi_url=wi_url,
    )
    notify_success(nudge, hook_name="SessionStart")


def _handle_compact(session_id: str) -> None:
    """compact 직후 세션 목표/파일/진행 상황을 Claude 컨텍스트에 재주입한다."""
    state = load_session(session_id)
    if state is None:
        exit_fail_open()
        return

    scope = state.scope
    stats = state.stats

    scope_summary = scope.summary[:SUMMARY_COMPACT_MAX] if scope.summary else "목표 미설정"
    topics = ", ".join(scope.topics) if scope.topics else "없음"
    expanded = ", ".join(scope.expanded_topics) if scope.expanded_topics else ""
    files = ", ".join(stats.files_touched[:FILES_COMPACT_MAX]) if stats.files_touched else "없음"

    wi_ids = state.plane_context.work_item_ids
    wi_text = f"\nPlane Work Items: {', '.join(wi_ids[:WORK_ITEMS_DISPLAY_MAX])}" if wi_ids else ""

    context_lines = [
        "[omk: 컨텍스트 압축 후 복원]",
        f"세션 목표: {scope_summary}",
        f"핵심 토픽: {topics}" + (f" + 확장: {expanded}" if expanded else ""),
        f"수정 파일: {files}",
        f"진행: 요청 {stats.total_prompts}회, 이탈 경고 {stats.drift_warnings}회",
    ]
    if wi_text:
        context_lines.append(wi_text.strip())

    # Plane Work Item 내용 조회 — compact 후 Claude가 일일이 API 호출하는 토큰 낭비 방지
    plane_content = ""
    if wi_ids:
        cfg = load_config()
        project_id = state.plane_context.project_id or cfg.project_id
        if project_id and cfg.api_key and cfg.workspace_slug:
            plane_content = build_plane_context(
                work_item_ids=wi_ids,
                project_id=project_id,
                base_url=cfg.base_url,
                api_key=cfg.api_key,
                workspace_slug=cfg.workspace_slug,
            )

    if plane_content:
        context_lines.append("\n[Plane Work Item 상세]")
        context_lines.append(plane_content)

    output_context("SessionStart", "\n".join(context_lines))

    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="compact_restored",
            summary="컨텍스트 압축 후 복원",
        )
    )
    save_session(state)


def _handle_startup_or_resume(session_id: str, source: str) -> None:
    """세션 시작 또는 재개 처리: 파일 초기화/복원 후 Plane 설정 연결."""
    state = load_session(session_id)

    if state is None:
        # 신규 세션
        state = create_session(session_id)
        state.timeline.append(
            TimelineEvent(
                timestamp=now_iso(),
                type="scope_init",
                summary=f"세션 시작 (source: {source})",
            )
        )
    else:
        # 기존 세션 재개
        state.timeline.append(
            TimelineEvent(
                timestamp=now_iso(),
                type="scope_init",
                summary=f"세션 재개 (source: {source})",
            )
        )

    # Plane 설정 있으면 project_id 연결, 신규 세션이면 drift 설정도 복사
    cfg = load_config()
    if cfg.project_id and not state.plane_context.project_id:
        state.plane_context.project_id = cfg.project_id
    # 신규 세션 생성 직후(create_session은 기본값으로 초기화)에만 config 값 복사
    # 기존 세션 재개 시에는 세션 파일에 저장된 값 유지
    if state.stats.total_prompts == 0:
        state.config.sensitivity = cfg.drift_sensitivity
        state.config.cooldown = cfg.drift_cooldown

    # Plane 미설정 시 첫 세션에서만 stderr 안내 (ErrorThrottle 적용)
    if not cfg.api_key and state.stats.total_prompts == 0:
        print(
            "[omk/SessionStart] Plane API 키 미설정. omk setup으로 설정하세요.",
            file=sys.stderr,
        )

    save_session(state)

    # WI가 연결된 경우 세션 시작 댓글 추가 및 성공 알림
    if state.plane_context.work_item_ids:
        _post_session_start_comment(state, cfg)
        _notify_wi_connected(state, cfg)
        # task_mode에 따라 WI에 omk 표준 라벨 적용 (fail-open)
        focused_id = state.plane_context.focused_work_item_id
        target_wi = focused_id or state.plane_context.work_item_ids[0]
        task_mode = _get_task_mode(cfg)
        is_main = task_mode == "main-sub"
        _apply_task_labels(
            target_wi,
            cfg,
            project_id=state.plane_context.project_id or cfg.project_id,
            is_main=is_main,
        )
        # ST-28: 차단 WI / Cycle 마감 알림 (fail-open)
        if source in ("startup", "resume") and cfg.api_key:
            try:
                _check_blocked_and_cycle_deadline(state, cfg)
            except Exception as e:
                print(
                    f"[omk] 차단/마감 알림 실패 (fail-open): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )
    elif source == "startup":
        # ST-18: 신규 세션이고 WI가 연결되지 않은 경우: 활성 WI 목록 안내
        _inject_new_session_wi_guidance(cfg)

    # ST-19: 세션 재개이고 핸드오프 메모가 있으면 사용자에게 표시
    if source == "resume" and state.handoff_note:
        handoff_user_msg = (
            f"[omk] 이전 세션 메모:\n"
            f"  {state.handoff_note[:300]}"
        )
        handoff_claude_ctx = (
            f"[omk] 이전 세션 핸드오프 메모: {state.handoff_note[:300]}\n"
            "이 메모를 참고하여 작업을 이어가세요."
        )
        output_system_message(handoff_user_msg, "SessionStart", handoff_claude_ctx)

    # 재개 세션이고 scope가 있으면 컨텍스트 재주입
    # (알려진 버그 #10373: 새 세션 SessionStart에서는 stdout 주입이 실패할 수 있음)
    if source == "resume" and state.scope.summary:
        wi_ids = state.plane_context.work_item_ids
        wi_text = f" | Plane WI: {', '.join(wi_ids[:WORK_ITEMS_RESUME_MAX])}" if wi_ids else ""
        context = (
            f"[omk: 세션 재개] {state.scope.summary[:SUMMARY_RESUME_MAX]}"
            f" | 요청 {state.stats.total_prompts}회{wi_text}"
        )
        output_context("SessionStart", context)


def main() -> None:
    """SessionStart 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
    try:
        hook_input = read_hook_input()
        session_id = get_session_id(hook_input)
        if not session_id:
            exit_fail_open()
            return

        # source 필드: "startup" | "resume" | "compact" | "" (알 수 없음)
        source = str(hook_input.get("source", "startup"))

        if source == "compact":
            _handle_compact(session_id)
        else:
            _handle_startup_or_resume(session_id, source)

    except Exception as e:
        print(f"[omk] SessionStart 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        exit_fail_open()
        return


if __name__ == "__main__":
    main()
