"""config.py drift_sensitivity/cooldown 설정 확장 테스트."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from oh_my_kanban.config import Config, load_config


def _write_config(tmp_path: Path, content: str) -> Path:
    """임시 설정 파일을 작성하고 경로를 반환한다."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def test_config_default_drift_sensitivity() -> None:
    """Config 기본값: drift_sensitivity는 0.5여야 한다."""
    cfg = Config()
    assert cfg.drift_sensitivity == 0.5


def test_config_default_drift_cooldown() -> None:
    """Config 기본값: drift_cooldown은 3이어야 한다."""
    cfg = Config()
    assert cfg.drift_cooldown == 3


def test_toml_drift_sensitivity_loaded(tmp_path: Path) -> None:
    """TOML에 drift_sensitivity가 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ndrift_sensitivity = 0.8\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_sensitivity == pytest.approx(0.8)


def test_toml_drift_cooldown_loaded(tmp_path: Path) -> None:
    """TOML에 drift_cooldown이 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ndrift_cooldown = 5\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_cooldown == 5


def test_env_overrides_drift_sensitivity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """환경변수 OMK_DRIFT_SENSITIVITY가 TOML의 drift_sensitivity 값을 오버라이드한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ndrift_sensitivity = 0.3\n',
    )
    monkeypatch.setenv("OMK_DRIFT_SENSITIVITY", "0.9")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_sensitivity == pytest.approx(0.9)


def test_env_overrides_drift_cooldown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """환경변수 OMK_DRIFT_COOLDOWN이 TOML의 drift_cooldown 값을 오버라이드한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ndrift_cooldown = 2\n',
    )
    monkeypatch.setenv("OMK_DRIFT_COOLDOWN", "10")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_cooldown == 10


def test_invalid_env_drift_sensitivity_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """잘못된 OMK_DRIFT_SENSITIVITY 값은 무시되고 기본값이 유지된다."""
    config_file = _write_config(tmp_path, '[default]\n')
    monkeypatch.setenv("OMK_DRIFT_SENSITIVITY", "not_a_float")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_sensitivity == pytest.approx(0.5)


def test_invalid_env_drift_cooldown_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """잘못된 OMK_DRIFT_COOLDOWN 값은 무시되고 기본값이 유지된다."""
    config_file = _write_config(tmp_path, '[default]\n')
    monkeypatch.setenv("OMK_DRIFT_COOLDOWN", "not_an_int")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.drift_cooldown == 3
