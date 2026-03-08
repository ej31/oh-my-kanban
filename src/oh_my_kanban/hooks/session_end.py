"""SessionEnd 훅: 세션 요약 생성 + Plane Work Item 댓글 단일 API 호출.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
timeout: 30초 (settings.json에 명시)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import html
import sys

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import (
    exit_fail_open,
    get_session_id,
    read_hook_input,
    record_health_warning,
    sanitize_comment,
    validate_plane_url_params,
)
from oh_my_kanban.hooks.http_client import build_plane_headers, plane_http_client, plane_request
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.state import (
    FILES_DISPLAY_MAX,
    SESSION_ID_DISPLAY_LEN,
    STATUS_COMPLETED,
    STATUS_OPTED_OUT,
    SUMMARY_DISPLAY_MAX,
    TIMELINE_DISPLAY_MAX,
    SessionState,
    TimelineEvent,
    now_iso,
)

# ── 업로드 레벨 상수 ──────────────────────────────────────────────────────────
UPLOAD_LEVEL_NONE = "none"

UPLOAD_LEVEL_METADATA = "metadata"
UPLOAD_LEVEL_FULL = "full"
_VALID_UPLOAD_LEVELS = {UPLOAD_LEVEL_NONE, UPLOAD_LEVEL_METADATA, UPLOAD_LEVEL_FULL}


def _build_summary_comment(state: SessionState) -> str:
    """세션 종료 시 Plane Work Item에 달 댓글 내용을 생성한다."""
    scope = state.scope
    stats = state.stats

    lines = [
        "## omk 세션 종료",
        "",
        f"**목표**: {html.escape(scope.summary[:SUMMARY_DISPLAY_MAX]) if scope.summary else '미설정'}",
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
            lines.append(f"- `{html.escape(f)}`")
        if len(stats.files_touched) > FILES_DISPLAY_MAX:
            lines.append(f"- ...외 {len(stats.files_touched) - FILES_DISPLAY_MAX}개")

    if scope.topics:
        lines.append("")
        lines.append(f"**주요 토픽**: {', '.join(html.escape(t) for t in scope.topics)}")

    lines.append("")
    lines.append(f"*세션 ID: {state.session_id[:SESSION_ID_DISPLAY_LEN]}...*")
    return "\n".join(lines)


def _build_full_comment(state: SessionState) -> str:
    """타임라인 이벤트를 포함한 상세 댓글을 생성한다 (full 모드용)."""
    # 메타데이터 요약 섹션 포함
    lines = _build_summary_comment(state).splitlines()

    # 타임라인 이벤트 섹션 추가 (HTML 특수문자 이스케이프로 XSS 방지)
    if state.timeline:
        lines.append("")
        lines.append("**타임라인**")
        for event in state.timeline[:TIMELINE_DISPLAY_MAX]:
            ts_short = event.timestamp[:19] if len(event.timestamp) >= 19 else event.timestamp
            safe_summary = html.escape(event.summary)
            lines.append(f"- `{ts_short}` [{html.escape(event.type)}] {safe_summary}")
        if len(state.timeline) > TIMELINE_DISPLAY_MAX:
            lines.append(f"- ...외 {len(state.timeline) - TIMELINE_DISPLAY_MAX}개 이벤트")

    return "\n".join(lines)


def _post_plane_comment(state: SessionState, comment: str, cfg=None) -> bool:
    """Plane Work Item에 댓글을 추가한다. 성공 여부를 반환한다."""
    try:
        import httpx
    except ImportError:
        return False

    if cfg is None:
        cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return False

    wi_ids = state.plane_context.work_item_ids
    project_id = state.plane_context.project_id or cfg.project_id

    if not wi_ids or not project_id:
        return False

    # URL 경로 삽입 전 형식 검증 (경로 트래버설 / 인젝션 방지)
    workspace_slug = cfg.workspace_slug
    if not workspace_slug or not validate_plane_url_params(workspace_slug, project_id):
        print("[omk] 유효하지 않은 workspace_slug 또는 project_id — Plane 댓글 건너뜀", file=sys.stderr)
        return False

    base_url = cfg.base_url.rstrip("/")

    success_count = 0
    failure_count = 0
    try:
        with plane_http_client(cfg.api_key) as client:
            for wi_id in wi_ids:
                # wi_id UUID 형식 검증 (URL 경로 인젝션 방지)
                if not validate_plane_url_params(workspace_slug, project_id, wi_id):
                    print(f"[omk] 유효하지 않은 work_item_id 건너뜀: {wi_id!r}", file=sys.stderr)
                    failure_count += 1
                    continue
                url = (
                    f"{base_url}/api/v1/workspaces/{workspace_slug}"
                    f"/projects/{project_id}/issues/{wi_id}/comments/"
                )
                try:
                    resp = plane_request(
                        client, "POST", url,
                        json={"comment_html": sanitize_comment(comment)},
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

        # upload_level에 따라 댓글 업로드 방식 결정
        cfg = load_config()
        upload_level = cfg.upload_level
        if upload_level not in _VALID_UPLOAD_LEVELS:
            print(
                f"[omk] 알 수 없는 upload_level '{upload_level}', none으로 대체합니다 (안전 기본값).",
                file=sys.stderr,
            )
            upload_level = UPLOAD_LEVEL_NONE

        # Plane Work Item 댓글 추가 (none이 아닌 경우에만)
        if upload_level != UPLOAD_LEVEL_NONE and state.plane_context.work_item_ids:
            if upload_level == UPLOAD_LEVEL_FULL:
                comment = _build_full_comment(state)
            else:
                comment = _build_summary_comment(state)
            _post_plane_comment(state, comment, cfg)

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
