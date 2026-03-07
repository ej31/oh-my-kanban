"""Orphan WI 감지 유닛 테스트."""
import json
from unittest.mock import patch, MagicMock
import pytest
from oh_my_kanban.hooks.common import handle_orphan_wi
from oh_my_kanban.session.state import SessionState, PlaneContext


def make_state(wi_ids: list[str]) -> SessionState:
    state = SessionState(session_id="test-session")
    state.plane_context = PlaneContext(
        project_id="proj-1",
        work_item_ids=wi_ids,
    )
    return state


def test_handle_orphan_single_wi_all_deleted(capsys):
    state = make_state(["wi-abc123"])
    handle_orphan_wi(state, "wi-abc123")
    # stale 목록에 추가됨
    assert "wi-abc123" in state.plane_context.stale_work_item_ids
    # stdout에 systemMessage 출력됨
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "systemMessage" in output
    assert "삭제" in output["systemMessage"]


def test_handle_orphan_partial_wi_deleted(capsys):
    state = make_state(["wi-1", "wi-2"])
    handle_orphan_wi(state, "wi-1")
    assert "wi-1" in state.plane_context.stale_work_item_ids
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "1개 WI로 계속" in output["systemMessage"]


def test_handle_orphan_no_duplicate(capsys):
    state = make_state(["wi-abc"])
    handle_orphan_wi(state, "wi-abc")
    # 두 번째 호출은 무시됨
    handle_orphan_wi(state, "wi-abc")
    assert state.plane_context.stale_work_item_ids.count("wi-abc") == 1


def test_plane_context_builder_404_marker():
    """_fetch_work_item이 404 응답 시 __deleted__ 마커를 반환한다."""
    from oh_my_kanban.session.plane_context_builder import _fetch_work_item

    mock_resp = MagicMock()
    mock_resp.status_code = 404

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    result = _fetch_work_item(
        mock_client, "https://plane.example.com", "ws", "proj", "wi-deleted", {}
    )
    assert result is not None
    assert result.get("__deleted__") is True
    assert result.get("__status__") == 404


def test_plane_context_builder_410_marker():
    """_fetch_work_item이 410 응답 시 __deleted__ 마커를 반환한다."""
    from oh_my_kanban.session.plane_context_builder import _fetch_work_item

    mock_resp = MagicMock()
    mock_resp.status_code = 410

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    result = _fetch_work_item(
        mock_client, "https://plane.example.com", "ws", "proj", "wi-gone", {}
    )
    assert result.get("__deleted__") is True
    assert result.get("__status__") == 410
