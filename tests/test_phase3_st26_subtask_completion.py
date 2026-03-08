"""ST-26: Sub-task 전체 완료 → 완료 처리 유도 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.user_prompt import _check_subtask_completion
from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.user_prompt"


def _make_state(focused_id: str = "wi-uuid-main") -> SessionState:
    state = SessionState(session_id="sess-st26-001")
    state.plane_context.work_item_ids = [focused_id]
    state.plane_context.focused_work_item_id = focused_id
    state.plane_context.project_id = "proj-uuid"
    return state


def _make_cfg(api_key: str = "key"):
    cfg = MagicMock()
    cfg.api_key = api_key
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj-uuid"
    cfg.base_url = "https://plane.example.com"
    return cfg


def _make_http_mock(status_code: int = 200, body: dict | None = None):
    if body is None:
        body = {"results": []}
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body
    mock_cm = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)
    return mock_cm


class TestCheckSubtaskCompletion:
    def test_skips_when_already_nudged(self):
        """이미 알림을 보냈으면 다시 보내지 않는다."""
        state = _make_state()
        state.plane_context.subtask_completion_nudged_ids = ["wi-uuid-main"]
        cfg = _make_cfg()

        with patch("httpx.Client") as mock_httpx:
            _check_subtask_completion(state, cfg)

        mock_httpx.assert_not_called()

    def test_skips_when_no_focused_wi(self):
        """focused_work_item_id가 없으면 건너뜀."""
        state = _make_state()
        state.plane_context.focused_work_item_id = None
        cfg = _make_cfg()

        with patch("httpx.Client") as mock_httpx:
            _check_subtask_completion(state, cfg)

        mock_httpx.assert_not_called()

    def test_skips_when_no_api_key(self):
        """API 키가 없으면 건너뜀."""
        state = _make_state()
        cfg = _make_cfg(api_key="")

        with patch("httpx.Client") as mock_httpx:
            _check_subtask_completion(state, cfg)

        mock_httpx.assert_not_called()

    def test_no_nudge_when_no_subtasks(self):
        """sub-task가 없으면 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        mock_cm = _make_http_mock(body={"results": []})

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_subtask_completion(state, cfg)

        mock_sys.assert_not_called()
        assert state.plane_context.subtask_completion_nudged_ids == []

    def test_no_nudge_when_subtask_incomplete(self):
        """미완료 sub-task가 있으면 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        body = {
            "results": [
                {"id": "sub-1", "state_detail": {"group": "completed"}},
                {"id": "sub-2", "state_detail": {"group": "started"}},  # 미완료
            ]
        }
        mock_cm = _make_http_mock(body=body)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_subtask_completion(state, cfg)

        mock_sys.assert_not_called()
        assert state.plane_context.subtask_completion_nudged_ids == []

    def test_nudges_when_all_subtasks_complete(self):
        """모든 sub-task가 완료이면 사용자에게 알림."""
        state = _make_state()
        cfg = _make_cfg()
        body = {
            "results": [
                {"id": "sub-1", "state_detail": {"group": "completed"}},
                {"id": "sub-2", "state_detail": {"group": "cancelled"}},
            ]
        }
        mock_cm = _make_http_mock(body=body)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_subtask_completion(state, cfg)

        mock_sys.assert_called_once()
        msg = mock_sys.call_args[0][0]
        assert "2개" in msg or "모두 완료" in msg
        assert state.plane_context.subtask_completion_nudged_ids == ["wi-uuid-main"]

    def test_sets_nudged_flag_to_prevent_repeat(self):
        """알림 후 nudged 플래그가 True로 설정돼 중복 알림 방지."""
        state = _make_state()
        cfg = _make_cfg()
        body = {"results": [{"id": "sub-1", "state_detail": {"group": "completed"}}]}
        mock_cm = _make_http_mock(body=body)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message"),
        ):
            _check_subtask_completion(state, cfg)

        assert state.plane_context.subtask_completion_nudged_ids == ["wi-uuid-main"]

    def test_fail_open_on_http_error(self):
        """HTTP 오류 시 예외를 전파하지 않는다."""
        state = _make_state()
        cfg = _make_cfg()
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("연결 오류")
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _check_subtask_completion(state, cfg)  # 예외 없어야 함

    def test_skips_on_non_200_response(self):
        """200 이외 응답 시 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        mock_cm = _make_http_mock(status_code=404, body={})

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_subtask_completion(state, cfg)

        mock_sys.assert_not_called()
