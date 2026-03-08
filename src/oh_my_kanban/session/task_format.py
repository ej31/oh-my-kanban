"""태스크 형식 결정 모듈: task_mode 설정에 따라 WI 생성 방식을 결정한다."""

from __future__ import annotations

# ── 태스크 모드 상수 ──────────────────────────────────────────────────────────
TASK_MODE_MAIN_SUB = "main-sub"
TASK_MODE_FLAT = "flat"
TASK_MODE_MODULE_TASK_SUB = "module-task-sub"
_VALID_TASK_MODES = {TASK_MODE_MAIN_SUB, TASK_MODE_FLAT, TASK_MODE_MODULE_TASK_SUB}


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


def build_task_title(summary: str, mode: str, is_subtask: bool = False) -> str:
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


def build_task_description(summary: str, topics: list[str], mode: str) -> str:
    """task_mode에 따라 태스크 설명을 생성한다.

    Args:
        summary: 태스크 요약 텍스트
        topics: 관련 토픽 목록
        mode: task_mode 설정값

    Returns:
        태스크 설명 문자열
    """
    normalized = normalize_task_mode(mode)
    lines: list[str] = []

    if normalized == TASK_MODE_FLAT:
        lines.append(f"**요약**: {summary}")
    elif normalized == TASK_MODE_MODULE_TASK_SUB:
        lines.append(f"**모듈 태스크**: {summary}")
    else:
        lines.append(f"**목표**: {summary}")

    if topics:
        lines.append("")
        lines.append(f"**토픽**: {', '.join(topics)}")

    return "\n".join(lines)
