"""ST-15: Recording Mode - upload_level 상수 및 경고 테스트."""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.session_end import UPLOAD_LEVEL_FULL, UPLOAD_LEVEL_METADATA


# ── 상수 검증 ──────────────────────────────────────────────────────────────────


def test_upload_level_metadata_constant():
    """UPLOAD_LEVEL_METADATA 상수가 'metadata' 이어야 한다."""
    assert UPLOAD_LEVEL_METADATA == "metadata"


def test_upload_level_full_constant():
    """UPLOAD_LEVEL_FULL 상수가 'full' 이어야 한다."""
    assert UPLOAD_LEVEL_FULL == "full"


# ── main() upload_level 처리 ────────────────────────────────────────────────────


def _make_state(*, opted_out: bool = False):
    """테스트용 SessionState 모의 객체를 생성한다."""
    from oh_my_kanban.session.state import SessionState
    state = SessionState(session_id="sess-test-001")
    state.opted_out = opted_out
    return state


def _make_cfg(upload_level: str = "metadata"):
    """테스트용 Config 모의 객체를 생성한다."""
    cfg = MagicMock()
    cfg.api_key = "test_key"
    cfg.workspace_slug = "test_ws"
    cfg.base_url = "https://plane.example.com"
    cfg.project_id = "proj-uuid"
    cfg.upload_level = upload_level
    return cfg


def test_upload_level_full_prints_warning(capsys):
    """upload_level=full 이면 stderr에 경고를 출력한다."""
    from oh_my_kanban.hooks.session_end import main

    state = _make_state()
    cfg = _make_cfg(upload_level="full")

    hook_input = {"session_id": "sess-test-001"}

    with (
        patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
        patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-test-001"),
        patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
        patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
        patch("oh_my_kanban.hooks.session_end.save_session"),
        patch("oh_my_kanban.hooks.session_end.reset_hud"),
    ):
        main()

    captured = capsys.readouterr()
    assert "full" in captured.err
    assert "미지원" in captured.err or "metadata" in captured.err


def test_upload_level_metadata_no_warning(capsys):
    """upload_level=metadata 이면 경고를 출력하지 않는다."""
    from oh_my_kanban.hooks.session_end import main

    state = _make_state()
    cfg = _make_cfg(upload_level="metadata")

    hook_input = {"session_id": "sess-test-001"}

    with (
        patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
        patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-test-001"),
        patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
        patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
        patch("oh_my_kanban.hooks.session_end.save_session"),
        patch("oh_my_kanban.hooks.session_end.reset_hud"),
    ):
        main()

    captured = capsys.readouterr()
    # upload_level 관련 경고가 없어야 한다
    assert "upload_level=full" not in captured.err


def test_upload_level_full_still_completes_normally():
    """upload_level=full 이어도 세션 완료 처리는 정상 수행된다."""
    from oh_my_kanban.hooks.session_end import main

    state = _make_state()
    cfg = _make_cfg(upload_level="full")

    hook_input = {"session_id": "sess-test-001"}
    save_mock = MagicMock()

    with (
        patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
        patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-test-001"),
        patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
        patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
        patch("oh_my_kanban.hooks.session_end.save_session", save_mock),
        patch("oh_my_kanban.hooks.session_end.reset_hud"),
    ):
        main()

    # save_session 호출 확인 (세션 완료 상태 저장)
    save_mock.assert_called_once()
