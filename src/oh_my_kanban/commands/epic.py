"""에픽 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint

# 에픽 목록 출력 컬럼
_EPIC_COLUMNS = ["id", "name", "priority", "start_date", "target_date", "state"]


@click.group()
def epic() -> None:
    """에픽 관리."""
    pass


@epic.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.pass_obj
@handle_api_error
def epic_list(ctx: CliContext, per_page: int) -> None:
    """에픽 목록을 조회한다."""
    from plane.models.query_params import PaginatedQueryParams

    project_id = ctx.require_project()
    ws = ctx.workspace

    params = PaginatedQueryParams(per_page=per_page)
    response = ctx.client.epics.list(ws, project_id, params=params)
    format_output(response.results, ctx.output, columns=_EPIC_COLUMNS)
    format_pagination_hint(response, ctx.output)


@epic.command("get")
@click.argument("epic_id")
@click.pass_obj
@handle_api_error
def epic_get(ctx: CliContext, epic_id: str) -> None:
    """에픽 상세 정보를 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    result = ctx.client.epics.retrieve(ws, project_id, epic_id)
    format_output(result, ctx.output)
