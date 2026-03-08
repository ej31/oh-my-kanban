"""oh-my-kanban MCP 서버.

Claude Code가 세션 상태를 능동적으로 조회·수정할 수 있도록
5개의 MCP tool을 노출한다.

실행:
    uv run python -m oh_my_kanban.mcp.server
    또는
    omk mcp serve
"""

from __future__ import annotations

import re
from typing import Any

# mcp 패키지 import — 선택적 의존성이므로 ImportError를 그대로 전파한다.
# 실행 진입점(mcp_cmd.py)에서 ImportError를 catch해 사용자에게 안내한다.
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    raise ImportError(
        "mcp 패키지가 설치되지 않았습니다. "
        "설치 방법: pip install 'oh-my-kanban[mcp]'"
    ) from e

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT, sanitize_comment
from oh_my_kanban.session.manager import list_sessions, load_session, save_session
from oh_my_kanban.session.state import STATUS_ACTIVE, TimelineEvent, now_iso

# UUID v4 형식 검증 정규식 (Plane Work Item ID는 UUID v4)
_UUID_RE = re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
)

# MCP 서버 인스턴스 — 이름은 Claude Code 설정의 key와 일치시킨다
mcp = FastMCP("oh-my-kanban")


def _find_active_session_id() -> str | None:
    """최근 활성 세션 ID를 반환한다. 없으면 None."""
    sessions = list_sessions()
    active = sorted(
        [s for s in sessions if s.status == STATUS_ACTIVE],
        key=lambda x: x.updated_at,
        reverse=True,
    )
    return active[0].session_id if active else None


def _scope_payload(scope: Any) -> dict[str, Any]:
    """ScopeState를 MCP 응답 dict로 직렬화한다."""
    return {
        "summary": scope.summary,
        "topics": scope.topics,
        "expanded_topics": scope.expanded_topics,
        "keywords": scope.keywords,
    }


# ── MCP Tools ────────────────────────────────────────────────────────────────


@mcp.tool()
def omk_get_session_status(session_id: str = "") -> dict[str, Any]:
    """현재 세션 상태를 반환한다.

    Claude가 언제든 세션 목표, Work Item 연결 상태, 통계를 조회할 수 있다.

    Args:
        session_id: 조회할 세션 ID. 빈 문자열이면 최근 활성 세션을 자동 선택.

    Returns:
        세션 상태 dict. 세션이 없으면 error 키를 포함한 dict.
    """
    target_id = session_id.strip() or _find_active_session_id()
    if not target_id:
        return {"error": "활성 세션이 없습니다. omk hooks install 후 Claude Code를 재시작하세요."}

    state = load_session(target_id)
    if state is None:
        return {"error": f"세션을 찾을 수 없습니다: {target_id!r}"}

    # 핵심 정보만 요약해서 반환 (전체 dict는 너무 방대할 수 있음)
    scope = state.scope
    stats = state.stats
    plane = state.plane_context

    return {
        "session_id": state.session_id,
        "status": state.status,
        "opted_out": state.opted_out,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "scope": {
            "summary": scope.summary,
            "topics": scope.topics,
            "expanded_topics": scope.expanded_topics,
            "keywords": scope.keywords,
            "file_refs": scope.file_refs,
        },
        "plane_context": {
            "project_id": plane.project_id,
            "work_item_ids": plane.work_item_ids,
            "module_id": plane.module_id,
        },
        "stats": {
            "total_prompts": stats.total_prompts,
            "drift_warnings": stats.drift_warnings,
            "scope_expansions": stats.scope_expansions,
            "files_touched": stats.files_touched,
        },
        "config": {
            "sensitivity": state.config.sensitivity,
            "cooldown": state.config.cooldown,
            "auto_expand": state.config.auto_expand,
        },
    }


