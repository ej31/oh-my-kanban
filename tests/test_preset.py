"""US-006: Preset system 테스트.

프리셋 목록/로드/저장/적용 기능을 검증한다.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from oh_my_kanban.cli import cli
from oh_my_kanban.config import (
    BUILTIN_PRESETS,
    Preset,
    apply_preset,
    list_presets,
    load_preset,
    save_preset,
)


# ── BUILTIN_PRESETS ───────────────────────────────────────────────────────────


class TestBuiltinPresets:
    """빌트인 프리셋 검증."""

    def test_minimal_preset(self) -> None:
        p = BUILTIN_PRESETS["minimal"]
        assert p.task_mode == "flat"
        assert p.upload_level == "none"

    def test_standard_preset(self) -> None:
        p = BUILTIN_PRESETS["standard"]
        assert p.task_mode == "main-sub"
        assert p.upload_level == "metadata"

    def test_verbose_preset(self) -> None:
        p = BUILTIN_PRESETS["verbose"]
        assert p.task_mode == "main-sub"
        assert p.upload_level == "full"

    def test_three_builtin_presets(self) -> None:
        assert len(BUILTIN_PRESETS) == 3


# ── list_presets ──────────────────────────────────────────────────────────────


class TestListPresets:
    """list_presets 함수 테스트."""

    def test_list_returns_builtins(self, tmp_path: Path) -> None:
        """빌트인 프리셋이 목록에 포함되어야 한다."""
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            presets = list_presets()
            names = [p.name for p in presets]
            assert "minimal" in names
            assert "standard" in names
            assert "verbose" in names

    def test_list_includes_user_presets(self, tmp_path: Path) -> None:
        """사용자 프리셋 파일이 있으면 목록에 포함되어야 한다."""
        user_preset = tmp_path / "custom.toml"
        user_preset.write_text(
            '[preset]\nname = "custom"\ndescription = "사용자 정의"\ntask_mode = "flat"\n',
            encoding="utf-8",
        )
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            presets = list_presets()
            names = [p.name for p in presets]
            assert "custom" in names


# ── load_preset ───────────────────────────────────────────────────────────────


class TestLoadPreset:
    """load_preset 함수 테스트."""

    def test_load_builtin(self) -> None:
        """빌트인 프리셋을 이름으로 로드할 수 있어야 한다."""
        preset = load_preset("minimal")
        assert preset is not None
        assert preset.task_mode == "flat"

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """존재하지 않는 프리셋은 None을 반환해야 한다."""
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            assert load_preset("nonexistent") is None

    def test_load_user_preset(self, tmp_path: Path) -> None:
        """사용자 프리셋 파일을 로드할 수 있어야 한다."""
        user_preset = tmp_path / "my-preset.toml"
        user_preset.write_text(
            '[preset]\nname = "my-preset"\ntask_mode = "module-task-sub"\n'
            'upload_level = "full"\n',
            encoding="utf-8",
        )
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            preset = load_preset("my-preset")
            assert preset is not None
            assert preset.task_mode == "module-task-sub"
            assert preset.upload_level == "full"


# ── save_preset ───────────────────────────────────────────────────────────────


class TestSavePreset:
    """save_preset 함수 테스트."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """프리셋 저장 시 TOML 파일이 생성되어야 한다."""
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            preset = Preset(name="test-save", description="저장 테스트", task_mode="flat")
            save_preset(preset)
            assert (tmp_path / "test-save.toml").exists()

    def test_save_invalid_name_raises(self, tmp_path: Path) -> None:
        """유효하지 않은 프리셋 이름은 ValueError를 발생시켜야 한다."""
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            with pytest.raises(ValueError, match="허용되지 않는 문자"):
                save_preset(Preset(name="../../bad"))

    def test_saved_preset_can_be_loaded(self, tmp_path: Path) -> None:
        """저장한 프리셋을 다시 로드할 수 있어야 한다."""
        with patch("oh_my_kanban.config.PRESETS_DIR", tmp_path):
            original = Preset(
                name="roundtrip",
                description="왕복 테스트",
                task_mode="module-task-sub",
                upload_level="full",
                drift_sensitivity=0.8,
                drift_cooldown=5,
            )
            save_preset(original)
            loaded = load_preset("roundtrip")
            assert loaded is not None
            assert loaded.task_mode == original.task_mode
            assert loaded.upload_level == original.upload_level
            assert loaded.drift_sensitivity == pytest.approx(original.drift_sensitivity)
            assert loaded.drift_cooldown == original.drift_cooldown


# ── apply_preset ──────────────────────────────────────────────────────────────


class TestApplyPreset:
    """apply_preset 함수 테스트."""

    def test_apply_calls_save_config(self, tmp_path: Path) -> None:
        """apply_preset이 save_config를 올바른 값으로 호출해야 한다."""
        preset = Preset(name="test", task_mode="flat", upload_level="none")

        config_file = tmp_path / "config.toml"
        with (
            patch("oh_my_kanban.config.CONFIG_DIR", tmp_path),
            patch("oh_my_kanban.config.CONFIG_FILE", config_file),
        ):
            apply_preset(preset)
            # config.toml이 생성되었는지 확인
            assert config_file.exists()
            content = config_file.read_text(encoding="utf-8")
            assert "flat" in content
            assert "none" in content


# ── CLI 커맨드 통합 테스트 ────────────────────────────────────────────────────


class TestPresetCLI:
    """config preset CLI 커맨드 테스트."""

    def test_preset_list_command(self) -> None:
        """omk config preset list 명령이 정상 실행되어야 한다."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "preset", "list"])
        assert result.exit_code == 0
        assert "minimal" in result.output
        assert "standard" in result.output
        assert "verbose" in result.output

    def test_preset_export_builtin(self) -> None:
        """omk config preset export 명령이 TOML을 출력해야 한다."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "preset", "export", "minimal"])
        assert result.exit_code == 0
        assert "[preset]" in result.output
        assert "flat" in result.output

    def test_preset_export_nonexistent(self) -> None:
        """존재하지 않는 프리셋 export 시 에러가 나야 한다."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "preset", "export", "nope"])
        assert result.exit_code != 0
