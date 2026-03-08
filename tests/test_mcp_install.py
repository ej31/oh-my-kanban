"""omk mcp install/uninstall 커맨드 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from oh_my_kanban.commands.mcp_cmd import (
    MCP_SERVER_CONFIG,
    MCP_SERVER_KEY,
    _install_mcp,
    _uninstall_mcp,
    install,
    uninstall,
)


class TestInstallMcp:
    """_install_mcp() 단위 테스트."""

    def test_새_파일에_mcpServers_등록(self, tmp_path: Path) -> None:
        """settings.json이 없으면 새로 생성하고 mcpServers를 등록한다."""
        settings_path = tmp_path / "settings.json"

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _install_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["mcpServers"][MCP_SERVER_KEY] == MCP_SERVER_CONFIG

    def test_기존_설정_보존하며_mcpServers_추가(self, tmp_path: Path) -> None:
        """기존 hooks 설정을 보존하면서 mcpServers를 추가한다."""
        settings_path = tmp_path / "settings.json"
        existing = {"hooks": {"SessionStart": []}, "other": "value"}
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _install_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        # 기존 설정 보존
        assert data["hooks"] == {"SessionStart": []}
        assert data["other"] == "value"
        # MCP 서버 추가
        assert data["mcpServers"][MCP_SERVER_KEY] == MCP_SERVER_CONFIG

    def test_기존_mcpServers_다른_항목_보존(self, tmp_path: Path) -> None:
        """기존 mcpServers의 다른 서버 설정을 보존한다."""
        settings_path = tmp_path / "settings.json"
        existing = {
            "mcpServers": {
                "other-server": {"command": "other", "args": ["serve"]},
            }
        }
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _install_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["mcpServers"]["other-server"] == {"command": "other", "args": ["serve"]}
        assert data["mcpServers"][MCP_SERVER_KEY] == MCP_SERVER_CONFIG

    def test_idempotent_재실행_동일_결과(self, tmp_path: Path) -> None:
        """이미 등록된 상태에서 다시 실행해도 동일한 결과를 유지한다."""
        settings_path = tmp_path / "settings.json"

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _install_mcp(local=False)
            _install_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["mcpServers"][MCP_SERVER_KEY] == MCP_SERVER_CONFIG

    def test_잘못된_json_파일_ClickException(self, tmp_path: Path) -> None:
        """settings.json이 유효하지 않은 JSON이면 ClickException을 발생시킨다."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{invalid json", encoding="utf-8")

        with (
            patch(
                "oh_my_kanban.commands.hooks._settings_path",
                return_value=settings_path,
            ),
            pytest.raises(click.ClickException, match="파싱 실패"),
        ):
            _install_mcp(local=False)


class TestUninstallMcp:
    """_uninstall_mcp() 단위 테스트."""

    def test_등록된_MCP_서버_제거(self, tmp_path: Path) -> None:
        """등록된 oh-my-kanban MCP 서버를 제거한다."""
        settings_path = tmp_path / "settings.json"
        existing = {
            "hooks": {"SessionStart": []},
            "mcpServers": {
                MCP_SERVER_KEY: MCP_SERVER_CONFIG,
                "other-server": {"command": "other"},
            },
        }
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _uninstall_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert MCP_SERVER_KEY not in data["mcpServers"]
        # 다른 서버는 보존
        assert data["mcpServers"]["other-server"] == {"command": "other"}
        # hooks도 보존
        assert data["hooks"] == {"SessionStart": []}

    def test_유일한_MCP_서버_제거시_mcpServers_키_삭제(self, tmp_path: Path) -> None:
        """oh-my-kanban이 유일한 MCP 서버면 mcpServers 키 자체를 삭제한다."""
        settings_path = tmp_path / "settings.json"
        existing = {"mcpServers": {MCP_SERVER_KEY: MCP_SERVER_CONFIG}}
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _uninstall_mcp(local=False)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "mcpServers" not in data

    def test_등록_안된_상태에서_uninstall_안전(self, tmp_path: Path) -> None:
        """oh-my-kanban이 등록되지 않은 상태에서 uninstall해도 에러 없이 진행된다."""
        settings_path = tmp_path / "settings.json"
        existing = {"mcpServers": {"other": {"command": "x"}}}
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            _uninstall_mcp(local=False)

        # 파일 내용 변경 없음
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data == existing

    def test_settings_파일_없으면_안전하게_종료(self, tmp_path: Path) -> None:
        """settings.json이 없으면 에러 없이 종료한다."""
        settings_path = tmp_path / "nonexistent" / "settings.json"

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ):
            # 예외 없이 정상 종료
            _uninstall_mcp(local=False)

    def test_잘못된_json_파일_uninstall_ClickException(self, tmp_path: Path) -> None:
        """uninstall 시 settings.json이 유효하지 않은 JSON이면 ClickException을 발생시킨다."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("{invalid json", encoding="utf-8")

        with (
            patch(
                "oh_my_kanban.commands.hooks._settings_path",
                return_value=settings_path,
            ),
            pytest.raises(click.ClickException, match="파싱 실패"),
        ):
            _uninstall_mcp(local=False)


class TestFlagForwarding:
    """local/local_only 플래그 전달 검증."""

    @pytest.mark.parametrize(
        ("local", "local_only", "expected_local", "expected_local_only"),
        [
            (False, False, False, False),
            (True, False, True, False),
            (False, True, False, True),
        ],
        ids=["user-scope", "project-scope", "local-scope"],
    )
    def test_install_플래그_전달(
        self,
        tmp_path: Path,
        local: bool,
        local_only: bool,
        expected_local: bool,
        expected_local_only: bool,
    ) -> None:
        """_install_mcp에 local/local_only 플래그가 올바르게 전달된다."""
        settings_path = tmp_path / "settings.json"

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ) as mock_path:
            _install_mcp(local=local, local_only=local_only)
            mock_path.assert_called_once_with(expected_local, expected_local_only)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["mcpServers"][MCP_SERVER_KEY] == MCP_SERVER_CONFIG

    @pytest.mark.parametrize(
        ("local", "local_only"),
        [
            (False, False),
            (True, False),
            (False, True),
        ],
        ids=["user-scope", "project-scope", "local-scope"],
    )
    def test_uninstall_플래그_전달(
        self,
        tmp_path: Path,
        local: bool,
        local_only: bool,
    ) -> None:
        """_uninstall_mcp에 local/local_only 플래그가 올바르게 전달된다."""
        settings_path = tmp_path / "settings.json"
        existing = {"mcpServers": {MCP_SERVER_KEY: MCP_SERVER_CONFIG}}
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch(
            "oh_my_kanban.commands.hooks._settings_path",
            return_value=settings_path,
        ) as mock_path:
            _uninstall_mcp(local=local, local_only=local_only)
            mock_path.assert_called_once_with(local, local_only)


class TestMutualExclusion:
    """--local과 --local-only 상호 배타 검증."""

    def test_install_둘_다_지정시_UsageError(self) -> None:
        """install에서 --local과 --local-only를 동시에 지정하면 UsageError."""
        ctx = click.Context(install)
        with pytest.raises(click.UsageError, match="동시에 사용할 수 없습니다"):
            ctx.invoke(install, local=True, local_only=True)

    def test_uninstall_둘_다_지정시_UsageError(self) -> None:
        """uninstall에서 --local과 --local-only를 동시에 지정하면 UsageError."""
        ctx = click.Context(uninstall)
        with pytest.raises(click.UsageError, match="동시에 사용할 수 없습니다"):
            ctx.invoke(uninstall, local=True, local_only=True)
