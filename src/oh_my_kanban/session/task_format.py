"""태스크 형식 결정 및 apply 엔진 모듈.

task_mode 설정에 따라 WI 생성 방식을 결정하고 자동 생성을 수행한다.
"""

from __future__ import annotations

import re as _re
import sys
from typing import TYPE_CHECKING, Any, Literal

_UNSAFE_TITLE_RE = _re.compile(r'[\x00-\x1f\x7f<>&"]')

from oh_my_kanban.session.manager import save_session
from oh_my_kanban.session.state import TimelineEvent, now_iso

if TYPE_CHECKING:
    from oh_my_kanban.config import Config
    from oh_my_kanban.provider import ProviderClient
    from oh_my_kanban.session.state import SessionState

# ── 태스크 모드 상수 ──────────────────────────────────────────────────────────
TASK_MODE_MAIN_SUB = "main-sub"
TASK_MODE_FLAT = "flat"
TASK_MODE_MODULE_TASK_SUB = "module-task-sub"
TASK_MODE_NONE = "none"
_VALID_TASK_MODES = {TASK_MODE_MAIN_SUB, TASK_MODE_FLAT, TASK_MODE_MODULE_TASK_SUB, TASK_MODE_NONE}

# apply 엔진에서 사용하는 frozenset (none 포함, module-task-sub 포함)
VALID_TASK_MODES = frozenset({"main-sub", "flat", "none", "module-task-sub"})


def normalize_task_mode(mode: str) -> str:
    """유효하지 않은 task_mode를 TASK_MODE_MAIN_SUB로 fallback한다."""
    if mode in _VALID_TASK_MODES:
        return mode
    return TASK_MODE_MAIN_SUB


def should_create_subtask(task_mode: str) -> bool:
    """주어진 task_mode에서 하위 태스크를 생성해야 하는지 판단한다.

    main-sub, module-task-sub: True (하위 태스크 생성)
    flat: False (단일 태스크만)
    """
    normalized = normalize_task_mode(task_mode)
    return normalized != TASK_MODE_FLAT


def build_task_title(summary: str, mode: str, *, is_subtask: bool = False) -> str:
    """task_mode에 따라 적절한 태스크 제목을 생성한다.

    Args:
        summary: 태스크 요약 텍스트
        mode: task_mode 설정값
        is_subtask: 하위 태스크 여부

    Returns:
        모드에 맞게 포맷팅된 태스크 제목
    """
    normalized = normalize_task_mode(mode)
    if not summary:
        summary = "무제"

    if normalized == TASK_MODE_FLAT:
        return summary

    if normalized == TASK_MODE_MODULE_TASK_SUB:
        if is_subtask:
            return f"[하위] {summary}"
        return f"[모듈] {summary}"

    # main-sub (기본값)
    if is_subtask:
        return f"[하위] {summary}"
    return summary


def build_task_description(summary: str, topics: list[str], mode: str, *, is_subtask: bool = False) -> str:
    """task_mode에 따라 태스크 설명을 생성한다.

    Args:
        summary: 태스크 요약 텍스트
        topics: 관련 토픽 목록
        mode: task_mode 설정값
        is_subtask: 하위 태스크 여부

    Returns:
        태스크 설명 문자열
    """
    normalized = normalize_task_mode(mode)
    lines: list[str] = []

    if normalized == TASK_MODE_FLAT:
        lines.append(f"**요약**: {summary}")
    elif normalized == TASK_MODE_MODULE_TASK_SUB:
        if is_subtask:
            lines.append(f"**하위 태스크**: {summary}")
        else:
            lines.append(f"**모듈 태스크**: {summary}")
    else:
        lines.append(f"**목표**: {summary}")

    if topics:
        lines.append("")
        lines.append(f"**토픽**: {', '.join(topics)}")

    return "\n".join(lines)


# ── apply 엔진 ────────────────────────────────────────────────────────────────


def _sanitize_wi_title(text: str, max_len: int = 60, *, default: str = "") -> str:
    """WI 제목에 사용하기 안전한 문자열로 정제한다. 결과가 비어있으면 default를 반환한다."""
    sanitized = _UNSAFE_TITLE_RE.sub(" ", text).strip()
    result = sanitized[:max_len].strip()
    return result if result else default


TaskFormatTrigger = Literal["session_start", "drift_detected"]


def _extract_wi_id(result: dict) -> str:
    """create_work_item 반환 dict에서 WI ID를 추출한다.

    1차: result["id"]
    2차: result["raw"]["id"]
    둘 다 없으면 빈 문자열 반환.
    """
    wi_id = result.get("id", "")
    if wi_id:
        return str(wi_id)
    raw = result.get("raw", {})
    if isinstance(raw, dict):
        wi_id = raw.get("id", "")
        if wi_id:
            return str(wi_id)
    return ""


