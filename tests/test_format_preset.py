"""ST-25: Task Format Preset 시스템 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.session.state import SessionState


_MOD = "oh_my_kanban.hooks.session_start"


def _make_state_with_wi() -> SessionState:
    state = SessionState(session_id="sess-fmt-001")
    state.plane_context.work_item_ids = ["wi-uuid-001"]
    state.plane_context.project_id = "proj-uuid"
    state.scope.summary = "세션 목표"
    return state


def _make_cfg(format_preset: str = "normal"):
    cfg = MagicMock()
    cfg.api_key = "key"
    cfg.workspace_slug = "ws"
    cfg.project_id = "proj-uuid"
    cfg.base_url = "https://plane.example.com"
    cfg.drift_sensitivity = 0.5
    cfg.drift_cooldown = 3
    cfg.task_mode = "main-sub"
    cfg.format_preset = format_preset
    return cfg


class TestFormatPresetSessionStart:
    def test_eco_skips_session_start_comment(self):
        """format_preset=eco이면 세션 시작 Plane 댓글을 생략한다."""
        from oh_my_kanban.hooks.session_start import _post_session_start_comment

        state = _make_state_with_wi()
        cfg = _make_cfg(format_preset="eco")

        with patch("httpx.Client") as mock_httpx:
            _post_session_start_comment(state, cfg)

        mock_httpx.assert_not_called()

    def test_normal_posts_standard_comment(self):
        """format_preset=normal이면 표준 세션 시작 댓글을 게시한다."""
        from oh_my_kanban.hooks.session_start import _post_session_start_comment

        state = _make_state_with_wi()
        cfg = _make_cfg(format_preset="normal")

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        import httpx

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _post_session_start_comment(state, cfg)

        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        # normal: 기본 필드 포함
        assert "omk 세션 시작" in kwargs["json"]["comment_html"]
        # normal: 상세 필드 미포함
        assert "누적 요청 수" not in kwargs["json"]["comment_html"]

    def test_detailed_posts_verbose_comment(self):
        """format_preset=detailed이면 더 많은 정보를 포함하는 댓글을 게시한다."""
        from oh_my_kanban.hooks.session_start import _post_session_start_comment

        state = _make_state_with_wi()
        state.stats.total_prompts = 42
        state.stats.files_touched = ["src/app.py", "src/utils.py"]
        cfg = _make_cfg(format_preset="detailed")

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        import httpx

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.return_value = mock_resp
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_client)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_cm):
            _post_session_start_comment(state, cfg)

        mock_client.post.assert_called_once()
        _, kwargs = mock_client.post.call_args
        comment = kwargs["json"]["comment_html"]
        # detailed: 기본 필드 포함
        assert "omk 세션 시작" in comment
        # detailed: 상세 필드 포함
        assert "누적 요청 수" in comment


class TestFormatPresetConfig:
    def test_default_format_preset_is_normal(self):
        """format_preset의 기본값은 'normal'이다."""
        from oh_my_kanban.config import Config
        cfg = Config()
        assert cfg.format_preset == "normal"

    def test_toml_loads_format_preset(self, tmp_path):
        """TOML 파일에서 format_preset을 로드한다."""
        from pathlib import Path
        from unittest.mock import patch
        from oh_my_kanban.config import load_config

        config_file = tmp_path / "config.toml"
        config_file.write_text('[default]\nformat_preset = "eco"\n', encoding="utf-8")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.format_preset == "eco"

    def test_env_overrides_format_preset(self, monkeypatch, tmp_path):
        """환경변수 OMK_FORMAT_PRESET이 format_preset을 오버라이드한다."""
        from pathlib import Path
        from unittest.mock import patch
        from oh_my_kanban.config import load_config

        config_file = tmp_path / "config.toml"
        config_file.write_text('[default]\nformat_preset = "normal"\n', encoding="utf-8")
        monkeypatch.setenv("OMK_FORMAT_PRESET", "detailed")

        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            cfg = load_config()

        assert cfg.format_preset == "detailed"

    def test_allowed_config_keys_includes_format_preset(self):
        """_ALLOWED_CONFIG_KEYS에 format_preset이 포함되어야 한다."""
        from oh_my_kanban.config import _ALLOWED_CONFIG_KEYS
        assert "format_preset" in _ALLOWED_CONFIG_KEYS
