"""opt_out: /omk-off-this-session 처리.

세션별 추적 비활성화. omk hooks opt-out 명령 또는 직접 실행으로 호출된다.
"""

from __future__ import annotations

import sys

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT, reset_hud
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.state import (
    STATUS_OPTED_OUT,
    SessionState,
    TimelineEvent,
    now_iso,
)


def _post_opt_out_comment(state: SessionState) -> None:
    """Plane Work Item에 opt-out 알림 댓글을 추가한다. 실패 시 무시."""
    try:
        import httpx
    except ImportError:
        return

    cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return

    wi_ids = state.plane_context.work_item_ids
    project_id = state.plane_context.project_id or cfg.project_id
    if not wi_ids or not project_id:
        return

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key, "Content-Type": "application/json"}
    comment = "-- 사용자 요청에 의해 이 세션의 자동 추적이 중단되었습니다 --"

    for wi_id in wi_ids:
        url = (
            f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
            f"/projects/{project_id}/issues/{wi_id}/comments/"
        )
        try:
            with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
                response = client.post(url, headers=headers, json={"comment_html": comment})
                response.raise_for_status()
        except Exception as e:
            print(
                f"[omk] opt-out 댓글 추가 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
                file=sys.stderr,
            )
            continue


def opt_out(session_id: str) -> None:
    """세션 추적을 중단한다."""
    if not session_id or not session_id.strip():
        print("오류: session_id가 비어있습니다.", file=sys.stderr)
        sys.exit(1)

    state = load_session(session_id)
    if state is None:
        print(f"오류: 세션을 찾을 수 없습니다 — {session_id}", file=sys.stderr)
        sys.exit(1)

    _post_opt_out_comment(state)
    state.opted_out = True
    state.status = STATUS_OPTED_OUT
    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="opted_out",
            summary="사용자 요청에 의한 추적 중단 (Work Item 유지)",
        )
    )
    reset_hud()
    print("세션 추적이 중단되었습니다. 이미 생성된 Plane Work Item은 유지됩니다.")
    save_session(state)
