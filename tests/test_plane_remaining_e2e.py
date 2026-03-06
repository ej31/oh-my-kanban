"""Plane module / milestone / epic / user / workspace E2E 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

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


# ─── module ───────────────────────────────────────────────────────────────────


class TestModuleList:
    def test_list_returns_modules(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        mod = MagicMock()
        mod.id = "mod-001"
        mod.name = "Backend Module"
        ctx.client.modules.list.return_value = _paginated([mod])
        result = runner.invoke(module, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.modules.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.list.return_value = _paginated([])
        result = runner.invoke(module, ["list"], obj=ctx)
        assert result.exit_code == 0

    def test_list_without_project_fails(self, runner):
        from oh_my_kanban.commands.module import module

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(module, ["list"], obj=ctx)
        assert result.exit_code != 0


class TestModuleGet:
    def test_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        mod = MagicMock()
        mod.id = "mod-001"
        ctx.client.modules.retrieve.return_value = mod
        result = runner.invoke(module, ["get", "mod-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.modules.retrieve.assert_called_once()


class TestModuleCreate:
    def test_create_minimal(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.create.return_value = MagicMock()
        result = runner.invoke(module, ["create", "--name", "New Module"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.modules.create.assert_called_once()

    def test_create_without_name_fails(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        result = runner.invoke(module, ["create"], obj=ctx)
        assert result.exit_code != 0


class TestModuleUpdate:
    def test_update_name(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.update.return_value = MagicMock()
        result = runner.invoke(
            module, ["update", "mod-001", "--name", "Updated Module"], obj=ctx
        )
        assert result.exit_code == 0, result.output


class TestModuleDelete:
    def test_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.delete.return_value = None
        result = runner.invoke(module, ["delete", "mod-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        result = runner.invoke(module, ["delete", "mod-001"], obj=ctx, input="n\n")
        # confirm 거부 시 return으로 종료 (exit_code 0)
        assert result.exit_code == 0
        ctx.client.modules.delete.assert_not_called()


class TestModuleItems:
    def test_items_returns_list(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        item = MagicMock()
        ctx.client.modules.list_work_items.return_value = _paginated([item])
        result = runner.invoke(module, ["items", "mod-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_add_items(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.add_work_items.return_value = MagicMock()
        result = runner.invoke(
            module, ["add-items", "mod-001", "--items", "wi-001"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_remove_item(self, runner, ctx):
        from oh_my_kanban.commands.module import module

        ctx.client.modules.remove_work_item.return_value = None
        result = runner.invoke(module, ["remove-item", "mod-001", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output


# ─── milestone ────────────────────────────────────────────────────────────────


class TestMilestoneList:
    def test_list_returns_milestones(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ms = MagicMock()
        ms.id = "ms-001"
        ms.name = "v1.0"
        ctx.client.milestones.list.return_value = _paginated([ms])
        result = runner.invoke(milestone, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.milestones.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ctx.client.milestones.list.return_value = _paginated([])
        result = runner.invoke(milestone, ["list"], obj=ctx)
        assert result.exit_code == 0


class TestMilestoneGet:
    def test_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ms = MagicMock()
        ms.id = "ms-001"
        ctx.client.milestones.retrieve.return_value = ms
        result = runner.invoke(milestone, ["get", "ms-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.milestones.retrieve.assert_called_once()


class TestMilestoneCreate:
    def test_create_minimal(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ctx.client.milestones.create.return_value = MagicMock()
        result = runner.invoke(milestone, ["create", "--title", "v1.0 Release"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.milestones.create.assert_called_once()

    def test_create_without_title_fails(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        result = runner.invoke(milestone, ["create"], obj=ctx)
        assert result.exit_code != 0


class TestMilestoneUpdate:
    def test_update_title(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ctx.client.milestones.update.return_value = MagicMock()
        result = runner.invoke(
            milestone, ["update", "ms-001", "--title", "v2.0 Release"], obj=ctx
        )
        assert result.exit_code == 0, result.output


class TestMilestoneDelete:
    def test_delete_confirmed(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        ctx.client.milestones.delete.return_value = None
        result = runner.invoke(milestone, ["delete", "ms-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        from oh_my_kanban.commands.milestone import milestone

        result = runner.invoke(milestone, ["delete", "ms-001"], obj=ctx, input="n\n")
        # confirm 거부 시 return으로 종료 (exit_code 0)
        assert result.exit_code == 0
        ctx.client.milestones.delete.assert_not_called()


# ─── epic ─────────────────────────────────────────────────────────────────────


class TestEpicList:
    def test_list_returns_epics(self, runner, ctx):
        from oh_my_kanban.commands.epic import epic

        ep = MagicMock()
        ep.id = "ep-001"
        ep.name = "User Auth Epic"
        ctx.client.epics.list.return_value = _paginated([ep])
        result = runner.invoke(epic, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.epics.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.commands.epic import epic

        ctx.client.epics.list.return_value = _paginated([])
        result = runner.invoke(epic, ["list"], obj=ctx)
        assert result.exit_code == 0

    def test_list_without_project_fails(self, runner):
        from oh_my_kanban.commands.epic import epic

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="test-api-key",
            workspace="test-workspace",
            project="",
            output="json",
        )
        ctx._client = MagicMock()
        result = runner.invoke(epic, ["list"], obj=ctx)
        assert result.exit_code != 0


class TestEpicGet:
    def test_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.epic import epic

        ep = MagicMock()
        ep.id = "ep-001"
        ctx.client.epics.retrieve.return_value = ep
        result = runner.invoke(epic, ["get", "ep-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.epics.retrieve.assert_called_once()


# ─── user ─────────────────────────────────────────────────────────────────────


class TestUserMe:
    def test_user_me_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.user import user

        me = MagicMock()
        me.id = "user-001"
        me.display_name = "Test User"
        ctx.client.users.get_me.return_value = me
        result = runner.invoke(user, ["me"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.users.get_me.assert_called_once()

    def test_user_me_without_api_key_fails(self, runner):
        from oh_my_kanban.commands.user import user

        ctx = CliContext(
            _base_url="https://api.plane.so",
            _api_key="",
            workspace="test-workspace",
            project="",
            output="json",
        )
        result = runner.invoke(user, ["me"], obj=ctx)
        assert result.exit_code != 0


# ─── workspace ────────────────────────────────────────────────────────────────


class TestWorkspaceMembers:
    def test_members_returns_list(self, runner, ctx):
        from oh_my_kanban.commands.workspace import workspace

        ctx.client.workspaces.get_members.return_value = [MagicMock(id="mem-001")]
        result = runner.invoke(workspace, ["members"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.workspaces.get_members.assert_called_once()

    def test_members_without_workspace_fails(self, runner):
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


class TestWorkspaceFeatures:
    def test_features_returns_detail(self, runner, ctx):
        from oh_my_kanban.commands.workspace import workspace

        ctx.client.workspaces.get_features.return_value = MagicMock()
        result = runner.invoke(workspace, ["features"], obj=ctx)
        assert result.exit_code == 0, result.output


# ─── 통합 CLI 경로 ──────────────────────────────────────────────────────────


class TestFullCliIntegration:
    """전체 CLI 그룹 구조 통합 검증 (--help 기반)."""

    def test_plane_work_item_list_help_via_cli(self, runner):
        """plane work-item list --help가 통합 CLI 경로로 정상 동작한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["plane", "work-item", "list", "--help"])
        assert result.exit_code == 0, result.output

    def test_plane_cycle_list_help_via_cli(self, runner):
        """plane cycle list --help가 통합 CLI 경로로 정상 동작한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["plane", "cycle", "list", "--help"])
        assert result.exit_code == 0, result.output

    def test_plane_module_list_help_via_cli(self, runner):
        """plane module list --help가 통합 CLI 경로로 정상 동작한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["plane", "module", "list", "--help"])
        assert result.exit_code == 0, result.output

    def test_pl_alias_help_works(self, runner):
        """pl alias가 plane 그룹과 동일하게 --help로 동작한다."""
        from oh_my_kanban.cli import cli

        result = runner.invoke(cli, ["pl", "work-item", "--help"])
        assert result.exit_code == 0, result.output
