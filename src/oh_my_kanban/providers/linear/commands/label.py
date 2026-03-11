"""Linear 레이블 관리 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.providers.linear.context import LinearContext
from oh_my_kanban.providers.linear.errors import handle_linear_error
from oh_my_kanban.output import format_output

_LABELS_QUERY = """
query GetLabels($id: String!) {
  team(id: $id) { labels { nodes { id name color } } }
}
"""

_LABEL_QUERY = """
query GetLabel($id: String!) {
  issueLabel(id: $id) { id name color parent { id name } }
}
"""


@click.group()
def label() -> None:
    """Linear 레이블 관리."""


@label.command("list")
@click.option("--team", "team_id", default=None, help="팀 ID")
@click.pass_obj
@handle_linear_error
def label_list(ctx: LinearContext, team_id: str | None) -> None:
    """팀의 레이블 목록을 조회한다."""
    tid = team_id or ctx.require_team()
    data = ctx.client.execute(_LABELS_QUERY, {"id": tid})
    nodes = data.get("team", {}).get("labels", {}).get("nodes", [])
    format_output(nodes, ctx.output, columns=["id", "name", "color"])


@label.command("get")
@click.argument("label_id")
@click.pass_obj
@handle_linear_error
def label_get(ctx: LinearContext, label_id: str) -> None:
    """레이블 상세 정보를 조회한다."""
    data = ctx.client.execute(_LABEL_QUERY, {"id": label_id})
    format_output(data.get("issueLabel", {}), ctx.output)
