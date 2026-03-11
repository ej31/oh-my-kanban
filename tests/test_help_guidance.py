"""High-signal help guidance tests for agents."""

from oh_my_kanban.cli import cli


def test_plane_work_item_create_help_mentions_project_context(runner):
    result = runner.invoke(cli, ["plane", "work-item", "create", "--help"])
    assert result.exit_code == 0
    assert "PLANE_PROJECT_ID" in result.output


def test_plane_cycle_create_help_mentions_workspace_and_project_context(runner):
    result = runner.invoke(cli, ["plane", "cycle", "create", "--help"])
    assert result.exit_code == 0
    assert "PLANE_WORKSPACE_SLUG" in result.output
    assert "PLANE_PROJECT_ID" in result.output


def test_linear_state_list_help_mentions_team_fallback(runner):
    result = runner.invoke(cli, ["linear", "state", "list", "--help"])
    assert result.exit_code == 0
    assert "LINEAR_TEAM_ID" in result.output


def test_linear_issue_create_help_mentions_explicit_team_requirement(runner):
    result = runner.invoke(cli, ["linear", "issue", "create", "--help"])
    assert result.exit_code == 0
    assert "--team" in result.output
    assert "LINEAR_TEAM_ID" in result.output
