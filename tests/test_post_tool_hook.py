"""PostToolUse 훅 테스트."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.session.state import SessionState


def _make_state(session_id: str = "test-session", opted_out: bool = False) -> SessionState:
    """테스트용 기본 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.opted_out = opted_out
    return state


def _run_hook(stdin_payload: dict) -> None:
    """훅 main()을 stdin을 주입해 실행한다."""
    from oh_my_kanban.hooks.post_tool import main

    with patch("sys.stdin", StringIO(json.dumps(stdin_payload))):
        try:
            main()
        except SystemExit:
            pass


class TestPostToolHookEdit:
    """Edit 도구 → files_touched 업데이트."""

    def test_edit_tool_updates_files_touched(self, tmp_path):
        state = _make_state()
        payload = {
            "session_id": "test-session",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/src/main.py"},
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        mock_save.assert_called_once()
        assert "/project/src/main.py" in state.stats.files_touched or \
               "project/src/main.py" in state.stats.files_touched[0]


class TestPostToolHookWrite:
    """Write 도구 → files_touched 업데이트."""

    def test_write_tool_updates_files_touched(self, tmp_path):
        state = _make_state()
        payload = {
            "session_id": "test-session",
            "tool_name": "Write",
            "tool_input": {"file_path": "/project/new_file.py"},
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        mock_save.assert_called_once()
        assert len(state.stats.files_touched) == 1
        assert "new_file.py" in state.stats.files_touched[0]


class TestPostToolHookMultiEdit:
    """MultiEdit → 여러 파일 업데이트."""

    def test_multiedit_updates_multiple_files(self):
        state = _make_state()
        payload = {
            "session_id": "test-session",
            "tool_name": "MultiEdit",
            "tool_input": {
                "edits": [
                    {"file_path": "/project/a.py", "old_string": "x", "new_string": "y"},
                    {"file_path": "/project/b.py", "old_string": "p", "new_string": "q"},
                ]
            },
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        mock_save.assert_called_once()
        assert len(state.stats.files_touched) == 2


class TestPostToolHookOptedOut:
    """opted_out 세션 → 아무 변경 없이 exit 0."""

    def test_opted_out_session_skips_update(self):
        state = _make_state(opted_out=True)
        payload = {
            "session_id": "test-session",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/main.py"},
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        mock_save.assert_not_called()
        assert len(state.stats.files_touched) == 0


class TestPostToolHookInvalidToolInput:
    """잘못된 페이로드 (tool_input이 None) → 예외 없이 처리."""

    def test_none_tool_input_handled_gracefully(self):
        state = _make_state()
        payload = {
            "session_id": "test-session",
            "tool_name": "Edit",
            "tool_input": None,
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        # tool_input이 None이면 빈 dict로 처리 → file_paths 없음 → save는 호출됨(빈 업데이트)
        mock_save.assert_called_once()
        assert len(state.stats.files_touched) == 0


class TestPostToolHookNoSessionId:
    """session_id 없음 → exit 0 (fail-open)."""

    def test_missing_session_id_exits_cleanly(self):
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/main.py"},
        }

        with patch("oh_my_kanban.hooks.post_tool.load_session") as mock_load:
            _run_hook(payload)

        mock_load.assert_not_called()


class TestPostToolHookSessionNotFound:
    """세션 파일 없음 → exit 0 (fail-open)."""

    def test_missing_session_file_exits_cleanly(self):
        payload = {
            "session_id": "nonexistent-session",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/main.py"},
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=None),
            patch("oh_my_kanban.hooks.post_tool.save_session") as mock_save,
        ):
            _run_hook(payload)

        mock_save.assert_not_called()


class TestPostToolHookException:
    """예외 발생 시 fail-open."""

    def test_exception_in_load_session_exits_cleanly(self, capsys):
        payload = {
            "session_id": "test-session",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/project/main.py"},
        }

        with patch(
            "oh_my_kanban.hooks.post_tool.load_session",
            side_effect=RuntimeError("DB 연결 오류"),
        ):
            _run_hook(payload)

        captured = capsys.readouterr()
        assert "fail-open" in captured.err
        assert "RuntimeError" in captured.err

    def test_exception_in_save_session_exits_cleanly(self, capsys):
        state = _make_state()
        payload = {
            "session_id": "test-session",
            "tool_name": "Write",
            "tool_input": {"file_path": "/project/main.py"},
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch(
                "oh_my_kanban.hooks.post_tool.save_session",
                side_effect=OSError("디스크 오류"),
            ),
        ):
            _run_hook(payload)

        captured = capsys.readouterr()
        assert "fail-open" in captured.err
