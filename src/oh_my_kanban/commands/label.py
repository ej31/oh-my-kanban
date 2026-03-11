"""레이블(Label) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.labels import CreateLabel, UpdateLabel

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint

# 출력 컬럼 정의
_COLUMNS = ["id", "name", "color", "parent"]


@click.group()
def label() -> None:
    """레이블 관리."""
    pass


@label.command("list")
@click.option("--per-page", type=int, default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, help="모든 페이지 가져오기")
@click.pass_obj
@handle_api_error
def label_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """레이블 목록 조회."""
    project_id = ctx.require_project()

    if fetch_all:
        from oh_my_kanban.utils import fetch_all_pages

        items = fetch_all_pages(
            ctx.client.labels.list,
            workspace_slug=ctx.workspace,
            project_id=project_id,
            per_page=per_page,
        )
        format_output(items, ctx.output, columns=_COLUMNS)
    else:
        from plane.models.query_params import PaginatedQueryParams

        response = ctx.client.labels.list(
            workspace_slug=ctx.workspace,
            project_id=project_id,
            params=PaginatedQueryParams(per_page=per_page),
        )
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@label.command("get")
@click.argument("label_id")
@click.pass_obj
@handle_api_error
def label_get(ctx: CliContext, label_id: str) -> None:
    """레이블 상세 조회."""
    project_id = ctx.require_project()
    result = ctx.client.labels.retrieve(ctx.workspace, project_id, label_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@label.command("create")
@click.option("--name", required=True, help="레이블 이름")
@click.option("--color", required=True, help="레이블 색상 (예: #FF0000)")
@click.option("--parent", default=None, help="부모 레이블 UUID")
@click.pass_obj
@handle_api_error
def label_create(
    ctx: CliContext,
    name: str,
    color: str,
    parent: str | None,
) -> None:
    """새 레이블 생성."""
    project_id = ctx.require_project()

    data = CreateLabel(name=name, color=color, parent=parent)
    result = ctx.client.labels.create(ctx.workspace, project_id, data=data)
    format_output(result, ctx.output, columns=_COLUMNS)


@label.command("update")
@click.argument("label_id")
@click.option("--name", default=None, help="새 레이블 이름")
@click.option("--color", default=None, help="새 레이블 색상 (예: #FF0000)")
@click.option("--parent", default=None, help="부모 레이블 UUID")
@click.pass_obj
@handle_api_error
def label_update(
    ctx: CliContext,
    label_id: str,
    name: str | None,
    color: str | None,
    parent: str | None,
) -> None:
    """레이블 수정."""
    project_id = ctx.require_project()

    data = UpdateLabel(name=name, color=color, parent=parent)
    result = ctx.client.labels.update(ctx.workspace, project_id, label_id, data=data)
    format_output(result, ctx.output, columns=_COLUMNS)


@label.command("delete")
@click.argument("label_id")
@click.pass_obj
@handle_api_error
def label_delete(ctx: CliContext, label_id: str) -> None:
    """레이블 삭제."""
    project_id = ctx.require_project()

    if not click.confirm(f"레이블 '{label_id}'를 삭제하시겠습니까?"):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.labels.delete(ctx.workspace, project_id, label_id)
    click.echo(f"레이블 '{label_id}'가 삭제되었습니다.")