def apply_task_format(
    state: "SessionState",
    cfg: "Config",
    provider_client: "ProviderClient",
    trigger: TaskFormatTrigger,
    prompt_text: str = "",
) -> None:
    """task_mode에 따라 WI를 자동 생성하고 세션 상태를 갱신한다.

    Args:
        state: 현재 세션 상태 (직접 변경됨).
        cfg: 로드된 설정 객체.
        provider_client: provider 작업을 위한 클라이언트.
        trigger: "session_start" 또는 "drift_detected".
        prompt_text: drift_detected 트리거 시 서브태스크 제목에 사용할 프롬프트.

    Raises:
        ValueError: task_mode가 VALID_TASK_MODES에 없을 때.
        Exception: provider_client.create_work_item 호출 실패 시 (re-raise).
    """
    # 1. task_mode 검증
    task_mode = cfg.task_mode
    if task_mode not in VALID_TASK_MODES:
        raise ValueError(
            f"유효하지 않은 task_mode: {task_mode!r}. "
            f"허용값: {sorted(VALID_TASK_MODES)}"
        )

    # 2. none 모드: 아무 것도 하지 않음
    if task_mode == "none":
        return

    # 3. provider별 대상 식별자 확인
    project_id = ""
    if provider_client.name == "plane":
        project_id = cfg.project_id or state.plane_context.project_id
        if not project_id:
            print(
                "[omk] task_format: project_id가 설정되지 않아 WI 자동 생성을 건너뜁니다.",
                file=sys.stderr,
            )
            return
    else:
        # Linear 등 다른 provider는 provider 자체에서 target 검증
        project_id = cfg.project_id or state.plane_context.project_id
        if not project_id:
            print(
                "[omk] task_format: project_id가 설정되지 않아 WI 자동 생성을 건너뜁니다.",
                file=sys.stderr,
            )
            return

    # 4. trigger별 처리
    if trigger == "session_start":
        _handle_session_start(state, cfg, provider_client, project_id)
    elif trigger == "drift_detected":
        _handle_drift_detected(state, cfg, provider_client, task_mode, prompt_text, project_id)


def _handle_session_start(
    state: "SessionState",
    cfg: "Config",
    provider_client: "ProviderClient",
    project_id: str,
) -> None:
    """session_start 트리거: 세션 메인 WI를 1회 자동 생성한다."""
    # 중복 방지: 이미 auto_created_task_id가 있으면 리턴
    if state.plane_context.auto_created_task_id:
        return

    # WI 제목 결정: scope.summary 또는 기본 제목
    title = _sanitize_wi_title(
        state.scope.summary or "",
        max_len=120,
        default=f"[omk] 새 세션 {state.session_id[:8]}",
    )

    # provider_context 구성 (ProviderContext로 변환)
    from oh_my_kanban.provider import ProviderContext
    provider_ctx = ProviderContext(
        provider_name=provider_client.name,
        project_id=project_id,
        work_item_ids=list(state.plane_context.work_item_ids),
        module_id=state.plane_context.module_id,
        focused_work_item_id=state.plane_context.focused_work_item_id,
        auto_created_task_id=state.plane_context.auto_created_task_id,
    )

    # WI 생성 — 예외는 호출자에게 re-raise
    result = provider_client.create_work_item(provider_ctx, title)
    wi_id = _extract_wi_id(result)

    if not wi_id:
        print(
            "[omk] task_format: session_start WI 생성 응답에서 ID를 추출하지 못했습니다.",
            file=sys.stderr,
        )
        return

    # 세션 상태 갱신 (불변 패턴)
    state.plane_context.auto_created_task_id = wi_id
    state.plane_context.work_item_ids = [*state.plane_context.work_item_ids, wi_id]
    state.plane_context.focused_work_item_id = wi_id

    state.timeline = [
        *state.timeline,
        TimelineEvent(
            timestamp=now_iso(),
            type="scope_init",
            summary=f"[omk] 세션 메인 WI 자동 생성: {wi_id} (제목: {title})",
        ),
    ]

    save_session(state)


def _handle_drift_detected(
    state: "SessionState",
    cfg: "Config",
    provider_client: "ProviderClient",
    task_mode: str,
    prompt_text: str,
    project_id: str,
) -> None:
    """drift_detected 트리거: main-sub/module-task-sub 모드에서 서브태스크 WI를 생성한다."""
    # flat 또는 none 모드는 서브태스크를 생성하지 않음
    # module-task-sub는 main-sub와 동일하게 서브태스크 생성
    if task_mode in ("flat", "none"):
        return

    # auto_created_task_id가 없으면 메인 WI가 없는 것이므로 리턴
    if not state.plane_context.auto_created_task_id:
        return

    # 서브태스크 제목 결정
    timestamp = now_iso()
    title = _sanitize_wi_title(
        prompt_text if prompt_text and prompt_text.strip() else "",
        default=f"[omk] 드리프트 작업 {timestamp}",
    )

    # provider_context 구성
    from oh_my_kanban.provider import ProviderContext
    provider_ctx = ProviderContext(
        provider_name=provider_client.name,
        project_id=project_id,
        work_item_ids=list(state.plane_context.work_item_ids),
        module_id=state.plane_context.module_id,
        focused_work_item_id=state.plane_context.focused_work_item_id,
        auto_created_task_id=state.plane_context.auto_created_task_id,
    )

    # WI 생성 — 예외는 호출자에게 re-raise
    result = provider_client.create_work_item(provider_ctx, title)
    wi_id = _extract_wi_id(result)

    if not wi_id:
        print(
            "[omk] task_format: drift_detected 서브태스크 생성 응답에서 ID를 추출하지 못했습니다.",
            file=sys.stderr,
        )
        return

    # 세션 상태 갱신 (auto_created_task_id는 불변)
    state.plane_context.work_item_ids = [*state.plane_context.work_item_ids, wi_id]
    state.plane_context.focused_work_item_id = wi_id

    state.timeline = [
        *state.timeline,
        TimelineEvent(
            timestamp=now_iso(),
            type="drift_detected",
            summary=f"[omk] 드리프트 서브태스크 WI 자동 생성: {wi_id} (제목: {title})",
        ),
    ]

    save_session(state)
