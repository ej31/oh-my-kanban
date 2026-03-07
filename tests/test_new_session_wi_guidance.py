"""ST-18: 신규 세션 WI 선택 안내 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


_MOD_START = "oh_my_kanban.hooks.session_start"


def _make_cfg(api_key: str = "key", workspace_slug: str = "ws", project_id: str = "proj-uuid"):
    cfg = MagicMock()
    cfg.api_key = api_key
    cfg.workspace_slug = workspace_slug
    cfg.project_id = project_id
    cfg.base_url = "https://plane.example.com"
    return cfg


def _make_wi_result(seq: int, name: str, group: str = "started") -> dict:
    return {
        "id": f"wi-uuid-{seq:03d}",
        "sequence_id": seq,
        "name": name,
        "state_detail": {"group": group, "name": "In Progress"},
    }


class TestFetchActiveWorkItems:
    def test_returns_empty_when_no_api_key(self):
        """API 키가 없으면 빈 리스트를 반환한다."""
        from oh_my_kanban.hooks.session_start import _fetch_active_work_items

        cfg = _make_cfg(api_key="")
        result = _fetch_active_work_items(cfg)
        assert result == []

    def test_returns_empty_when_no_project_id(self):
        """project_id가 없으면 빈 리스트를 반환한다."""
        from oh_my_kanban.hooks.session_start import _fetch_active_work_items

        cfg = _make_cfg(project_id="")
        result = _fetch_active_work_items(cfg)
        assert result == []

    def test_returns_in_progress_items_on_200(self):
        """HTTP 200 응답에서 in_progress 상태 WI를 반환한다."""
        from oh_my_kanban.hooks.session_start import _fetch_active_work_items

        cfg = _make_cfg()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                _make_wi_result(1, "Task A", group="started"),
                _make_wi_result(2, "Task B", group="backlog"),  # 필터됨
                _make_wi_result(3, "Task C", group="in_progress"),
            ]
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            result = _fetch_active_work_items(cfg)

        assert len(result) == 2
        assert result[0]["sequence_id"] == 1
        assert result[1]["sequence_id"] == 3

    def test_returns_empty_on_non_200(self):
        """HTTP 200이 아니면 빈 리스트를 반환한다 (fail-open)."""
        from oh_my_kanban.hooks.session_start import _fetch_active_work_items

        cfg = _make_cfg()
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            result = _fetch_active_work_items(cfg)

        assert result == []

    def test_returns_empty_on_exception(self):
        """네트워크 예외 시 빈 리스트를 반환한다 (fail-open)."""
        from oh_my_kanban.hooks.session_start import _fetch_active_work_items

        cfg = _make_cfg()
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("네트워크 오류")
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            result = _fetch_active_work_items(cfg)

        assert result == []


class TestInjectNewSessionWiGuidance:
    def test_outputs_system_message_with_active_wis(self):
        """활성 WI가 있으면 systemMessage를 출력한다."""
        from oh_my_kanban.hooks.session_start import _inject_new_session_wi_guidance

        cfg = _make_cfg()
        active_wis = [
            _make_wi_result(10, "OAuth2 구현"),
            _make_wi_result(11, "테스트 작성"),
        ]

        with (
            patch(f"{_MOD_START}._fetch_active_work_items", return_value=active_wis),
            patch(f"{_MOD_START}.output_system_message") as mock_out,
        ):
            _inject_new_session_wi_guidance(cfg)

        mock_out.assert_called_once()
        user_msg, hook_name, ctx = mock_out.call_args[0]
        assert "OMK-10" in user_msg
        assert "OMK-11" in user_msg
        assert "[omk]" in user_msg
        assert hook_name == "SessionStart"
        assert "OMK-10" in ctx

    def test_skips_when_no_active_wis(self):
        """활성 WI가 없으면 systemMessage를 출력하지 않는다."""
        from oh_my_kanban.hooks.session_start import _inject_new_session_wi_guidance

        cfg = _make_cfg()

        with (
            patch(f"{_MOD_START}._fetch_active_work_items", return_value=[]),
            patch(f"{_MOD_START}.output_system_message") as mock_out,
        ):
            _inject_new_session_wi_guidance(cfg)

        mock_out.assert_not_called()

    def test_shows_up_to_5_wis(self):
        """최대 5개까지만 WI를 표시한다."""
        from oh_my_kanban.hooks.session_start import _inject_new_session_wi_guidance

        cfg = _make_cfg()
        active_wis = [_make_wi_result(i, f"Task {i}") for i in range(1, 8)]  # 7개

        with (
            patch(f"{_MOD_START}._fetch_active_work_items", return_value=active_wis),
            patch(f"{_MOD_START}.output_system_message") as mock_out,
        ):
            _inject_new_session_wi_guidance(cfg)

        user_msg = mock_out.call_args[0][0]
        # OMK-1~5는 표시, OMK-6~7은 표시 안 됨
        assert "OMK-5" in user_msg
        assert "OMK-6" not in user_msg
