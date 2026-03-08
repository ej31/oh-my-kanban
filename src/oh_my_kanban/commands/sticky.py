"""스티키(Sticky) 관련 커맨드."""

from __future__ import annotations

import html
import click
from plane.models.stickies import CreateSticky, UpdateSticky

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 스티키 출력 컬럼
_COLUMNS = ["id", "name", "color", "background_color", "owner", "sort_order"]


@click.group()
def sticky() -> None:
    """스티키 관리 (워크스페이스 수준)."""
    pass


@sticky.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.option("--query", default=None, help="검색 키워드")
@click.pass_obj
@handle_api_error
def sticky_list(ctx: CliContext, per_page: int, fetch_all: bool, query: str | None) -> None:
    """스티키 목록 조회."""
    ws = ctx.workspace
    params: dict = {"per_page": per_page}
    if query:
        params["query"] = query

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.stickies.list,
            ws,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_COLUMNS)
    else:
        response = ctx.client.stickies.list(ws, params=params)
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@sticky.command("get")
@click.argument("sticky_id")
@click.pass_obj
@handle_api_error
def sticky_get(ctx: CliContext, sticky_id: str) -> None:
    """스티키 상세 조회."""
    result = ctx.client.stickies.retrieve(ctx.workspace, sticky_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@sticky.command("create")
@click.option("--name", default=None, help="스티키 이름")
@click.option("--description", default=None, help="내용 (HTML)")
@click.option("--color", default=None, help="텍스트 색상 (예: #FF0000)")
@click.option("--background-color", default=None, help="배경 색상 (예: #FFFF00)")
@click.pass_obj
@handle_api_error
def sticky_create(
    ctx: CliContext,
    name: str | None,
    description: str | None,
    color: str | None,
    background_color: str | None,
) -> None:
    """새 스티키 생성."""
    data = CreateSticky(
        name=name,
        description_html=f"<p>{html.escape(description)}</p>" if description else None,
        color=color,
        background_color=background_color,
    )
    result = ctx.client.stickies.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@sticky.command("update")
@click.argument("sticky_id")
@click.option("--name", default=None, help="스티키 이름")
@click.option("--description", default=None, help="내용 (HTML)")
@click.option("--color", default=None, help="텍스트 색상 (예: #FF0000)")
@click.option("--background-color", default=None, help="배경 색상 (예: #FFFF00)")
@click.pass_obj
@handle_api_error
def sticky_update(
    ctx: CliContext,
    sticky_id: str,
    name: str | None,
    description: str | None,
    color: str | None,
    background_color: str | None,
) -> None:
    """스티키 수정."""
    data = UpdateSticky(
        name=name,
        description_html=f"<p>{html.escape(description)}</p>" if description else None,
        color=color,
        background_color=background_color,
    )
    result = ctx.client.stickies.update(ctx.workspace, sticky_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@sticky.command("delete")
@click.argument("sticky_id")
@click.pass_obj
@handle_api_error
def sticky_delete(ctx: CliContext, sticky_id: str) -> None:
    """스티키 삭제."""
    if not confirm_delete("스티키", sticky_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.stickies.delete(ctx.workspace, sticky_id)
    click.echo(f"스티키 '{sticky_id}'을(를) 삭제했습니다.")
