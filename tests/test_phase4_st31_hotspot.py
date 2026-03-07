"""ST-31: 파일 핫스팟 인사이트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.post_tool import (
    _HOTSPOT_SESSION_THRESHOLD,
    _check_file_hotspot,
    _get_file_session_counts,
)
from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.post_tool"


def _make_state(session_id: str = "sess-st31-001") -> SessionState:
    state = SessionState(session_id=session_id)
    return state


def _make_mock_session(session_id: str, files: list[str]) -> MagicMock:
    s = MagicMock()
    s.session_id = session_id
    s.stats.files_touched = files
    return s


_MANAGER_PATH = "oh_my_kanban.session.manager.list_sessions"


class TestGetFileSessionCounts:
    def test_excludes_current_session(self):
        """현재 세션은 집계에서 제외한다."""
        sessions = [
            _make_mock_session("current", ["auth.py"]),
            _make_mock_session("other-1", ["auth.py"]),
        ]

        with patch(_MANAGER_PATH, return_value=sessions):
            counts = _get_file_session_counts("current")

        assert counts.get("auth.py", 0) == 1  # other-1만 집계

    def test_counts_across_sessions(self):
        """여러 세션에서 수정된 파일의 수를 정확히 집계한다."""
        sessions = [
            _make_mock_session("s1", ["auth.py", "user.py"]),
            _make_mock_session("s2", ["auth.py"]),
            _make_mock_session("s3", ["auth.py"]),
        ]

        with patch(_MANAGER_PATH, return_value=sessions):
            counts = _get_file_session_counts("current-x")

        assert counts["auth.py"] == 3
        assert counts["user.py"] == 1

    def test_returns_empty_on_error(self):
        """예외 발생 시 빈 dict를 반환한다 (fail-open)."""
        with patch(_MANAGER_PATH, side_effect=Exception("오류")):
            counts = _get_file_session_counts("any")

        # 예외가 전파되지 않아야 함
        assert isinstance(counts, dict)


class TestCheckFileHotspot:
    def test_no_alert_when_file_paths_empty(self):
        """파일 경로가 없으면 알림 없음."""
        state = _make_state()

        with patch(f"{_MOD}.output_system_message") as mock_msg:
            _check_file_hotspot(state, [])

        mock_msg.assert_not_called()

    def test_no_alert_below_threshold(self):
        """임계값 미만 세션에서 수정된 파일은 알림 없음."""
        state = _make_state()
        sessions = [
            _make_mock_session(f"s{i}", ["auth.py"])
            for i in range(_HOTSPOT_SESSION_THRESHOLD - 1)  # threshold - 1개
        ]

        with (
            patch(_MANAGER_PATH, return_value=sessions),
            patch(f"{_MOD}.output_system_message") as mock_msg,
        ):
            _check_file_hotspot(state, ["auth.py"])

        mock_msg.assert_not_called()

    def test_alerts_at_threshold(self):
        """임계값 이상 세션에서 수정된 파일은 알림 표시."""
        state = _make_state()
        sessions = [
            _make_mock_session(f"s{i}", ["auth.py"])
            for i in range(_HOTSPOT_SESSION_THRESHOLD)  # 정확히 threshold개
        ]

        with (
            patch(_MANAGER_PATH, return_value=sessions),
            patch(f"{_MOD}.output_system_message") as mock_msg,
        ):
            _check_file_hotspot(state, ["auth.py"])

        mock_msg.assert_called_once()
        msg = mock_msg.call_args[0][0]
        assert "auth.py" in msg
        assert str(_HOTSPOT_SESSION_THRESHOLD) in msg

    def test_skips_already_alerted_files(self):
        """이미 알림한 파일은 다시 알림 없음."""
        state = _make_state()
        state.plane_context.hotspot_alerted_files = ["auth.py"]
        sessions = [
            _make_mock_session(f"s{i}", ["auth.py"])
            for i in range(_HOTSPOT_SESSION_THRESHOLD + 5)
        ]

        with (
            patch(_MANAGER_PATH, return_value=sessions),
            patch(f"{_MOD}.output_system_message") as mock_msg,
        ):
            _check_file_hotspot(state, ["auth.py"])

        mock_msg.assert_not_called()

    def test_updates_alerted_files_state(self):
        """알림 후 state.plane_context.hotspot_alerted_files에 파일 추가."""
        state = _make_state()
        sessions = [
            _make_mock_session(f"s{i}", ["auth.py"])
            for i in range(_HOTSPOT_SESSION_THRESHOLD)
        ]

        with (
            patch(_MANAGER_PATH, return_value=sessions),
            patch(f"{_MOD}.output_system_message"),
        ):
            _check_file_hotspot(state, ["auth.py"])

        assert "auth.py" in state.plane_context.hotspot_alerted_files

    def test_fail_open_on_count_error(self):
        """집계 오류 시 예외를 전파하지 않는다."""
        state = _make_state()

        with patch(_MANAGER_PATH, side_effect=Exception("DB 오류")):
            _check_file_hotspot(state, ["auth.py"])  # 예외 없어야 함
