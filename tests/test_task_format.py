"""US-005: Task format system 테스트.

task_mode 설정에 따른 태스크 형식 결정 로직을 검증한다.
"""

from __future__ import annotations

import pytest

from oh_my_kanban.session.task_format import (
    TASK_MODE_FLAT,
    TASK_MODE_MAIN_SUB,
    TASK_MODE_MODULE_TASK_SUB,
    _VALID_TASK_MODES,
    build_task_description,
    build_task_title,
    normalize_task_mode,
    should_create_subtask,
)


# ── normalize_task_mode ───────────────────────────────────────────────────────


class TestNormalizeTaskMode:
    """normalize_task_mode 함수 테스트."""

    def test_valid_main_sub(self) -> None:
        assert normalize_task_mode("main-sub") == "main-sub"

    def test_valid_flat(self) -> None:
        assert normalize_task_mode("flat") == "flat"

    def test_valid_module_task_sub(self) -> None:
        assert normalize_task_mode("module-task-sub") == "module-task-sub"

    def test_invalid_value_fallback(self) -> None:
        """유효하지 않은 값은 main-sub로 fallback되어야 한다."""
        assert normalize_task_mode("invalid") == TASK_MODE_MAIN_SUB

    def test_empty_string_fallback(self) -> None:
        """빈 문자열은 main-sub로 fallback되어야 한다."""
        assert normalize_task_mode("") == TASK_MODE_MAIN_SUB


# ── should_create_subtask ─────────────────────────────────────────────────────


class TestShouldCreateSubtask:
    """should_create_subtask 함수 테스트."""

    def test_main_sub_returns_true(self) -> None:
        assert should_create_subtask("main-sub") is True

    def test_module_task_sub_returns_true(self) -> None:
        assert should_create_subtask("module-task-sub") is True

    def test_flat_returns_false(self) -> None:
        assert should_create_subtask("flat") is False

    def test_invalid_mode_returns_true(self) -> None:
        """유효하지 않은 모드는 main-sub fallback이므로 True."""
        assert should_create_subtask("unknown") is True


# ── build_task_title ──────────────────────────────────────────────────────────


class TestBuildTaskTitle:
    """build_task_title 함수 테스트."""

    def test_flat_mode_returns_plain_summary(self) -> None:
        assert build_task_title("로그인 구현", "flat") == "로그인 구현"

    def test_flat_mode_subtask_same_as_main(self) -> None:
        """flat 모드에서는 is_subtask 여부와 관계없이 동일한 제목."""
        assert build_task_title("로그인 구현", "flat", is_subtask=True) == "로그인 구현"

    def test_main_sub_main_task(self) -> None:
        assert build_task_title("로그인 구현", "main-sub") == "로그인 구현"

    def test_main_sub_subtask(self) -> None:
        assert build_task_title("로그인 구현", "main-sub", is_subtask=True) == "[하위] 로그인 구현"

    def test_module_task_sub_main(self) -> None:
        assert build_task_title("인증 모듈", "module-task-sub") == "[모듈] 인증 모듈"

    def test_module_task_sub_subtask(self) -> None:
        assert build_task_title("인증 모듈", "module-task-sub", is_subtask=True) == "[하위] 인증 모듈"

    def test_empty_summary_uses_default(self) -> None:
        """빈 summary는 '무제'로 대체되어야 한다."""
        assert build_task_title("", "flat") == "무제"


# ── build_task_description ────────────────────────────────────────────────────


class TestBuildTaskDescription:
    """build_task_description 함수 테스트."""

    def test_flat_mode_description(self) -> None:
        desc = build_task_description("구현", ["auth"], "flat")
        assert "**요약**" in desc
        assert "auth" in desc

    def test_main_sub_description(self) -> None:
        desc = build_task_description("구현", ["auth", "api"], "main-sub")
        assert "**목표**" in desc
        assert "auth" in desc

    def test_module_task_sub_description(self) -> None:
        desc = build_task_description("구현", [], "module-task-sub")
        assert "**모듈 태스크**" in desc

    def test_empty_topics(self) -> None:
        """토픽이 없으면 토픽 섹션이 생략되어야 한다."""
        desc = build_task_description("구현", [], "flat")
        assert "토픽" not in desc
