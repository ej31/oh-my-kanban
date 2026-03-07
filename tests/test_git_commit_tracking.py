"""ST-24: PostToolUse git commit 감지 + WI 댓글 자동 기록 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.hooks.post_tool import (
    _detect_git_commit,
    _extract_commit_hash,
    _post_commit_comment,
)
from oh_my_kanban.session.state import PlaneContext, SessionState


# ── _detect_git_commit ────────────────────────────────────────────────────────


class TestDetectGitCommit:
    def test_detects_bash_git_commit(self):
        """Bash + git commit 명령을 감지한다."""
        found, cmd = _detect_git_commit("Bash", {"command": "git commit -m 'feat: add login'"})
        assert found is True
        assert "git commit" in cmd

    def test_rejects_non_bash_tool(self):
        """Bash가 아닌 도구는 감지하지 않는다."""
        found, _ = _detect_git_commit("Edit", {"command": "git commit -m '...'"})
        assert found is False

    def test_rejects_bash_without_git_commit(self):
        """git commit이 없는 Bash 명령은 감지하지 않는다."""
        found, _ = _detect_git_commit("Bash", {"command": "git status"})
        assert found is False

    def test_rejects_no_commit_flag(self):
        """--no-commit 플래그가 있으면 감지하지 않는다."""
        found, _ = _detect_git_commit("Bash", {"command": "git merge --no-commit feature"})
        assert found is False

    def test_rejects_empty_command(self):
        """명령이 없으면 감지하지 않는다."""
        found, _ = _detect_git_commit("Bash", {})
        assert found is False


# ── _extract_commit_hash ──────────────────────────────────────────────────────


class TestExtractCommitHash:
    def test_extracts_7char_hash(self):
        """git commit 출력에서 7자리 해시를 추출한다."""
        output = "[master abc1234] feat: add login\n 1 file changed"
        assert _extract_commit_hash(output) == "abc1234"

    def test_extracts_hash_from_branch_slash(self):
        """브랜치에 슬래시가 있는 경우에도 해시를 추출한다."""
        output = "[feat/login a1b2c3d] feat: login API"
        assert _extract_commit_hash(output) == "a1b2c3d"

    def test_returns_empty_for_empty_output(self):
        """출력이 없으면 빈 문자열을 반환한다."""
        assert _extract_commit_hash("") == ""
        assert _extract_commit_hash(None) == ""  # type: ignore

    def test_returns_empty_when_no_hash(self):
        """해시 패턴이 없으면 빈 문자열을 반환한다."""
        assert _extract_commit_hash("nothing here") == ""


# ── _post_commit_comment ──────────────────────────────────────────────────────


class TestPostCommitComment:
    def _make_state(self, wi_ids: list[str] | None = None) -> SessionState:
        state = SessionState(session_id="sess-commit-001")
        if wi_ids:
            state.plane_context.work_item_ids = wi_ids
            state.plane_context.project_id = "proj-uuid"
        return state

    def _make_cfg(self, api_key: str = "key"):
        cfg = MagicMock()
        cfg.api_key = api_key
        cfg.workspace_slug = "ws"
        cfg.project_id = "proj-uuid"
        cfg.base_url = "https://plane.example.com"
        return cfg

    def _make_http_mock(self, status_code: int = 201):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)
        return mock_client, mock_cm

    def test_posts_comment_to_wi(self):
        """WI가 연결된 경우 커밋 댓글을 Plane에 게시한다."""
        state = self._make_state(wi_ids=["wi-uuid-001"])
        cfg = self._make_cfg()
        mock_client, mock_cm = self._make_http_mock()

        with (
            patch("oh_my_kanban.hooks.post_tool.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.post_tool.create_plane_http_client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.post_tool.output_context"),
        ):
            _post_commit_comment(state, "abc1234", "git commit -m 'feat'")

        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        assert "abc1234" in kwargs["json"]["comment_html"]

    def test_skips_when_no_wi(self):
        """WI가 없으면 댓글을 게시하지 않는다."""
        state = self._make_state(wi_ids=[])
        cfg = self._make_cfg()

        with (
            patch("oh_my_kanban.hooks.post_tool.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.post_tool.create_plane_http_client") as mock_create,
        ):
            _post_commit_comment(state, "abc1234", "git commit -m '...'")

        mock_create.assert_not_called()

    def test_skips_when_no_api_key(self):
        """API 키가 없으면 댓글을 게시하지 않는다."""
        state = self._make_state(wi_ids=["wi-uuid-001"])
        cfg = self._make_cfg(api_key="")

        with (
            patch("oh_my_kanban.hooks.post_tool.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.post_tool.create_plane_http_client") as mock_create,
        ):
            _post_commit_comment(state, "abc1234", "git commit -m '...'")

        mock_create.assert_not_called()

    def test_outputs_additional_context_on_success(self):
        """댓글 게시 후 Claude에게 additionalContext를 주입한다."""
        state = self._make_state(wi_ids=["wi-uuid-001"])
        cfg = self._make_cfg()
        mock_client, mock_cm = self._make_http_mock()

        with (
            patch("oh_my_kanban.hooks.post_tool.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.post_tool.create_plane_http_client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.post_tool.output_context") as mock_ctx,
        ):
            _post_commit_comment(state, "abc1234", "git commit -m '...'")

        mock_ctx.assert_called_once()
        assert "abc1234" in mock_ctx.call_args[0][1]

    def test_fail_open_on_http_exception(self):
        """HTTP 예외 시 fail-open으로 처리된다 (예외 전파 없음)."""
        state = self._make_state(wi_ids=["wi-uuid-001"])
        cfg = self._make_cfg()
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("서버 오류")
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with (
            patch("oh_my_kanban.hooks.post_tool.load_config", return_value=cfg),
            patch("oh_my_kanban.hooks.post_tool.create_plane_http_client", return_value=mock_cm),
            patch("oh_my_kanban.hooks.post_tool.output_context"),
        ):
            _post_commit_comment(state, "abc1234", "git commit -m '...'")  # 예외 없어야 함


# ── main() 통합 테스트 ────────────────────────────────────────────────────────


class TestPostToolMainGitCommit:
    def test_main_detects_git_commit_and_posts_comment(self):
        """main()에서 Bash+git commit을 감지하면 WI 댓글을 게시한다."""
        from oh_my_kanban.hooks.post_tool import main
        from oh_my_kanban.session.state import SessionState

        state = SessionState(session_id="sess-main-001")
        state.plane_context.work_item_ids = ["wi-uuid-001"]
        state.plane_context.project_id = "proj-uuid"

        hook_input = {
            "session_id": "sess-main-001",
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'feat: add login'"},
            "tool_response": "[master a1b2c3d] feat: add login\n 1 file changed",
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session"),
            patch("oh_my_kanban.hooks.post_tool._post_commit_comment") as mock_post,
        ):
            main()

        mock_post.assert_called_once()
        args = mock_post.call_args[0]
        assert args[1] == "a1b2c3d"  # commit hash

    def test_main_skips_commit_comment_when_no_wi(self):
        """WI가 없으면 커밋 댓글을 게시하지 않는다."""
        from oh_my_kanban.hooks.post_tool import main
        from oh_my_kanban.session.state import SessionState

        state = SessionState(session_id="sess-main-002")

        hook_input = {
            "session_id": "sess-main-002",
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'feat'"},
            "tool_response": "[master a1b2c3d] feat",
        }

        with (
            patch("oh_my_kanban.hooks.post_tool.read_hook_input", return_value=hook_input),
            patch("oh_my_kanban.hooks.post_tool.load_session", return_value=state),
            patch("oh_my_kanban.hooks.post_tool.save_session"),
            patch("oh_my_kanban.hooks.post_tool._post_commit_comment") as mock_post,
        ):
            main()

        mock_post.assert_not_called()
