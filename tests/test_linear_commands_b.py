"""label / project / cycle 커맨드 B 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from oh_my_kanban.providers.linear.context import LinearContext


@pytest.fixture
def ctx() -> LinearContext:
    """테스트용 LinearContext (mock client)."""
    context = LinearContext(_api_key="test-key", team_id="team-123", output="json")
    context._client = MagicMock()
    return context


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ─── label ────────────────────────────────────────────────────────────────────


class TestLabelList:
    def test_label_list_with_team_option(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.label import label

        ctx.client.execute.return_value = {
            "team": {
                "labels": {
                    "nodes": [{"id": "lbl-1", "name": "Bug", "color": "#ff0000"}]
                }
            }
        }
        result = runner.invoke(label, ["list", "--team", "team-xyz"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "lbl-1" in result.output

    def test_label_list_uses_context_team(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.label import label

        ctx.client.execute.return_value = {
            "team": {
                "labels": {
                    "nodes": [{"id": "lbl-2", "name": "Feature", "color": "#00ff00"}]
                }
            }
        }
        result = runner.invoke(label, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "lbl-2" in result.output

    def test_label_list_no_team_raises(self, runner):
        from oh_my_kanban.providers.linear.commands.label import label

        no_team_ctx = LinearContext(_api_key="test-key", team_id="", output="json")
        no_team_ctx._client = MagicMock()
        result = runner.invoke(label, ["list"], obj=no_team_ctx)
        assert result.exit_code != 0

    def test_label_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.label import label

        ctx.client.execute.return_value = {"team": {"labels": {"nodes": []}}}
        result = runner.invoke(label, ["list"], obj=ctx)
        # 빈 결과는 정상 종료
        assert result.exit_code == 0


class TestLabelGet:
    def test_label_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.label import label

        ctx.client.execute.return_value = {
            "issueLabel": {
                "id": "lbl-1",
                "name": "Bug",
                "color": "#ff0000",
                "parent": None,
            }
        }
        result = runner.invoke(label, ["get", "lbl-1"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "lbl-1" in result.output


# ─── project ──────────────────────────────────────────────────────────────────


class TestProjectList:
    def test_project_list_relay_pagination(self, runner, ctx):
        """paginate_relay가 2페이지 결과를 합산해 반환하는지 검증한다."""
        from oh_my_kanban.providers.linear.commands.project import project

        ctx.client.paginate_relay.return_value = [
            {"id": "proj-1", "name": "Alpha", "state": "started"},
            {"id": "proj-2", "name": "Beta", "state": "planned"},
        ]
        result = runner.invoke(project, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "proj-1" in result.output
        assert "proj-2" in result.output
        ctx.client.paginate_relay.assert_called_once()

    def test_project_list_first_option(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.project import project

        ctx.client.paginate_relay.return_value = []
        result = runner.invoke(project, ["list", "--first", "10"], obj=ctx)
        assert result.exit_code == 0
        # paginate_relay 호출 시 first=10이 variables에 전달됐는지 확인
        call_args = ctx.client.paginate_relay.call_args
        variables = call_args[0][1]  # 두 번째 위치 인수가 variables dict
        assert variables.get("first") == 10

    def test_project_list_default_first_is_50(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.project import project

        ctx.client.paginate_relay.return_value = []
        runner.invoke(project, ["list"], obj=ctx)
        call_args = ctx.client.paginate_relay.call_args
        variables = call_args[0][1]
        assert variables.get("first") == 50


class TestProjectGet:
    def test_project_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.project import project

        ctx.client.execute.return_value = {
            "project": {
                "id": "proj-1",
                "name": "Alpha",
                "description": "설명",
                "state": "started",
                "startDate": "2024-01-01",
                "targetDate": "2024-06-01",
            }
        }
        result = runner.invoke(project, ["get", "proj-1"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "proj-1" in result.output


# ─── cycle ────────────────────────────────────────────────────────────────────


class TestCycleList:
    def test_cycle_list_with_team_option(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.cycle import cycle

        ctx.client.execute.return_value = {
            "team": {
                "cycles": {
                    "nodes": [
                        {
                            "id": "cyc-1",
                            "name": "Sprint 1",
                            "startsAt": "2024-01-01",
                            "endsAt": "2024-01-14",
                        }
                    ]
                }
            }
        }
        result = runner.invoke(cycle, ["list", "--team", "team-xyz"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "cyc-1" in result.output

    def test_cycle_list_uses_context_team(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.cycle import cycle

        ctx.client.execute.return_value = {
            "team": {
                "cycles": {
                    "nodes": [
                        {
                            "id": "cyc-2",
                            "name": "Sprint 2",
                            "startsAt": "2024-01-15",
                            "endsAt": "2024-01-28",
                        }
                    ]
                }
            }
        }
        result = runner.invoke(cycle, ["list"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "cyc-2" in result.output

    def test_cycle_list_no_team_raises(self, runner):
        from oh_my_kanban.providers.linear.commands.cycle import cycle

        no_team_ctx = LinearContext(_api_key="test-key", team_id="", output="json")
        no_team_ctx._client = MagicMock()
        result = runner.invoke(cycle, ["list"], obj=no_team_ctx)
        assert result.exit_code != 0

    def test_cycle_list_empty_returns_ok(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.cycle import cycle

        ctx.client.execute.return_value = {"team": {"cycles": {"nodes": []}}}
        result = runner.invoke(cycle, ["list"], obj=ctx)
        assert result.exit_code == 0


class TestCycleGet:
    def test_cycle_get_returns_detail(self, runner, ctx):
        from oh_my_kanban.providers.linear.commands.cycle import cycle

        ctx.client.execute.return_value = {
            "cycle": {
                "id": "cyc-1",
                "name": "Sprint 1",
                "startsAt": "2024-01-01",
                "endsAt": "2024-01-14",
                "completedAt": None,
            }
        }
        result = runner.invoke(cycle, ["get", "cyc-1"], obj=ctx)
        assert result.exit_code == 0, result.output
        assert "cyc-1" in result.output
