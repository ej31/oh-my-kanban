"""Linear workflow state 조회 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.providers.linear.context import LinearContext
from oh_my_kanban.providers.linear.errors import handle_linear_error
from oh_my_kanban.output import format_output

_STATES_QUERY = """
query GetStates($id: String!) {
  team(id: $id) { states { nodes { id name type position } } }
}
"""


@click.group("state")
def state() -> None:
    """Linear workflow state 관리.

    Team-scoped command group. `--team` can fall back to LINEAR_TEAM_ID or
    config `linear.team_id`.
    """


@state.command("list")
@click.option("--team", "team_id", default=None, help="팀 ID")
@click.pass_obj
@handle_linear_error
def state_list(ctx: LinearContext, team_id: str | None) -> None:
    """팀의 workflow state 목록을 조회한다.

    Team is resolved from `--team`, `LINEAR_TEAM_ID`, or config `linear.team_id`.
    """
    tid = team_id or ctx.require_team()
    data = ctx.client.execute(_STATES_QUERY, {"id": tid})
    nodes = data.get("team", {}).get("states", {}).get("nodes", [])
    format_output(nodes, ctx.output, columns=["id", "name", "type", "position"])
