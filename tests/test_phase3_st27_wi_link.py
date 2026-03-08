"""ST-27: 커밋 메시지 WI 식별자 감지 → 세션 연결 제안 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oh_my_kanban.hooks.post_tool import _suggest_wi_link_from_commit
from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.post_tool"


def _make_state(has_wi: bool = False) -> SessionState:
    state = SessionState(session_id="sess-st27-001")
    if has_wi:
        state.plane_context.work_item_ids = ["wi-uuid-001"]
        state.plane_context.project_id = "proj-uuid"
    return state


class TestSuggestWiLinkFromCommit:
    def test_skips_when_wi_already_linked(self):
        """세션에 이미 WI가 연결된 경우 제안 없음."""
        state = _make_state(has_wi=True)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'feat: OMK-42'")

        mock_ctx.assert_not_called()

    def test_no_suggestion_when_no_identifier(self):
        """커밋 메시지에 WI 식별자가 없으면 제안 없음."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'feat: add login'")

        mock_ctx.assert_not_called()

    def test_suggests_when_identifier_found(self):
        """커밋 메시지에 WI 식별자(OMK-42)가 있으면 연결 제안."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'feat: OMK-42 add OAuth'")

        mock_ctx.assert_called_once()
        ctx_msg = mock_ctx.call_args[0][1]
        assert "OMK-42" in ctx_msg

    def test_extracts_multiple_identifiers(self):
        """여러 WI 식별자가 있으면 모두 포함."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'fix: OMK-42 OMK-43'")

        mock_ctx.assert_called_once()
        ctx_msg = mock_ctx.call_args[0][1]
        assert "OMK-42" in ctx_msg
        assert "OMK-43" in ctx_msg

    def test_caps_at_three_identifiers(self):
        """4개 이상의 식별자는 3개까지만 표시."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            cmd = "git commit -m 'feat: OMK-1 OMK-2 OMK-3 OMK-4'"
            _suggest_wi_link_from_commit(state, cmd)

        ctx_msg = mock_ctx.call_args[0][1]
        assert "OMK-1" in ctx_msg
        assert "OMK-2" in ctx_msg
        assert "OMK-3" in ctx_msg
        assert "OMK-4" not in ctx_msg

    def test_deduplicates_identifiers(self):
        """중복 식별자는 한 번만 표시."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'fix: OMK-42 OMK-42'")

        ctx_msg = mock_ctx.call_args[0][1]
        assert ctx_msg.count("OMK-42") == 1

    def test_suggestion_includes_focus_command(self):
        """제안 메시지에 /oh-my-kanban:focus 힌트 포함."""
        state = _make_state(has_wi=False)

        with patch(f"{_MOD}.output_context") as mock_ctx:
            _suggest_wi_link_from_commit(state, "git commit -m 'feat: OMK-99'")

        ctx_msg = mock_ctx.call_args[0][1]
        assert "focus" in ctx_msg.lower() or "연결" in ctx_msg
