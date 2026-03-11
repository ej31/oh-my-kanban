"""모듈 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 모듈 목록 출력 컬럼
_MODULE_COLUMNS = ["id", "name", "status", "start_date", "target_date"]

# 모듈 워크 아이템 출력 컬럼
_WORK_ITEM_COLUMNS = ["id", "name", "priority", "state"]


@click.group()
def module() -> None:
    """모듈 관리."""
    pass


@module.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def module_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """모듈 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.modules.list,
            ws,
            project_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_MODULE_COLUMNS)
    else:
        response = ctx.client.modules.list(ws, project_id, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_MODULE_COLUMNS)
        format_pagination_hint(response, ctx.output)


@module.command("archived")
@click.pass_obj
@handle_api_error
def module_archived(ctx: CliContext) -> None:
    """아카이브된 모듈 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    response = ctx.client.modules.list_archived(ws, project_id)
    format_output(response.results, ctx.output, columns=_MODULE_COLUMNS)


@module.command("get")
@click.argument("module_id")
@click.pass_obj
@handle_api_error
def module_get(ctx: CliContext, module_id: str) -> None:
    """모듈 상세 정보를 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    result = ctx.client.modules.retrieve(ws, project_id, module_id)
    format_output(result, ctx.output)


@module.command("create")
@click.option("--name", required=True, help="모듈 이름")
@click.option("--description", default=None, help="모듈 설명")
@click.option(
    "--status",
    default=None,
    type=click.Choice(
        ["backlog", "planned", "in-progress", "paused", "completed", "cancelled"],
        case_sensitive=False,
    ),
    help="모듈 상태",
)
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--target-date", default=None, help="목표 날짜 (YYYY-MM-DD)")
@click.pass_obj
@handle_api_error
def module_create(
    ctx: CliContext,
    name: str,
    description: str | None,
    status: str | None,
    start_date: str | None,
    target_date: str | None,
) -> None:
    """새 모듈을 생성한다."""
    from plane.models.modules import CreateModule

    project_id = ctx.require_project()
    ws = ctx.workspace

    data = CreateModule(
        name=name,
        description=description,
        status=status,
        start_date=start_date,
        target_date=target_date,
    )
    result = ctx.client.modules.create(ws, project_id, data=data)
    format_output(result, ctx.output)


@module.command("update")
@click.argument("module_id")
@click.option("--name", default=None, help="모듈 이름")
@click.option("--description", default=None, help="모듈 설명")
@click.option(
    "--status",
    default=None,
    type=click.Choice(
        ["backlog", "planned", "in-progress", "paused", "completed", "cancelled"],
        case_sensitive=False,
    ),
    help="모듈 상태",
)
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--target-date", default=None, help="목표 날짜 (YYYY-MM-DD)")
@click.pass_obj
@handle_api_error
def module_update(
    ctx: CliContext,
    module_id: str,
    name: str | None,
    description: str | None,
    status: str | None,
    start_date: str | None,
    target_date: str | None,
) -> None:
    """모듈 정보를 수정한다."""
    from plane.models.modules import UpdateModule

    project_id = ctx.require_project()
    ws = ctx.workspace

    data = UpdateModule(
        name=name,
        description=description,
        status=status,
        start_date=start_date,
        target_date=target_date,
    )
    result = ctx.client.modules.update(ws, project_id, module_id, data=data)
    format_output(result, ctx.output)


@module.command("delete")
@click.argument("module_id")
@click.pass_obj
@handle_api_error
def module_delete(ctx: CliContext, module_id: str) -> None:
    """모듈을 삭제한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    if not confirm_delete("모듈", module_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.modules.delete(ws, project_id, module_id)
    click.echo(f"모듈 '{module_id}'을(를) 삭제했습니다.")


@module.command("archive")
@click.argument("module_id")
@click.pass_obj
@handle_api_error
def module_archive(ctx: CliContext, module_id: str) -> None:
    """모듈을 아카이브한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.modules.archive(ws, project_id, module_id)
    click.echo(f"모듈 '{module_id}'을(를) 아카이브했습니다.")


@module.command("unarchive")
@click.argument("module_id")
@click.pass_obj
@handle_api_error
def module_unarchive(ctx: CliContext, module_id: str) -> None:
    """모듈 아카이브를 해제한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.modules.unarchive(ws, project_id, module_id)
    click.echo(f"모듈 '{module_id}'의 아카이브를 해제했습니다.")


@module.command("items")
@click.argument("module_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def module_items(ctx: CliContext, module_id: str, per_page: int, fetch_all: bool) -> None:
    """모듈에 포함된 워크 아이템 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.modules.list_work_items,
            ws,
            project_id,
            module_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_WORK_ITEM_COLUMNS)
    else:
        response = ctx.client.modules.list_work_items(
            ws, project_id, module_id, params={"per_page": per_page}
        )
        format_output(response.results, ctx.output, columns=_WORK_ITEM_COLUMNS)
        format_pagination_hint(response, ctx.output)


@module.command("add-items")
@click.argument("module_id")
@click.option(
    "--items",
    multiple=True,
    required=True,
    help="추가할 워크 아이템 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def module_add_items(ctx: CliContext, module_id: str, items: tuple[str, ...]) -> None:
    """모듈에 워크 아이템을 추가한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.modules.add_work_items(ws, project_id, module_id, issue_ids=list(items))
    click.echo(f"워크 아이템 {len(items)}개를 모듈 '{module_id}'에 추가했습니다.")


@module.command("remove-item")
@click.argument("module_id")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def module_remove_item(ctx: CliContext, module_id: str, work_item_id: str) -> None:
    """모듈에서 워크 아이템을 제거한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.modules.remove_work_item(ws, project_id, module_id, work_item_id)
    click.echo(f"워크 아이템 '{work_item_id}'을(를) 모듈 '{module_id}'에서 제거했습니다.")
