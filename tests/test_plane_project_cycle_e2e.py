"""Plane project / cycle / state / label E2E 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

from helpers import paginated as _paginated

from oh_my_kanban.commands.cycle import cycle
from oh_my_kanban.commands.label import label
from oh_my_kanban.commands.project import project
from oh_my_kanban.commands.state import state

# ─── project ──────────────────────────────────────────────────────────────────


class TestProjectList:
    def test_list_returns_projects(self, runner, ctx):
        proj = MagicMock()
        proj.id = "proj-001"
        proj.name = "My Project"
        ctx.client.projects.list.return_value = _paginated([proj])
        result = runner.invoke(project, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.projects.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        ctx.client.projects.list.return_value = _paginated([])
        result = runner.invoke(project, ["list"], obj=ctx)
        assert result.exit_code == 0

    def test_list_with_per_page(self, runner, ctx):
        ctx.client.projects.list.return_value = _paginated([])
        result = runner.invoke(project, ["list", "--per-page", "10"], obj=ctx)
        assert result.exit_code == 0


class TestProjectGet:
    def test_get_returns_detail(self, runner, ctx):
        proj = MagicMock()
        proj.id = "proj-001"
        ctx.client.projects.retrieve.return_value = proj
        result = runner.invoke(project, ["get", "proj-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.projects.retrieve.assert_called_once()


class TestProjectCreate:
    def test_create_minimal(self, runner, ctx):
        ctx.client.projects.create.return_value = MagicMock()
        result = runner.invoke(
            project, ["create", "--name", "New Project", "--identifier", "NP"], obj=ctx
        )
        assert result.exit_code == 0, result.output
        ctx.client.projects.create.assert_called_once()

    def test_create_without_name_fails(self, runner, ctx):
        result = runner.invoke(project, ["create", "--identifier", "NP"], obj=ctx)
        assert result.exit_code != 0


class TestProjectUpdate:
    def test_update_name(self, runner, ctx):
        ctx.client.projects.update.return_value = MagicMock()
        result = runner.invoke(
            project, ["update", "proj-001", "--name", "Updated Name"], obj=ctx
        )
        assert result.exit_code == 0, result.output
        ctx.client.projects.update.assert_called_once()


class TestProjectDelete:
    def test_delete_confirmed(self, runner, ctx):
        ctx.client.projects.delete.return_value = None
        result = runner.invoke(project, ["delete", "proj-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        result = runner.invoke(project, ["delete", "proj-001"], obj=ctx, input="n\n")
        assert result.exit_code != 0
        ctx.client.projects.delete.assert_not_called()


class TestProjectMembers:
    def test_members_returns_list(self, runner, ctx):
        ctx.client.projects.get_members.return_value = [MagicMock()]
        result = runner.invoke(project, ["members", "proj-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.projects.get_members.assert_called_once()


class TestProjectFeatures:
    def test_features_returns_detail(self, runner, ctx):
        ctx.client.projects.get_features.return_value = MagicMock()
        result = runner.invoke(project, ["features", "proj-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.projects.get_features.assert_called_once()


# ─── cycle ────────────────────────────────────────────────────────────────────


class TestCycleList:
    def test_list_returns_cycles(self, runner, ctx):
        cyc = MagicMock()
        cyc.id = "cyc-001"
        cyc.name = "Sprint 1"
        ctx.client.cycles.list.return_value = _paginated([cyc])
        result = runner.invoke(cycle, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.cycles.list.assert_called_once()

    def test_list_empty_returns_ok(self, runner, ctx):
        ctx.client.cycles.list.return_value = _paginated([])
        result = runner.invoke(cycle, ["list"], obj=ctx)
        assert result.exit_code == 0

    def test_list_without_project_fails(self, runner, no_project_ctx):
        result = runner.invoke(cycle, ["list"], obj=no_project_ctx)
        assert result.exit_code != 0


class TestCycleGet:
    def test_get_returns_detail(self, runner, ctx):
        cyc = MagicMock()
        cyc.id = "cyc-001"
        ctx.client.cycles.retrieve.return_value = cyc
        result = runner.invoke(cycle, ["get", "cyc-001"], obj=ctx)
        assert result.exit_code == 0, result.output
        ctx.client.cycles.retrieve.assert_called_once()


class TestCycleCreate:
    def test_create_with_dates(self, runner, ctx):
        ctx.client.cycles.create.return_value = MagicMock()
        ctx.client.users.get_me.return_value.id = "user-id-123"
        result = runner.invoke(
            cycle,
            [
                "create",
                "--name", "Sprint 1",
                "--start-date", "2026-01-01",
                "--end-date", "2026-01-14",
            ],
            obj=ctx,
        )
        assert result.exit_code == 0, result.output
        ctx.client.cycles.create.assert_called_once()

    def test_create_without_name_fails(self, runner, ctx):
        result = runner.invoke(cycle, ["create"], obj=ctx)
        assert result.exit_code != 0


class TestCycleUpdate:
    def test_update_name(self, runner, ctx):
        ctx.client.cycles.update.return_value = MagicMock()
        result = runner.invoke(
            cycle, ["update", "cyc-001", "--name", "Updated Sprint"], obj=ctx
        )
        assert result.exit_code == 0, result.output


class TestCycleDelete:
    def test_delete_confirmed(self, runner, ctx):
        ctx.client.cycles.delete.return_value = None
        result = runner.invoke(cycle, ["delete", "cyc-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        result = runner.invoke(cycle, ["delete", "cyc-001"], obj=ctx, input="n\n")
        assert result.exit_code != 0
        ctx.client.cycles.delete.assert_not_called()


class TestCycleWorkItems:
    def test_items_returns_list(self, runner, ctx):
        ctx.client.cycles.list_work_items.return_value = _paginated([MagicMock()])
        result = runner.invoke(cycle, ["items", "cyc-001"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_add_items(self, runner, ctx):
        ctx.client.cycles.add_work_items.return_value = MagicMock()
        result = runner.invoke(
            cycle, ["add-items", "cyc-001", "--items", "wi-001", "--items", "wi-002"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_remove_item(self, runner, ctx):
        ctx.client.cycles.remove_work_item.return_value = None
        result = runner.invoke(cycle, ["remove-item", "cyc-001", "wi-001"], obj=ctx)
        assert result.exit_code == 0, result.output


# ─── state ────────────────────────────────────────────────────────────────────


class TestStateList:
    def test_list_returns_states(self, runner, ctx):
        st = MagicMock()
        st.id = "st-001"
        st.name = "Todo"
        ctx.client.states.list.return_value = _paginated([st])
        result = runner.invoke(state, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_list_empty_returns_ok(self, runner, ctx):
        ctx.client.states.list.return_value = _paginated([])
        result = runner.invoke(state, ["list"], obj=ctx)
        assert result.exit_code == 0


class TestStateCreate:
    def test_create_state(self, runner, ctx):
        ctx.client.states.create.return_value = MagicMock()
        result = runner.invoke(
            state, ["create", "--name", "In Review", "--color", "#abcdef"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_create_without_name_fails(self, runner, ctx):
        result = runner.invoke(state, ["create"], obj=ctx)
        assert result.exit_code != 0


class TestStateUpdate:
    def test_update_state(self, runner, ctx):
        ctx.client.states.update.return_value = MagicMock()
        result = runner.invoke(state, ["update", "st-001", "--name", "Done"], obj=ctx)
        assert result.exit_code == 0, result.output


class TestStateDelete:
    def test_delete_confirmed(self, runner, ctx):
        ctx.client.states.delete.return_value = None
        result = runner.invoke(state, ["delete", "st-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        result = runner.invoke(state, ["delete", "st-001"], obj=ctx, input="n\n")
        # state delete는 confirm 거부 시 return으로 종료 (exit_code 0)
        assert result.exit_code == 0
        ctx.client.states.delete.assert_not_called()


# ─── label ────────────────────────────────────────────────────────────────────


class TestLabelList:
    def test_list_returns_labels(self, runner, ctx):
        lbl = MagicMock()
        lbl.id = "lbl-001"
        lbl.name = "Bug"
        ctx.client.labels.list.return_value = _paginated([lbl])
        result = runner.invoke(label, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output

    def test_list_empty_returns_ok(self, runner, ctx):
        ctx.client.labels.list.return_value = _paginated([])
        result = runner.invoke(label, ["list"], obj=ctx)
        assert result.exit_code == 0


class TestLabelCreate:
    def test_create_label(self, runner, ctx):
        ctx.client.labels.create.return_value = MagicMock()
        result = runner.invoke(
            label, ["create", "--name", "Enhancement", "--color", "#00ff00"], obj=ctx
        )
        assert result.exit_code == 0, result.output

    def test_create_without_name_fails(self, runner, ctx):
        result = runner.invoke(label, ["create"], obj=ctx)
        assert result.exit_code != 0


class TestLabelUpdate:
    def test_update_label(self, runner, ctx):
        ctx.client.labels.update.return_value = MagicMock()
        result = runner.invoke(
            label, ["update", "lbl-001", "--name", "Critical Bug"], obj=ctx
        )
        assert result.exit_code == 0, result.output


class TestLabelDelete:
    def test_delete_confirmed(self, runner, ctx):
        ctx.client.labels.delete.return_value = None
        result = runner.invoke(label, ["delete", "lbl-001"], obj=ctx, input="y\n")
        assert result.exit_code == 0, result.output

    def test_delete_aborted(self, runner, ctx):
        result = runner.invoke(label, ["delete", "lbl-001"], obj=ctx, input="n\n")
        # label delete는 confirm 거부 시 return으로 종료 (exit_code 0)
        assert result.exit_code == 0
        ctx.client.labels.delete.assert_not_called()