@mcp.tool()
def omk_link_work_item(work_item_id: str, session_id: str = "") -> dict[str, Any]:
    """현재 세션에 Plane Work Item ID를 연결한다.

    Claude가 Plane Work Item을 생성한 직후 세션에 연결할 때 사용한다.
    연결된 Work Item에는 세션 종료 시 자동으로 댓글이 추가된다.

    Args:
        work_item_id: 연결할 Plane Work Item UUID.
        session_id: 대상 세션 ID. 빈 문자열이면 최근 활성 세션을 자동 선택.

    Returns:
        성공 여부와 현재 연결된 work_item_ids 목록.
    """
    # 입력 검증: work_item_id가 비어있거나 UUID 형식이 아니면 거부
    if not work_item_id or not work_item_id.strip():
        return {"error": "work_item_id가 비어있습니다."}

    wi_id = work_item_id.strip()
    if not _UUID_RE.match(wi_id):
        return {"error": f"유효하지 않은 UUID 형식입니다: {wi_id!r}"}

    target_id = session_id.strip() or _find_active_session_id()
    if not target_id:
        return {"error": "활성 세션이 없습니다."}

    state = load_session(target_id)
    if state is None:
        return {"error": f"세션을 찾을 수 없습니다: {target_id!r}"}

    # 중복 추가 방지
    if wi_id in state.plane_context.work_item_ids:
        return {
            "success": True,
            "message": f"이미 연결된 Work Item입니다: {wi_id}",
            "work_item_ids": state.plane_context.work_item_ids,
        }

    state.plane_context.work_item_ids = [*state.plane_context.work_item_ids, wi_id]
    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="prompt",
            summary=f"Work Item 연결: {wi_id}",
        )
    )
    save_session(state)

    return {
        "success": True,
        "message": f"Work Item 연결 완료: {wi_id}",
        "work_item_ids": state.plane_context.work_item_ids,
    }


