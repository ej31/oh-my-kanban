"""SessionStart 훅: 세션 초기화/복원 및 /compact 후 컨텍스트 재주입.

Claude Code가 이 스크립트를 독립 프로세스로 실행한다.
stdin: {"session_id": "...", "source": "startup|resume|compact", ...}
stdout: JSON (additionalContext 주입용)
exit code 0: 항상 (fail-open)
"""

from __future__ import annotations

import sys
from pathlib import Path

from oh_my_kanban.config import OMK_DIR_NAME, load_config
from oh_my_kanban.hooks.common import (
    exit_fail_open,
    get_session_id,
    output_context,
    read_hook_input,
    record_health_warning,
)
from oh_my_kanban.session.manager import create_session, load_session, save_session
from oh_my_kanban.session.plane_context_builder import build_plane_context
from oh_my_kanban.session.state import (
    FILES_COMPACT_MAX,
    SUMMARY_COMPACT_MAX,
    SUMMARY_RESUME_MAX,
    WORK_ITEMS_DISPLAY_MAX,
    WORK_ITEMS_RESUME_MAX,
    TimelineEvent,
    now_iso,
)

# .omk 디렉토리 내 마커 파일 상수
_DISABLED_FILE = "disabled"
_PROMPTED_FILE = ".prompted"
_PROJECT_TOML_FILE = "project.toml"


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
            plane_content, stale_ids = build_plane_context(
                work_item_ids=wi_ids,
                project_id=project_id,
                base_url=cfg.base_url,
                api_key=cfg.api_key,
                workspace_slug=cfg.workspace_slug,
            )
            # stale IDs를 항상 갱신 — 이전 실패가 복구되면 빈 리스트로 클리어
            state.plane_context.stale_work_item_ids = stale_ids
            if stale_ids:
                state.plane_context.stale_work_item_ids = stale_ids
                context_lines.append(
                    f"\n[경고] 다음 Work Item을 조회할 수 없습니다 (삭제/이동 가능): {', '.join(stale_ids)}"
                )
                record_health_warning({
                    "type": "stale_work_items",
                    "session_id": session_id,
                    "stale_ids": stale_ids,
                    "timestamp": now_iso(),
                })

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


def _is_project_disabled() -> bool:
    """cwd에서 .omk/disabled 마커가 존재하는지 확인한다 (프로젝트 단위 opt-out)."""
    disabled = Path.cwd() / OMK_DIR_NAME / _DISABLED_FILE
    return disabled.exists()


def _inject_project_guidance() -> None:
    """프로젝트에 .omk/project.toml이 없으면 1회성 안내를 주입한다.

    .omk/.prompted 마커가 이미 있으면 안내를 건너뛴다.
    안내 주입 후 .omk/.prompted 마커를 생성한다.
    """
    cwd = Path.cwd()
    omk_dir = cwd / OMK_DIR_NAME
    project_toml = omk_dir / _PROJECT_TOML_FILE
    prompted = omk_dir / _PROMPTED_FILE

    # .omk/project.toml이 있으면 안내 불필요
    if project_toml.exists():
        return

    # 이미 안내를 받았으면 건너뜀
    if prompted.exists():
        return

    # 1회성 안내 주입
    guidance = (
        "[omk] 이 프로젝트에 Plane/Linear가 연결되지 않았습니다.\n"
        "  omk project bind <project_id> 로 연결하거나,\n"
        "  이 안내를 무시하면 다시 표시되지 않습니다.\n"
        "  세션 추적은 활성화되지만 WI 연동은 비활성 상태입니다."
    )
    output_context("SessionStart", guidance)

    # .omk/.prompted 마커 생성 (다음 세션에서 안내하지 않도록)
    try:
        omk_dir.mkdir(parents=True, exist_ok=True)
        prompted.write_text(now_iso(), encoding="utf-8")
    except OSError:
        pass  # 마커 생성 실패해도 훅을 차단하지 않는다


def _handle_startup_or_resume(session_id: str, source: str) -> None:
    """세션 시작 또는 재개 처리: 파일 초기화/복원 후 Plane 설정 연결."""
    # 프로젝트 단위 opt-out 확인
    if _is_project_disabled():
        return

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

    save_session(state)

    # 신규 세션이고 project_id가 없으면 1회성 안내 주입
    if source == "startup" and not cfg.project_id:
        _inject_project_guidance()

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


if __name__ == "__main__":
    main()
