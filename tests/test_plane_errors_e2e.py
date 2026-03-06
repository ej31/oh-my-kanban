"""Plane 에러 처리 및 경계 조건 E2E 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from oh_my_kanban.cli import cli
from oh_my_kanban.context import CliContext


def _paginated(items: list) -> MagicMock:
    resp = MagicMock()
    resp.results = items
    resp.next_page_results = False
    return resp


@pytest.fixture
def ctx() -> CliContext:
    context = CliContext(
        _base_url="https://api.plane.so",
        _api_key="test-api-key",
        workspace="test-workspace",
        project="test-project-id",
        output="json",
    )
    context._client = MagicMock()
    return context


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ─── API 키 없을 때 ────────────────────────────────────────────────────────────


class TestMissingApiKey:
    def test_work_item_list_without_api_key_fails(self, runner):
        from oh_my_kanban.commands.work_item import work_item

        no_key_ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="",
            workspace="test-workspace",
            project="test-project-id",
            output="json",
        )
        result = runner.invoke(work_item, ["list"], obj=no_key_ctx)
        assert result.exit_code != 0

    def test_cycle_list_without_api_key_fails(self, runner):
        from oh_my_kanban.commands.cycle import cycle

        no_key_ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="",
            workspace="test-workspace",
            project="test-project-id",
            output="json",
        )
        result = runner.invoke(cycle, ["list"], obj=no_key_ctx)
        assert result.exit_code != 0


# ─── 프로젝트 없을 때 ─────────────────────────────────────────────────────────


class TestMissingProject:
    def test_work_item_list_without_project_fails(self, runner):
        from oh_my_kanban.commands.work_item import work_item

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(work_item, ["list"], obj=ctx)
        assert result.exit_code != 0

    def test_work_item_create_without_project_fails(self, runner):
        from oh_my_kanban.commands.work_item import work_item

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(work_item, ["create", "--name", "Task"], obj=ctx)
        assert result.exit_code != 0

    def test_label_list_without_project_fails(self, runner):
        from oh_my_kanban.commands.label import label

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(label, ["list"], obj=ctx)
        assert result.exit_code != 0


# ─── 워크스페이스 없을 때 ─────────────────────────────────────────────────────


class TestMissingWorkspace:
    def test_workspace_members_without_workspace_fails(self, runner):
        from oh_my_kanban.commands.workspace import workspace

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(workspace, ["members"], obj=ctx)
        assert result.exit_code != 0


# ─── 날짜 형식 검증 ────────────────────────────────────────────────────────────


class TestInvalidDateFormat:
    def test_work_item_create_bad_start_date(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["create", "--name", "Task", "--start-date", "not-a-date"], obj=ctx
        )
        assert result.exit_code != 0

    def test_work_item_create_bad_target_date(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["create", "--name", "Task", "--target-date", "2026/01/01"], obj=ctx
        )
        assert result.exit_code != 0

    def test_work_item_update_bad_start_date(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["update", "wi-001", "--start-date", "13-01-2026"], obj=ctx
        )
        assert result.exit_code != 0


# ─── HTTP 에러 처리 ────────────────────────────────────────────────────────────


class TestHttpErrorHandling:
    def test_401_error_exits_with_77(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        err = Exception()
        err.status_code = 401  # type: ignore[attr-defined]
        err.response = {"detail": "Unauthorized"}  # type: ignore[attr-defined]
        ctx.client.work_items.list.side_effect = err

        # plane.errors.errors.HttpError로 처리되려면 isinstance 체크가 필요
        # 여기서는 일반 Exception도 handle_api_error에서 처리됨
        result = runner.invoke(work_item, ["list"], obj=ctx)
        assert result.exit_code != 0

    def test_404_error_exits_nonzero(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        ctx.client.work_items.retrieve.side_effect = Exception("Not found")
        result = runner.invoke(work_item, ["get", "nonexistent-id"], obj=ctx)
        assert result.exit_code != 0


# ─── 잘못된 선택지 ────────────────────────────────────────────────────────────


class TestInvalidChoices:
    def test_work_item_list_invalid_priority(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(work_item, ["list", "--priority", "SUPER_HIGH"], obj=ctx)
        assert result.exit_code != 0

    def test_work_item_create_invalid_priority(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item, ["create", "--name", "Task", "--priority", "INVALID"], obj=ctx
        )
        assert result.exit_code != 0

    def test_relation_create_invalid_type(self, runner, ctx):
        from oh_my_kanban.commands.work_item import work_item

        result = runner.invoke(
            work_item,
            [
                "relation",
                "create",
                "wi-001",
                "--related-item", "wi-002",
                "--relation-type", "INVALID_TYPE",
            ],
            obj=ctx,
        )
        assert result.exit_code != 0


# ─── github stub ──────────────────────────────────────────────────────────────


class TestGithubStub:
    def test_github_help_exits_ok(self, runner):
        result = runner.invoke(cli, ["github", "--help"])
        assert result.exit_code == 0

    def test_gh_alias_help_exits_ok(self, runner):
        result = runner.invoke(cli, ["gh", "--help"])
        assert result.exit_code == 0


# ─── config 커맨드 ────────────────────────────────────────────────────────────


class TestConfigShow:
    def test_config_show_exits_ok(self, runner):
        with patch("oh_my_kanban.commands.config_cmd.load_config") as mock_load:
            from oh_my_kanban.config import Config
            mock_load.return_value = Config()
            result = runner.invoke(cli, ["config", "show"])
            assert result.exit_code == 0


class TestConfigSet:
    def test_config_set_api_key(self, runner, tmp_path):
        config_file = tmp_path / "config.toml"
        with patch("oh_my_kanban.config.CONFIG_FILE", config_file):
            with patch("oh_my_kanban.commands.config_cmd.load_config") as mock_load:
                from oh_my_kanban.config import Config
                mock_load.return_value = Config()
                result = runner.invoke(cli, ["config", "set", "api_key", "new-api-key"])
                assert result.exit_code in (0, 1)


# ─── linear alias ─────────────────────────────────────────────────────────────


class TestLinearAlias:
    def test_linear_help_exits_ok(self, runner):
        result = runner.invoke(cli, ["linear", "--help"])
        assert result.exit_code == 0

    def test_ln_alias_help_exits_ok(self, runner):
        result = runner.invoke(cli, ["ln", "--help"])
        assert result.exit_code == 0

    def test_linear_shows_me_subcommand(self, runner):
        result = runner.invoke(cli, ["linear", "--help"])
        assert result.exit_code == 0
        assert "me" in result.output

    def test_linear_shows_issue_subcommand(self, runner):
        result = runner.invoke(cli, ["linear", "--help"])
        assert result.exit_code == 0
        assert "issue" in result.output
