"""ST-20: 팀원 댓글 2분 throttle 폴링 + circuit breaker 테스트."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.user_prompt import (
    _COMMENT_POLL_INTERVAL_SEC,
    _COMMENT_POLL_MAX_FAILURES,
    _poll_comments,
)
from oh_my_kanban.session.state import PlaneContext, SessionState, now_iso


_TEST_PROJECT_UUID = "00000000-0000-0000-0000-000000000001"
_TEST_WI_UUID = "00000000-0000-0000-0000-000000000011"


def _make_state(
    focused_id: str = _TEST_WI_UUID,
    last_check: str | None = None,
    known_ids: list[str] | None = None,
    failures: int = 0,
) -> SessionState:
    state = SessionState(session_id="sess-poll-001")
    state.plane_context.focused_work_item_id = focused_id
    state.plane_context.project_id = _TEST_PROJECT_UUID
    state.plane_context.work_item_ids = [focused_id]
    if last_check:
        state.plane_context.last_comment_check = last_check
    if known_ids is not None:
        state.plane_context.known_comment_ids = known_ids
    state.plane_context.comment_poll_failures = failures
    return state


def _make_cfg(api_key: str = "key"):
    cfg = MagicMock()
    cfg.api_key = api_key
    cfg.workspace_slug = "ws"
    cfg.project_id = _TEST_PROJECT_UUID
    cfg.base_url = "https://plane.example.com"
    return cfg


def _past_timestamp(seconds_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return dt.isoformat()


class TestPollCommentsThrottle:
    def test_skips_when_no_focused_wi(self):
        """focused_work_item_id가 없으면 폴링하지 않는다."""
        state = _make_state(focused_id="")
        cfg = _make_cfg()

        with patch("httpx.Client") as mock_httpx:
            _poll_comments(state, cfg)
            mock_httpx.assert_not_called()

    def test_skips_when_circuit_breaker_triggered(self):
        """연속 실패 횟수가 임계값 이상이면 폴링하지 않는다."""
        state = _make_state(failures=_COMMENT_POLL_MAX_FAILURES)
        cfg = _make_cfg()

        with patch("httpx.Client") as mock_httpx:
            _poll_comments(state, cfg)
            mock_httpx.assert_not_called()

    def test_skips_when_within_throttle_window(self):
        """마지막 폴링으로부터 2분 미경과 시 폴링하지 않는다."""
        state = _make_state(last_check=_past_timestamp(60))  # 1분 전
        cfg = _make_cfg()

        with patch("httpx.Client") as mock_httpx:
            _poll_comments(state, cfg)
            mock_httpx.assert_not_called()

    def test_polls_when_throttle_window_elapsed(self):
        """마지막 폴링으로부터 2분 이상 경과하면 폴링한다."""
        state = _make_state(last_check=_past_timestamp(130))  # 2분 10초 전
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)

        mock_client.get.assert_called_once()

    def test_polls_when_last_check_is_none(self):
        """last_comment_check가 None이면 즉시 폴링한다."""
        state = _make_state(last_check=None)
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)

        mock_client.get.assert_called_once()


class TestPollCommentsResults:
    def test_outputs_system_message_for_new_comments(self, capsys):
        """새 댓글이 있으면 output_system_message를 호출한다."""
        state = _make_state(known_ids=["old-id-1"])
        cfg = _make_cfg()

        new_comment = {
            "id": "new-id-2",
            "comment_stripped": "새로운 의견입니다",
            "actor_detail": {"display_name": "김철수"},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [new_comment]}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.user_prompt.output_system_message") as mock_out,
        ):
            _poll_comments(state, cfg)

        mock_out.assert_called_once()
        assert "김철수" in mock_out.call_args[0][0]
        assert "새로운 의견" in mock_out.call_args[0][0]

    def test_skips_omk_self_comments(self):
        """omk 자체 댓글(## omk 시작)은 알림에서 제외한다."""
        state = _make_state(known_ids=[])
        cfg = _make_cfg()

        omk_comment = {
            "id": "omk-id-1",
            "comment_stripped": "## omk 세션 시작\n세션 ID: abc...",
            "actor_detail": {"display_name": "Claude"},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [omk_comment]}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.user_prompt.output_system_message") as mock_out,
        ):
            _poll_comments(state, cfg)

        mock_out.assert_not_called()

    def test_updates_known_comment_ids_after_poll(self):
        """폴링 성공 후 known_comment_ids가 갱신된다."""
        state = _make_state(known_ids=["old-id"])
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"id": "old-id", "comment_stripped": "기존", "actor_detail": {}},
                {"id": "new-id", "comment_stripped": "신규", "actor_detail": {"display_name": "팀원"}},
            ]
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.user_prompt.output_system_message"),
        ):
            _poll_comments(state, cfg)

        assert "old-id" in state.plane_context.known_comment_ids
        assert "new-id" in state.plane_context.known_comment_ids

    def test_updates_last_comment_check_after_poll(self):
        """폴링 성공 후 last_comment_check가 갱신된다."""
        state = _make_state()
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)

        assert state.plane_context.last_comment_check is not None

    def test_resets_failure_counter_on_success(self):
        """폴링 성공 시 circuit breaker 카운터가 0으로 초기화된다."""
        state = _make_state(failures=2)
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)

        assert state.plane_context.comment_poll_failures == 0

    def test_increments_failure_counter_on_http_error(self):
        """HTTP 오류 시 circuit breaker 카운터가 증가한다."""
        state = _make_state(failures=0)
        cfg = _make_cfg()

        mock_resp = MagicMock()
        mock_resp.status_code = 500

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)

        assert state.plane_context.comment_poll_failures == 1

    def test_increments_failure_counter_on_exception(self):
        """네트워크 예외 시 circuit breaker 카운터가 증가한다 (fail-open)."""
        state = _make_state(failures=1)
        cfg = _make_cfg()

        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("연결 오류")
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _poll_comments(state, cfg)  # 예외가 전파되지 않아야 함

        assert state.plane_context.comment_poll_failures == 2