@mcp.tool()
def omk_update_scope(
    summary: str = "",
    topics: list[str] | None = None,
    expanded_topics: list[str] | None = None,
    keywords: list[str] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """세션 범위(scope)를 수동으로 업데이트한다.

    Claude가 명시적으로 작업 목표나 범위를 변경할 때 사용한다.
    Phase 2 drift 감지에서 범위 확장을 사용자가 승인했을 때 호출하면 된다.

    Args:
        summary: 세션 목표 요약. 빈 문자열이면 기존 값 유지.
        topics: 핵심 토픽 목록. None이면 기존 값 유지.
        expanded_topics: 확장 토픽 목록. None이면 기존 값 유지.
        keywords: 키워드 목록. None이면 기존 값 유지.
        session_id: 대상 세션 ID. 빈 문자열이면 최근 활성 세션 자동 선택.

    Returns:
        성공 여부와 업데이트된 scope 정보.
    """
    target_id = session_id.strip() or _find_active_session_id()
    if not target_id:
        return {"error": "활성 세션이 없습니다."}

    state = load_session(target_id)
    if state is None:
        return {"error": f"세션을 찾을 수 없습니다: {target_id!r}"}

    # 제공된 값만 업데이트 (None이면 기존 값 보존)
    changed: list[str] = []

    if summary.strip():
        state.scope.summary = summary.strip()
        changed.append("summary")

    if topics is not None:
        state.scope.topics = [t for t in topics if t.strip()]
        changed.append("topics")

    if expanded_topics is not None:
        state.scope.expanded_topics = [t for t in expanded_topics if t.strip()]
        state.stats.scope_expansions += 1
        changed.append("expanded_topics")

    if keywords is not None:
        state.scope.keywords = [k for k in keywords if k.strip()]
        changed.append("keywords")

    if not changed:
        return {
            "success": True,
            "message": "변경할 내용이 없습니다.",
            "scope": _scope_payload(state.scope),
        }

    state.timeline.append(
        TimelineEvent(
            timestamp=now_iso(),
            type="scope_expanded",
            summary=f"범위 수동 업데이트: {', '.join(changed)}",
        )
    )
    save_session(state)

    return {
        "success": True,
        "message": f"scope 업데이트 완료: {', '.join(changed)}",
        "scope": _scope_payload(state.scope),
    }


@mcp.tool()
def omk_get_timeline(session_id: str = "", limit: int = 20) -> dict[str, Any]:
    """세션 타임라인 이벤트 목록을 반환한다.

    세션 중 발생한 이벤트(시작, drift 감지, 범위 확장, compact 복원 등)를 조회한다.

    Args:
        session_id: 조회할 세션 ID. 빈 문자열이면 최근 활성 세션 자동 선택.
        limit: 반환할 최대 이벤트 수. 1~100 범위로 제한. 기본값 20.

    Returns:
        타임라인 이벤트 목록.
    """
    # 범위 제한: limit은 1~100 사이
    safe_limit = max(1, min(limit, 100))

    target_id = session_id.strip() or _find_active_session_id()
    if not target_id:
        return {"error": "활성 세션이 없습니다."}

    state = load_session(target_id)
    if state is None:
        return {"error": f"세션을 찾을 수 없습니다: {target_id!r}"}

    # 최신 이벤트부터 반환 (역순으로 slice 후 다시 정순 정렬)
    events = state.timeline[-safe_limit:]

    return {
        "session_id": state.session_id,
        "total_events": len(state.timeline),
        "returned": len(events),
        "timeline": [
            {
                "timestamp": e.timestamp,
                "type": e.type,
                "summary": e.summary,
                "drift_score": e.drift_score,
            }
            for e in events
        ],
    }


@mcp.tool()
def omk_add_comment(
    comment: str,
    work_item_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """세션에 연결된 Plane Work Item에 댓글을 즉시 추가한다.

    Claude가 중요한 결정이나 발견을 Work Item에 즉시 기록할 때 사용한다.
    work_item_id를 지정하면 해당 항목에만, 지정하지 않으면 세션의 모든 Work Item에 추가한다.

    Args:
        comment: 추가할 댓글 내용 (마크다운 가능).
        work_item_id: 대상 Work Item UUID. 빈 문자열이면 세션의 모든 WI에 추가.
        session_id: 대상 세션 ID. 빈 문자열이면 최근 활성 세션 자동 선택.

    Returns:
        성공/실패 결과.
    """
    # 입력 검증: 댓글 내용이 비어있으면 거부
    if not comment or not comment.strip():
        return {"error": "댓글 내용이 비어있습니다."}

    target_id = session_id.strip() or _find_active_session_id()
    if not target_id:
        return {"error": "활성 세션이 없습니다."}

    state = load_session(target_id)
    if state is None:
        return {"error": f"세션을 찾을 수 없습니다: {target_id!r}"}

    # 대상 Work Item 목록 결정
    plane = state.plane_context
    project_id = plane.project_id

    if work_item_id.strip():
        wi_stripped = work_item_id.strip()
        if not _UUID_RE.match(wi_stripped):
            return {"error": f"유효하지 않은 UUID 형식입니다: {wi_stripped!r}"}
        target_wi_ids = [wi_stripped]
    else:
        target_wi_ids = plane.work_item_ids

    if not target_wi_ids:
        return {
            "error": "세션에 연결된 Work Item이 없습니다. omk_link_work_item으로 먼저 연결하세요."
        }

    if not project_id:
        return {"error": "세션에 project_id가 설정되지 않았습니다. omk config set으로 설정하세요."}

    # Plane API 호출
    try:
        import httpx
    except ImportError:
        return {"error": "httpx 패키지가 없습니다."}

    cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return {"error": "Plane API 키 또는 워크스페이스 슬러그가 설정되지 않았습니다."}

    base_url = cfg.base_url.rstrip("/")
    headers = {
        "X-API-Key": cfg.api_key,
        "Content-Type": "application/json",
    }

    # 민감 정보 제거 후 게시
    sanitized_comment = sanitize_comment(comment.strip())

    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
        for wi_id in target_wi_ids:
            url = (
                f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
                f"/projects/{project_id}/issues/{wi_id}/comments/"
            )
            try:
                resp = client.post(
                    url, headers=headers, json={"comment_html": sanitized_comment}
                )
                if resp.status_code in (200, 201):
                    results.append({"work_item_id": wi_id, "success": True})
                else:
                    results.append({
                        "work_item_id": wi_id,
                        "success": False,
                        "error": f"HTTP {resp.status_code}",
                    })
            except httpx.TimeoutException:
                results.append({
                    "work_item_id": wi_id,
                    "success": False,
                    "error": f"요청 시간 초과 ({PLANE_API_TIMEOUT}초)",
                })
            except httpx.NetworkError as e:
                results.append({
                    "work_item_id": wi_id,
                    "success": False,
                    "error": f"네트워크 오류: {e}",
                })
            except httpx.HTTPError as e:
                results.append({
                    "work_item_id": wi_id,
                    "success": False,
                    "error": f"HTTP 클라이언트 오류: {type(e).__name__}: {e}",
                })

    success_count = sum(1 for r in results if r.get("success"))
    return {
        "success": success_count > 0,
        "message": f"{success_count}/{len(results)}개 Work Item에 댓글 추가 완료",
        "results": results,
    }


# ── 진입점 ────────────────────────────────────────────────────────────────────

def main() -> None:
    """MCP 서버를 stdio 모드로 실행한다."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
