"""상태(State) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.states import CreateState, UpdateState

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint

# 출력 컬럼 정의
_COLUMNS = ["id", "name", "color", "group", "default"]

# 상태 그룹 선택지
_GROUP_CHOICES = click.Choice(
    ["backlog", "unstarted", "started", "completed", "cancelled"],
    case_sensitive=False,
)


@click.group()
def state() -> None:
    """상태 관리."""
    pass


@state.command("list")
@click.option("--per-page", type=int, default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, help="모든 페이지 가져오기")
@click.pass_obj
@handle_api_error
def state_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """상태 목록 조회."""
    project_id = ctx.require_project()

    if fetch_all:
        from oh_my_kanban.utils import fetch_all_pages

        items = fetch_all_pages(
            ctx.client.states.list,
            workspace_slug=ctx.workspace,
            project_id=project_id,
            per_page=per_page,
        )
        format_output(items, ctx.output, columns=_COLUMNS)
    else:
        from plane.models.query_params import PaginatedQueryParams

        response = ctx.client.states.list(
            workspace_slug=ctx.workspace,
            project_id=project_id,
            params=PaginatedQueryParams(per_page=per_page),
        )
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@state.command("get")
@click.argument("state_id")
@click.pass_obj
@handle_api_error
def state_get(ctx: CliContext, state_id: str) -> None:
    """상태 상세 조회."""
    project_id = ctx.require_project()
    result = ctx.client.states.retrieve(ctx.workspace, project_id, state_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@state.command("create")
@click.option("--name", required=True, help="상태 이름")
@click.option("--color", required=True, help="상태 색상 (예: #FF0000)")
@click.option("--group", type=_GROUP_CHOICES, default=None, help="상태 그룹")
@click.pass_obj
@handle_api_error
def state_create(
    ctx: CliContext,
    name: str,
    color: str,
    group: str | None,
) -> None:
    """새 상태 생성."""
    project_id = ctx.require_project()

    data = CreateState(name=name, color=color, group=group)
    result = ctx.client.states.create(ctx.workspace, project_id, data=data)
    format_output(result, ctx.output, columns=_COLUMNS)


@state.command("update")
@click.argument("state_id")
@click.option("--name", default=None, help="새 상태 이름")
@click.option("--color", default=None, help="새 상태 색상 (예: #FF0000)")
@click.option("--group", type=_GROUP_CHOICES, default=None, help="새 상태 그룹")
@click.pass_obj
@handle_api_error
def state_update(
    ctx: CliContext,
    state_id: str,
    name: str | None,
    color: str | None,
    group: str | None,
) -> None:
    """상태 수정."""
    project_id = ctx.require_project()

    data = UpdateState(name=name, color=color, group=group)
    result = ctx.client.states.update(ctx.workspace, project_id, state_id, data=data)
    format_output(result, ctx.output, columns=_COLUMNS)


@state.command("delete")
@click.argument("state_id")
@click.pass_obj
@handle_api_error
def state_delete(ctx: CliContext, state_id: str) -> None:
    """상태 삭제."""
    project_id = ctx.require_project()

    if not click.confirm(f"상태 '{state_id}'를 삭제하시겠습니까?"):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.states.delete(ctx.workspace, project_id, state_id)
    click.echo(f"상태 '{state_id}'가 삭제되었습니다.")
