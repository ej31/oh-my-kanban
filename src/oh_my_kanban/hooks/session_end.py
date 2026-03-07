"""SessionEnd 훅: 세션 요약 생성 + Plane Work Item 댓글 단일 API 호출.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
timeout: 30초 (settings.json에 명시)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import sys

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import (
    exit_fail_open,
    get_session_id,
    read_hook_input,
    record_health_warning,
)
from oh_my_kanban.hooks.http_client import build_plane_headers, plane_http_client, plane_request
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.state import (
    FILES_DISPLAY_MAX,
    SESSION_ID_DISPLAY_LEN,
    STATUS_COMPLETED,
    STATUS_OPTED_OUT,
    SUMMARY_DISPLAY_MAX,
    SessionState,
    TimelineEvent,
    now_iso,
)


def _build_summary_comment(state: SessionState) -> str:
    """세션 종료 시 Plane Work Item에 달 댓글 내용을 생성한다."""
    scope = state.scope
    stats = state.stats

    lines = [
        "## omk 세션 종료",
        "",
        f"**목표**: {scope.summary[:SUMMARY_DISPLAY_MAX] if scope.summary else '미설정'}",
        "",
        "**통계**",
        f"- 요청 횟수: {stats.total_prompts}회",
        f"- 수정 파일: {len(stats.files_touched)}개",
        f"- 범위 이탈 경고: {stats.drift_warnings}회",
        f"- 범위 자동 확장: {stats.scope_expansions}회",
    ]

    if stats.files_touched:
        lines.append("")
        lines.append("**수정된 파일**")
        for f in stats.files_touched[:FILES_DISPLAY_MAX]:
            lines.append(f"- `{f}`")
        if len(stats.files_touched) > FILES_DISPLAY_MAX:
            lines.append(f"- ...외 {len(stats.files_touched) - FILES_DISPLAY_MAX}개")

    if scope.topics:
        lines.append("")
        lines.append(f"**주요 토픽**: {', '.join(scope.topics)}")

    lines.append("")
    lines.append(f"*세션 ID: {state.session_id[:SESSION_ID_DISPLAY_LEN]}...*")
    return "\n".join(lines)


def _post_plane_comment(state: SessionState, comment: str) -> bool:
    """Plane Work Item에 댓글을 추가한다. 성공 여부를 반환한다."""
    try:
        import httpx
    except ImportError:
        return False

    cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return False

    wi_ids = state.plane_context.work_item_ids
    project_id = state.plane_context.project_id or cfg.project_id

    if not wi_ids or not project_id:
        return False

    base_url = cfg.base_url.rstrip("/")

    success_count = 0
    failure_count = 0
    try:
        with plane_http_client(cfg.api_key) as client:
            for wi_id in wi_ids:
                url = (
                    f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
                    f"/projects/{project_id}/issues/{wi_id}/comments/"
                )
                try:
                    resp = plane_request(
                        client, "POST", url,
                        json={"comment_html": comment},
                        context=f"댓글 추가 wi_id={wi_id}",
                    )
                    if resp.status_code in (200, 201):
                        success_count += 1
                    else:
                        failure_count += 1
                        print(f"[omk] Plane 댓글 추가 HTTP {resp.status_code} (wi_id={wi_id!r})", file=sys.stderr)
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    failure_count += 1
                    print(f"[omk] Plane 댓글 추가 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}", file=sys.stderr)
                    continue
                except Exception as e:
                    failure_count += 1
                    print(f"[omk] Plane 댓글 추가 중 예외 (wi_id={wi_id!r}): {type(e).__name__}: {e}", file=sys.stderr)
                    continue
    except Exception as e:
        print(f"[omk] Plane 클라이언트 생성 실패: {type(e).__name__}: {e}", file=sys.stderr)
        return False

    if failure_count > 0:
        print(f"[omk] Plane 댓글 동기화: {success_count} 성공, {failure_count} 실패", file=sys.stderr)
    return success_count > 0 and failure_count == 0


def main() -> None:
    """SessionEnd 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
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

        # opted_out이면 Plane 동기화 없이 상태만 갱신
        if state.opted_out:
            state.status = STATUS_OPTED_OUT
            state.timeline.append(
                TimelineEvent(
                    timestamp=now_iso(),
                    type="opted_out",
                    summary="opted_out 세션 종료",
                )
            )
            save_session(state)
            exit_fail_open()
            return

        # 세션 완료 처리
        state.status = STATUS_COMPLETED
        state.timeline.append(
            TimelineEvent(
                timestamp=now_iso(),
                type="prompt",
                summary="세션 정상 종료",
            )
        )

        # Plane Work Item 댓글 추가 (설정이 있는 경우)
        if state.plane_context.work_item_ids:
            comment = _build_summary_comment(state)
            _post_plane_comment(state, comment)

        save_session(state)

    except Exception as e:
        print(f"[omk] SessionEnd 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        record_health_warning({
            "type": "session_end_failure",
            "error": f"{type(e).__name__}: {e}",
            "timestamp": now_iso(),
        })
        exit_fail_open()


if __name__ == "__main__":
    main()
