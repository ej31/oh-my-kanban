"""US-004: Productize task switching 테스트.

hooks switch-task 커맨드를 통한 태스크 전환 기능을 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from oh_my_kanban.cli import cli
from oh_my_kanban.session.state import (
    PlaneContext,
    ScopeState,
    SessionState,
    SessionStats,
    STATUS_ACTIVE,
)


def _make_active_state(
    session_id: str = "switch-test-001",
    work_item_ids: list[str] | None = None,
) -> SessionState:
    """태스크 전환 테스트용 활성 세션 생성."""
    state = SessionState(session_id=session_id, status=STATUS_ACTIVE)
    state.plane_context = PlaneContext(
        project_id="proj-1",
        work_item_ids=work_item_ids or ["wi-old-001", "wi-old-002"],
    )
    state.scope = ScopeState(summary="이전 작업")
    return state


class TestSwitchTask:
    """hooks switch-task 커맨드 테스트."""

    def test_switch_moves_work_items_to_stale(self) -> None:
        """전환 시 기존 work_item_ids가 stale로 이동해야 한다."""
        runner = CliRunner()
        state = _make_active_state()

        # switch-task 커맨드는 함수 내부에서 lazy import하므로
        # session.manager 모듈을 직접 패치한다
        saved_states: list[SessionState] = []

        def capture_save(s: SessionState) -> None:
            saved_states.append(s)

        with (
            patch("oh_my_kanban.session.manager.list_sessions", return_value=[state]),
            patch("oh_my_kanban.session.manager.load_session", return_value=state),
            patch("oh_my_kanban.session.manager.save_session", side_effect=capture_save),
        ):
            result = runner.invoke(cli, ["hooks", "switch-task", "--reason", "우선순위 변경"])

        assert result.exit_code == 0, result.output
        assert "태스크 전환 완료" in result.output

        assert len(saved_states) == 1
        saved = saved_states[0]
        assert saved.plane_context.work_item_ids == []
        assert "wi-old-001" in saved.plane_context.stale_work_item_ids
        assert "wi-old-002" in saved.plane_context.stale_work_item_ids

    def test_switch_adds_timeline_event(self) -> None:
        """전환 시 타임라인에 task_switch 이벤트가 추가되어야 한다."""
        runner = CliRunner()
        state = _make_active_state()
        initial_timeline_len = len(state.timeline)

        with (
            patch("oh_my_kanban.session.manager.list_sessions", return_value=[state]),
            patch("oh_my_kanban.session.manager.load_session", return_value=state),
            patch("oh_my_kanban.session.manager.save_session"),
        ):
            result = runner.invoke(cli, [
                "hooks", "switch-task",
                "--new", "새 기능 구현",
                "--reason", "요구사항 변경",
            ])

        assert result.exit_code == 0, result.output
        assert len(state.timeline) == initial_timeline_len + 1
        last_event = state.timeline[-1]
        assert last_event.type == "task_switch"
        assert "새 기능 구현" in last_event.summary
        assert "요구사항 변경" in last_event.summary

    def test_switch_no_active_session_fails(self) -> None:
        """활성 세션이 없으면 에러가 발생해야 한다."""
        runner = CliRunner()

        with patch("oh_my_kanban.session.manager.list_sessions", return_value=[]):
            result = runner.invoke(cli, ["hooks", "switch-task"])

        assert result.exit_code != 0
        assert "활성 세션이 없습니다" in result.output

    def test_switch_with_new_title_shows_info(self) -> None:
        """--new 옵션이 있으면 새 태스크 제목 정보가 출력되어야 한다."""
        runner = CliRunner()
        state = _make_active_state()

        with (
            patch("oh_my_kanban.session.manager.list_sessions", return_value=[state]),
            patch("oh_my_kanban.session.manager.load_session", return_value=state),
            patch("oh_my_kanban.session.manager.save_session"),
        ):
            result = runner.invoke(cli, [
                "hooks", "switch-task", "--new", "긴급 버그 수정",
            ])

        assert result.exit_code == 0, result.output
        assert "긴급 버그 수정" in result.output
