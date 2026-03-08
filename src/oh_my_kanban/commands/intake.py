"""인테이크(Intake) 관련 커맨드."""

from __future__ import annotations

import html
import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 인테이크 워크 아이템 목록 출력 컬럼
_INTAKE_COLUMNS = ["id", "status", "source", "created_at", "updated_at"]


@click.group()
def intake() -> None:
    """인테이크 워크 아이템 관리."""
    pass


@intake.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def intake_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """인테이크 워크 아이템 목록을 조회한다."""
    from plane.models.query_params import PaginatedQueryParams

    project_id = ctx.require_project()
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            lambda *a, **kw: ctx.client.intake.list(
                ws,
                project_id,
                params=PaginatedQueryParams(per_page=kw.get("per_page", per_page)),
            ),
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_INTAKE_COLUMNS)
    else:
        params = PaginatedQueryParams(per_page=per_page)
        response = ctx.client.intake.list(ws, project_id, params=params)
        format_output(response.results, ctx.output, columns=_INTAKE_COLUMNS)
        format_pagination_hint(response, ctx.output)


@intake.command("get")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def intake_get(ctx: CliContext, work_item_id: str) -> None:
    """인테이크 워크 아이템 상세 정보를 조회한다.

    \b
    WORK_ITEM_ID: 인테이크 목록(list)의 'issue' 필드 UUID를 사용합니다.
    인테이크 자체의 'id' 필드가 아님에 주의하세요.
    """
    project_id = ctx.require_project()
    ws = ctx.workspace

    result = ctx.client.intake.retrieve(ws, project_id, work_item_id)
    format_output(result, ctx.output)


@intake.command("create")
@click.option("--name", required=True, help="워크 아이템 이름")
@click.option("--description", default=None, help="워크 아이템 설명 (HTML 형식)")
@click.option(
    "--priority",
    default=None,
    type=click.Choice(["urgent", "high", "medium", "low", "none"], case_sensitive=False),
    help="우선순위",
)
@click.option("--source", default=None, help="소스 (예: email, api)")
@click.pass_obj
@handle_api_error
def intake_create(
    ctx: CliContext,
    name: str,
    description: str | None,
    priority: str | None,
    source: str | None,
) -> None:
    """새 인테이크 워크 아이템을 생성한다."""
    from plane.models.intake import CreateIntakeWorkItem
    from plane.models.work_items import WorkItemForIntakeRequest

    project_id = ctx.require_project()
    ws = ctx.workspace

    issue_data = WorkItemForIntakeRequest(
        name=name,
        description_html=f"<p>{html.escape(description)}</p>" if description else None,
        priority=priority,
    )
    data = CreateIntakeWorkItem(issue=issue_data)
    result = ctx.client.intake.create(ws, project_id, data=data)
    format_output(result, ctx.output)


@intake.command("update")
@click.argument("work_item_id")
@click.option(
    "--status",
    default=None,
    type=int,
    help="인테이크 상태 코드 (-2: 거부, -1: 스누즈, 0: 대기, 1: 승인, 2: 중복)",
)
@click.option("--source", default=None, help="소스")
@click.option("--duplicate-to", default=None, help="중복 대상 워크 아이템 UUID")
@click.pass_obj
@handle_api_error
def intake_update(
    ctx: CliContext,
    work_item_id: str,
    status: int | None,
    source: str | None,
    duplicate_to: str | None,
) -> None:
    """인테이크 워크 아이템을 수정한다.

    \b
    WORK_ITEM_ID: 인테이크 목록(list)의 'issue' 필드 UUID를 사용합니다.
    인테이크 자체의 'id' 필드가 아님에 주의하세요.
    """
    from plane.models.intake import UpdateIntakeWorkItem

    project_id = ctx.require_project()
    ws = ctx.workspace

    data = UpdateIntakeWorkItem(
        status=status,
        source=source,
        duplicate_to=duplicate_to,
    )
    result = ctx.client.intake.update(ws, project_id, work_item_id, data=data)
    format_output(result, ctx.output)


@intake.command("delete")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def intake_delete(ctx: CliContext, work_item_id: str) -> None:
    """인테이크 워크 아이템을 삭제한다.

    \b
    WORK_ITEM_ID: 인테이크 목록(list)의 'issue' 필드 UUID를 사용합니다.
    인테이크 자체의 'id' 필드가 아님에 주의하세요.
    """
    project_id = ctx.require_project()
    ws = ctx.workspace

    if not confirm_delete("인테이크 워크 아이템", work_item_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.intake.delete(ws, project_id, work_item_id)
    click.echo(f"인테이크 워크 아이템 '{work_item_id}'을(를) 삭제했습니다.")
