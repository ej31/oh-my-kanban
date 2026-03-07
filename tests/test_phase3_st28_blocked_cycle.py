"""ST-28: 차단 WI / Cycle 마감 알림 테스트."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.session_start import _check_blocked_and_cycle_deadline
from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.session_start"


def _make_state(focused_id: str = "wi-main") -> SessionState:
    state = SessionState(session_id="sess-st28-001")
    state.plane_context.work_item_ids = [focused_id]
    state.plane_context.focused_work_item_id = focused_id
    state.plane_context.project_id = "proj-uuid"
    return state


def _make_cfg():
    cfg = MagicMock()
    cfg.api_key = "key"
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj-uuid"
    cfg.base_url = "https://plane.example.com"
    return cfg


def _make_http_mock_factory(url_responses: dict):
    """URL별로 다른 응답을 반환하는 HTTP mock."""
    def _get_side_effect(url, **kwargs):
        for key, (status, body) in url_responses.items():
            if key in url:
                resp = MagicMock()
                resp.status_code = status
                resp.json.return_value = body
                return resp
        resp = MagicMock()
        resp.status_code = 404
        resp.json.return_value = {}
        return resp

    mock_client = MagicMock()
    mock_client.get.side_effect = _get_side_effect
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_client)
    mock_cm.__exit__ = MagicMock(return_value=False)
    return mock_client, mock_cm


class TestBlockedWiAlert:
    def test_no_alert_when_no_focused_wi(self):
        """focused_work_item_id가 없으면 알림 없음."""
        state = _make_state()
        state.plane_context.focused_work_item_id = None
        cfg = _make_cfg()

        with (
            patch("httpx.Client") as mock_httpx,
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        mock_sys.assert_not_called()

    def test_no_alert_when_no_blocked_relations(self):
        """blocked_by 관계가 없으면 차단 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        url_responses = {
            "issue-relations": (200, {"results": [{"relation_type": "relates_to"}]}),
            "cycles": (200, {"results": []}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        blocked_calls = [
            c for c in mock_sys.call_args_list
            if "차단" in str(c)
        ]
        assert len(blocked_calls) == 0

    def test_alerts_when_blocked_by_relation_exists(self):
        """blocked_by 관계가 있으면 차단 알림 표시."""
        state = _make_state()
        cfg = _make_cfg()
        url_responses = {
            "issue-relations": (200, {"results": [
                {
                    "relation_type": "blocked_by",
                    "related_issue": {"sequence_id": 99, "name": "DB 스키마 변경"},
                }
            ]}),
            "cycles": (200, {"results": []}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        blocked_calls = [c for c in mock_sys.call_args_list if "차단" in str(c)]
        assert len(blocked_calls) >= 1
        assert "OMK-99" in str(blocked_calls[0])

    def test_fail_open_on_relation_api_error(self):
        """관계 API 오류 시 예외를 전파하지 않는다."""
        state = _make_state()
        cfg = _make_cfg()
        url_responses = {
            "issue-relations": (500, {}),
            "cycles": (200, {"results": []}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with patch("httpx.Client", return_value=mock_cm):
            _check_blocked_and_cycle_deadline(state, cfg)  # 예외 없어야 함


class TestCycleDeadlineAlert:
    def test_no_alert_when_no_active_cycle(self):
        """활성 Cycle이 없으면 마감 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        url_responses = {
            "issue-relations": (200, {"results": []}),
            "cycles": (200, {"results": []}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        deadline_calls = [c for c in mock_sys.call_args_list if "마감" in str(c)]
        assert len(deadline_calls) == 0

    def test_alerts_when_cycle_deadline_within_3_days(self):
        """Cycle 마감이 3일 이내이면 알림 표시."""
        state = _make_state()
        cfg = _make_cfg()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        url_responses = {
            "issue-relations": (200, {"results": []}),
            "cycles": (200, {"results": [
                {"name": "Sprint 5", "status": "current", "end_date": tomorrow}
            ]}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        deadline_calls = [c for c in mock_sys.call_args_list if "마감" in str(c)]
        assert len(deadline_calls) >= 1
        assert "Sprint 5" in str(deadline_calls[0])

    def test_no_alert_when_cycle_deadline_far(self):
        """Cycle 마감이 4일 이상 남았으면 알림 없음."""
        state = _make_state()
        cfg = _make_cfg()
        far_future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        url_responses = {
            "issue-relations": (200, {"results": []}),
            "cycles": (200, {"results": [
                {"name": "Sprint 6", "status": "current", "end_date": far_future}
            ]}),
        }
        _, mock_cm = _make_http_mock_factory(url_responses)

        with (
            patch("httpx.Client", return_value=mock_cm),
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        deadline_calls = [c for c in mock_sys.call_args_list if "마감" in str(c)]
        assert len(deadline_calls) == 0

    def test_no_alert_when_no_api_key(self):
        """API 키가 없으면 API 호출 없음."""
        state = _make_state()
        cfg = _make_cfg()
        cfg.api_key = ""

        with (
            patch("httpx.Client") as mock_httpx,
            patch(f"{_MOD}.output_system_message") as mock_sys,
        ):
            _check_blocked_and_cycle_deadline(state, cfg)

        mock_httpx.assert_not_called()
        mock_sys.assert_not_called()
