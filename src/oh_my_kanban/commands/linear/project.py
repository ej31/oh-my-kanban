"""Linear 프로젝트 관리 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.linear_context import LinearContext
from oh_my_kanban.linear_errors import handle_linear_error
from oh_my_kanban.output import format_output

_PROJECTS_QUERY = """
query GetProjects($first: Int, $after: String) {
  projects(first: $first, after: $after) {
    nodes { id name state }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_PROJECT_QUERY = """
query GetProject($id: String!) {
  project(id: $id) { id name description state startDate targetDate }
}
"""


@click.group()
def project() -> None:
    """Linear 프로젝트 관리."""


@project.command("list")
@click.option("--first", default=50, show_default=True, help="페이지당 결과 수")
@click.pass_obj
@handle_linear_error
def project_list(ctx: LinearContext, first: int) -> None:
    """프로젝트 목록을 조회한다 (Relay 페이지네이션)."""
    results = ctx.client.paginate_relay(
        _PROJECTS_QUERY,
        {"first": first},
        path="projects",
    )
    format_output(results, ctx.output, columns=["id", "name", "state"])


@project.command("get")
@click.argument("project_id")
@click.pass_obj
@handle_linear_error
def project_get(ctx: LinearContext, project_id: str) -> None:
    """프로젝트 상세 정보를 조회한다."""
    data = ctx.client.execute(_PROJECT_QUERY, {"id": project_id})
    format_output(data.get("project", {}), ctx.output)
