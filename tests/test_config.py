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


# ── ST-12: WI 워크플로우 설정 필드 테스트 ──────────────────────────────────────


def test_config_default_task_mode() -> None:
    """Config 기본값: task_mode는 'main-sub'여야 한다."""
    cfg = Config()
    assert cfg.task_mode == "main-sub"


def test_config_default_upload_level() -> None:
    """Config 기본값: upload_level은 'metadata'여야 한다."""
    cfg = Config()
    assert cfg.upload_level == "metadata"


def test_config_default_auto_archive_days() -> None:
    """Config 기본값: auto_archive_days는 7이어야 한다."""
    cfg = Config()
    assert cfg.auto_archive_days == 7


def test_config_default_auto_complete_subtasks() -> None:
    """Config 기본값: auto_complete_subtasks는 True여야 한다."""
    cfg = Config()
    assert cfg.auto_complete_subtasks is True


def test_config_default_session_retention_days() -> None:
    """Config 기본값: session_retention_days는 30이어야 한다."""
    cfg = Config()
    assert cfg.session_retention_days == 30


def test_toml_task_mode_loaded(tmp_path: Path) -> None:
    """TOML에 task_mode가 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ntask_mode = "module-task-sub"\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.task_mode == "module-task-sub"


def test_toml_upload_level_loaded(tmp_path: Path) -> None:
    """TOML에 upload_level이 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\nupload_level = "full"\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.upload_level == "full"


def test_toml_auto_archive_days_loaded(tmp_path: Path) -> None:
    """TOML에 auto_archive_days가 있을 때 load_config()가 해당 값을 반환한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\nauto_archive_days = 14\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.auto_archive_days == 14


def test_toml_session_retention_days_minimum(tmp_path: Path) -> None:
    """session_retention_days 최솟값은 1이어야 한다 (0 입력 시 1로 보정)."""
    config_file = _write_config(
        tmp_path,
        '[default]\nsession_retention_days = 0\n',
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.session_retention_days == 1


def test_env_overrides_task_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """환경변수 OMK_TASK_MODE가 TOML의 task_mode 값을 오버라이드한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\ntask_mode = "main-sub"\n',
    )
    monkeypatch.setenv("OMK_TASK_MODE", "module-task-sub")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.task_mode == "module-task-sub"


def test_env_overrides_upload_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """환경변수 OMK_UPLOAD_LEVEL이 TOML의 upload_level 값을 오버라이드한다."""
    config_file = _write_config(
        tmp_path,
        '[default]\nupload_level = "metadata"\n',
    )
    monkeypatch.setenv("OMK_UPLOAD_LEVEL", "full")

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.upload_level == "full"


def test_allowed_config_keys_includes_workflow_fields() -> None:
    """ALLOWED_CONFIG_KEYS에 워크플로우 설정 키가 포함되어 있어야 한다."""
    from oh_my_kanban.config import ALLOWED_CONFIG_KEYS

    assert "task_mode" in ALLOWED_CONFIG_KEYS
    assert "upload_level" in ALLOWED_CONFIG_KEYS
    assert "auto_archive_days" in ALLOWED_CONFIG_KEYS
    assert "auto_complete_subtasks" in ALLOWED_CONFIG_KEYS
    assert "session_retention_days" in ALLOWED_CONFIG_KEYS


def test_toml_auto_complete_subtasks_native_bool_loaded(tmp_path: Path) -> None:
    """TOML bool 스칼라가 auto_complete_subtasks에 반영되어야 한다."""
    config_file = _write_config(
        tmp_path,
        "[default]\nauto_complete_subtasks = true\n",
    )

    with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
        cfg = load_config()

    assert cfg.auto_complete_subtasks is True
