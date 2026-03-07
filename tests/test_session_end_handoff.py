"""ST-22: 핸드오프 메모 유도 + ST-25 eco format 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from oh_my_kanban.session.state import PlaneContext, SessionState, now_iso


def _make_state(wi_ids: list[str] | None = None) -> SessionState:
    state = SessionState(session_id="sess-end-001")
    if wi_ids:
        state.plane_context.work_item_ids = wi_ids
        state.plane_context.project_id = "proj-uuid"
    return state


def _make_cfg(api_key: str = "key", format_preset: str = "normal"):
    cfg = MagicMock()
    cfg.api_key = api_key
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj-uuid"
    cfg.base_url = "https://plane.example.com"
    cfg.upload_level = "metadata"
    cfg.format_preset = format_preset
    return cfg


def _run_main(hook_input: dict) -> None:
    import sys
    from io import StringIO
    from unittest.mock import patch as _patch

    with _patch("sys.stdin", StringIO("")):
        from oh_my_kanban.hooks.session_end import main
        main()


class TestHandoffMemoInjection:
    def test_output_context_called_when_wi_connected_and_api_configured(self):
        """WI 연결 + API 키 있을 때 핸드오프 메모 additionalContext가 주입된다."""
        state = _make_state(wi_ids=["wi-uuid-001"])
        cfg = _make_cfg()
        hook_input = {"session_id": "sess-end-001"}

        with (
            patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-end-001"),
            patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.session_end.save_session"),
            patch("oh_my_kanban.hooks.session_end.reset_hud"),
            patch("oh_my_kanban.hooks.session_end._post_plane_comment", return_value=True),
            patch("oh_my_kanban.hooks.session_end.notify_success"),
            patch("oh_my_kanban.hooks.session_end.output_context") as mock_ctx,
        ):
            from oh_my_kanban.hooks.session_end import main
            main()

        mock_ctx.assert_called_once()
        call_args = mock_ctx.call_args[0]
        assert call_args[0] == "SessionEnd"
        assert "핸드오프" in call_args[1]
        assert "다음 세션" in call_args[1]

    def test_output_context_not_called_when_no_wi(self):
        """WI가 연결되지 않았으면 핸드오프 additionalContext가 주입되지 않는다."""
        state = _make_state(wi_ids=[])  # WI 없음
        cfg = _make_cfg()
        hook_input = {"session_id": "sess-end-001"}

        with (
            patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-end-001"),
            patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.session_end.save_session"),
            patch("oh_my_kanban.hooks.session_end.reset_hud"),
            patch("oh_my_kanban.hooks.session_end.output_context") as mock_ctx,
        ):
            from oh_my_kanban.hooks.session_end import main
            main()

        mock_ctx.assert_not_called()

    def test_output_context_not_called_when_no_api_key(self):
        """API 키가 없으면 핸드오프 additionalContext가 주입되지 않는다."""
        state = _make_state(wi_ids=["wi-uuid-001"])
        cfg = _make_cfg(api_key="")  # API 키 없음
        hook_input = {"session_id": "sess-end-001"}

        with (
            patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-end-001"),
            patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.session_end.save_session"),
            patch("oh_my_kanban.hooks.session_end.reset_hud"),
            patch("oh_my_kanban.hooks.session_end._post_plane_comment", return_value=False),
            patch("oh_my_kanban.hooks.session_end.output_context") as mock_ctx,
        ):
            from oh_my_kanban.hooks.session_end import main
            main()

        mock_ctx.assert_not_called()


class TestFormatPresetEcoSkipsComment:
    def test_eco_preset_skips_session_end_comment(self):
        """format_preset=eco이면 세션 종료 Plane 댓글을 생략한다."""
        state = _make_state(wi_ids=["wi-uuid-001"])
        cfg = _make_cfg(format_preset="eco")
        hook_input = {"session_id": "sess-end-001"}

        with (
            patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-end-001"),
            patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.session_end.save_session"),
            patch("oh_my_kanban.hooks.session_end.reset_hud"),
            patch("oh_my_kanban.hooks.session_end._post_plane_comment") as mock_post,
            patch("oh_my_kanban.hooks.session_end.output_context"),
        ):
            from oh_my_kanban.hooks.session_end import main
            main()

        mock_post.assert_not_called()

    def test_normal_preset_posts_comment(self):
        """format_preset=normal이면 세션 종료 댓글을 게시한다."""
        state = _make_state(wi_ids=["wi-uuid-001"])
        cfg = _make_cfg(format_preset="normal")
        hook_input = {"session_id": "sess-end-001"}

        with (
            patch("oh_my_kanban.hooks.session_end.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.session_end.get_session_id", return_value="sess-end-001"),
            patch("oh_my_kanban.hooks.session_end.load_session", return_value=state),
            patch("oh_my_kanban.hooks.session_end.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.session_end.save_session"),
            patch("oh_my_kanban.hooks.session_end.reset_hud"),
            patch("oh_my_kanban.hooks.session_end._post_plane_comment", return_value=True) as mock_post,
            patch("oh_my_kanban.hooks.session_end.notify_success"),
            patch("oh_my_kanban.hooks.session_end.output_context"),
        ):
            from oh_my_kanban.hooks.session_end import main
            main()

        mock_post.assert_called_once()
