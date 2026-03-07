"""omk hooks install의 플러그인 파일 복사 기능 테스트."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.commands.hooks import _install_plugin_files


class TestInstallPluginFiles:
    """_install_plugin_files() 단위 테스트."""

    def test_plugin_data_dir_not_exists_warns_and_returns(self, tmp_path: Path) -> None:
        """plugin_data_dir이 없으면 경고 출력 후 반환 (fail-open)."""
        # 가짜 패키지 구조 생성 (plugin_data 없음)
        (tmp_path / "oh_my_kanban").mkdir(parents=True, exist_ok=True)
        (tmp_path / "oh_my_kanban" / "__init__.py").write_text("")
        fake_init = str(tmp_path / "oh_my_kanban" / "__init__.py")

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=tmp_path / "home",
            ),
            patch(
                "importlib.metadata.version",
                return_value="0.1.0",
            ),
            patch(
                "oh_my_kanban.commands.hooks.shutil",
            ) as mock_shutil,
            patch(
                "oh_my_kanban.commands.hooks.click",
            ) as mock_click,
        ):
            # oh_my_kanban 패키지의 __file__을 모킹
            fake_module = MagicMock()
            fake_module.__file__ = fake_init

            with patch.dict("sys.modules", {"oh_my_kanban": fake_module}):
                _install_plugin_files()

            # plugin_data가 없으므로 경고가 출력되어야 함
            mock_click.echo.assert_called_once()
            assert "경고" in mock_click.echo.call_args[0][0]
            # copytree는 호출되지 않아야 함
            mock_shutil.copytree.assert_not_called()

    def test_copies_plugin_data_to_cache_dir(self, tmp_path: Path) -> None:
        """plugin_data_dir 존재 시 캐시 디렉토리에 복사됨."""
        # 가짜 패키지 구조 생성
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "test.txt").write_text("hello")

        home_dir = tmp_path / "home"

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                return_value="1.2.3",
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            _install_plugin_files()

        # 캐시 디렉토리에 파일이 복사되었는지 확인
        cache_dir = home_dir / ".claude" / "plugins" / "cache" / "omk" / "oh-my-kanban" / "1.2.3"
        assert cache_dir.exists()
        assert (cache_dir / "test.txt").read_text() == "hello"

    def test_idempotent_overwrites_existing(self, tmp_path: Path) -> None:
        """이미 캐시 디렉토리가 존재하면 제거 후 재복사 (idempotent)."""
        # 가짜 패키지 구조
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "new.txt").write_text("new content")

        home_dir = tmp_path / "home"
        cache_dir = home_dir / ".claude" / "plugins" / "cache" / "omk" / "oh-my-kanban" / "1.0.0"
        cache_dir.mkdir(parents=True)
        (cache_dir / "old.txt").write_text("old content")

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                return_value="1.0.0",
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            _install_plugin_files()

        # 이전 파일은 삭제되고 새 파일만 존재해야 함
        assert not (cache_dir / "old.txt").exists()
        assert (cache_dir / "new.txt").read_text() == "new content"

    def test_version_from_importlib_metadata(self, tmp_path: Path) -> None:
        """버전이 importlib.metadata에서 올바르게 읽힘."""
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "f.txt").write_text("x")

        home_dir = tmp_path / "home"

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                return_value="99.88.77",
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            _install_plugin_files()

        cache_dir = home_dir / ".claude" / "plugins" / "cache" / "omk" / "oh-my-kanban" / "99.88.77"
        assert cache_dir.exists()

    def test_version_fallback_on_error(self, tmp_path: Path) -> None:
        """버전 조회 실패 시 'unknown'으로 폴백."""
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "f.txt").write_text("x")

        home_dir = tmp_path / "home"

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                side_effect=PackageNotFoundError("oh-my-kanban"),
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            _install_plugin_files()

        cache_dir = home_dir / ".claude" / "plugins" / "cache" / "omk" / "oh-my-kanban" / "unknown"
        assert cache_dir.exists()

    def test_version_sanitization_path_traversal(self, tmp_path: Path) -> None:
        """악의적인 버전 문자열(경로 순회 시도)은 'unknown'으로 대체된다."""
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "f.txt").write_text("x")

        home_dir = tmp_path / "home"

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                return_value="../../../evil",  # 경로 순회 시도
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            _install_plugin_files()

        # 'unknown' 디렉토리에 복사되어야 하며, 상위 디렉토리 탈출 없음
        expected = home_dir / ".claude" / "plugins" / "cache" / "omk" / "oh-my-kanban" / "unknown"
        assert expected.exists(), "무효한 버전은 'unknown' 디렉토리에 복사되어야 함"
        # 경로 순회 없음: evil 디렉토리가 생성되지 않아야 함
        assert not (tmp_path / "evil").exists()

    def test_copy_failure_fail_open(self, tmp_path: Path) -> None:
        """복사 실패 시 예외가 아닌 경고만 출력 (fail-open)."""
        pkg_dir = tmp_path / "oh_my_kanban"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("")

        plugin_data = pkg_dir / "plugin_data"
        plugin_data.mkdir()
        (plugin_data / "f.txt").write_text("x")

        home_dir = tmp_path / "home"

        fake_module = MagicMock()
        fake_module.__file__ = str(init_file)

        with (
            patch(
                "oh_my_kanban.commands.hooks.Path.home",
                return_value=home_dir,
            ),
            patch(
                "importlib.metadata.version",
                return_value="1.0.0",
            ),
            patch(
                "oh_my_kanban.commands.hooks.shutil.copytree",
                side_effect=OSError("permission denied"),
            ),
            patch.dict("sys.modules", {"oh_my_kanban": fake_module}),
        ):
            # 예외가 발생하지 않아야 함 (fail-open)
            _install_plugin_files()

    def test_install_hooks_calls_install_plugin_files(self) -> None:
        """_install_hooks() 실행 시 _install_plugin_files() 호출됨."""
        with (
            patch(
                "oh_my_kanban.commands.hooks._install_plugin_files",
            ) as mock_plugin,
            patch(
                "oh_my_kanban.commands.hooks._write_settings_atomic",
            ),
            patch(
                "oh_my_kanban.commands.hooks._settings_path",
                return_value=Path("/nonexistent/settings.json"),
            ),
            patch(
                "oh_my_kanban.commands.hooks._build_omk_hooks_config",
                return_value={},
            ),
            patch(
                "oh_my_kanban.commands.hooks._merge_hooks",
                return_value={},
            ),
            patch("oh_my_kanban.commands.hooks.click"),
            patch("oh_my_kanban.commands.hooks.sys") as mock_sys,
            patch("oh_my_kanban.hooks", create=True) as mock_hooks_pkg,
        ):
            mock_sys.executable = "/usr/bin/python"
            mock_hooks_pkg.__file__ = "/fake/hooks/__init__.py"

            from oh_my_kanban.commands.hooks import _install_hooks

            _install_hooks(local=False)

            mock_plugin.assert_called_once()
