"""Linear 필드 TOML 읽기 테스트."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from oh_my_kanban.config import load_config


def _write_config(tmp_path: Path, content: str) -> Path:
    """임시 설정 파일을 작성하고 경로를 반환한다."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def test_toml_linear_api_key_loaded(tmp_path: Path) -> None:
    """TOML에 linear_api_key가 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\nlinear_api_key = "lin_api_toml_value"\nlinear_team_id = "team_toml_id"\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.linear_api_key == "lin_api_toml_value"
    assert cfg.linear_team_id == "team_toml_id"


def test_env_overrides_toml_linear_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """환경변수 LINEAR_API_KEY가 TOML의 linear_api_key 값을 오버라이드한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\nlinear_api_key = "lin_api_toml_value"\n',
    )
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_env_value")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.linear_api_key == "lin_api_env_value"
