"""Linear 팀 조회 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.linear_context import LinearContext
from oh_my_kanban.linear_errors import handle_linear_error
from oh_my_kanban.output import format_output

_TEAMS_QUERY = "{ teams { nodes { id name key } } }"

_TEAM_QUERY = """
query GetTeam($id: String!) {
  team(id: $id) { id name key description }
}
"""


@click.group("team")
def team() -> None:
    """Linear 팀 관리."""


@team.command("list")
@click.pass_obj
@handle_linear_error
def team_list(ctx: LinearContext) -> None:
    """팀 목록을 조회한다."""
    data = ctx.client.execute(_TEAMS_QUERY)
    nodes = data.get("teams", {}).get("nodes", [])
    format_output(nodes, ctx.output, columns=["id", "name", "key"])


@team.command("get")
@click.argument("team_id")
@click.pass_obj
@handle_linear_error
def team_get(ctx: LinearContext, team_id: str) -> None:
    """팀 상세 정보를 조회한다."""
    data = ctx.client.execute(_TEAM_QUERY, {"id": team_id})
    format_output(data.get("team", {}), ctx.output)
