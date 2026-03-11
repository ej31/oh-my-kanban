"""Linear 사이클 관리 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.providers.linear.context import LinearContext
from oh_my_kanban.providers.linear.errors import handle_linear_error
from oh_my_kanban.output import format_output

_CYCLES_QUERY = """
query GetCycles($id: String!) {
  team(id: $id) { cycles { nodes { id name startsAt endsAt } } }
}
"""

_CYCLE_QUERY = """
query GetCycle($id: String!) {
  cycle(id: $id) { id name startsAt endsAt completedAt }
}
"""


@click.group()
def cycle() -> None:
    """Linear 사이클 관리."""


@cycle.command("list")
@click.option("--team", "team_id", default=None, help="팀 ID")
@click.pass_obj
@handle_linear_error
def cycle_list(ctx: LinearContext, team_id: str | None) -> None:
    """팀의 사이클 목록을 조회한다."""
    tid = team_id or ctx.require_team()
    data = ctx.client.execute(_CYCLES_QUERY, {"id": tid})
    nodes = data.get("team", {}).get("cycles", {}).get("nodes", [])
    format_output(nodes, ctx.output, columns=["id", "name", "startsAt", "endsAt"])


@cycle.command("get")
@click.argument("cycle_id")
@click.pass_obj
@handle_linear_error
def cycle_get(ctx: LinearContext, cycle_id: str) -> None:
    """사이클 상세 정보를 조회한다."""
    data = ctx.client.execute(_CYCLE_QUERY, {"id": cycle_id})
    format_output(data.get("cycle", {}), ctx.output)
