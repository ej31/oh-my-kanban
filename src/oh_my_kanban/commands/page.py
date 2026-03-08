"""페이지 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output

# 페이지 출력 컬럼
_PAGE_COLUMNS = ["id", "name", "owned_by", "created_at", "updated_at"]


@click.group()
def page() -> None:
    """페이지 관리."""
    pass


@page.command("get")
@click.argument("page_id")
@click.option("--workspace", "workspace_scope", is_flag=True, default=False, help="워크스페이스 페이지로 조회")
@click.pass_obj
@handle_api_error
def page_get(ctx: CliContext, page_id: str, workspace_scope: bool) -> None:
    """페이지 상세 정보를 조회한다."""
    ws = ctx.workspace

    if workspace_scope:
        result = ctx.client.pages.retrieve_workspace_page(ws, page_id)
    else:
        project_id = ctx.require_project()
        result = ctx.client.pages.retrieve_project_page(ws, project_id, page_id)

    format_output(result, ctx.output)


@page.command("create")
@click.option("--name", required=True, help="페이지 제목")
@click.option("--description-html", default="<p></p>", show_default=True, help="HTML 형식의 페이지 내용 (HTML이 그대로 전달되므로 신뢰할 수 없는 입력은 사용하지 마세요)")
@click.option("--workspace", "workspace_scope", is_flag=True, default=False, help="워크스페이스 페이지로 생성")
@click.pass_obj
@handle_api_error
def page_create(
    ctx: CliContext,
    name: str,
    description_html: str,
    workspace_scope: bool,
) -> None:
    """새 페이지를 생성한다."""
    from plane.models.pages import CreatePage

    ws = ctx.workspace

    data = CreatePage(
        name=name,
        description_html=description_html,
    )

    if workspace_scope:
        result = ctx.client.pages.create_workspace_page(ws, data=data)
    else:
        project_id = ctx.require_project()
        result = ctx.client.pages.create_project_page(ws, project_id, data=data)

    format_output(result, ctx.output)
