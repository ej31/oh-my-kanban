"""사이클 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 사이클 목록 출력 컬럼
_CYCLE_COLUMNS = ["id", "name", "status", "start_date", "end_date"]

# 사이클 워크 아이템 출력 컬럼
_WORK_ITEM_COLUMNS = ["id", "name", "priority", "state"]


@click.group()
def cycle() -> None:
    """사이클 관리."""
    pass


@cycle.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def cycle_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """사이클 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.cycles.list,
            ws,
            project_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_CYCLE_COLUMNS)
    else:
        response = ctx.client.cycles.list(ws, project_id, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_CYCLE_COLUMNS)
        format_pagination_hint(response, ctx.output)


@cycle.command("archived")
@click.pass_obj
@handle_api_error
def cycle_archived(ctx: CliContext) -> None:
    """아카이브된 사이클 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    response = ctx.client.cycles.list_archived(ws, project_id)
    format_output(response.results, ctx.output, columns=_CYCLE_COLUMNS)


@cycle.command("get")
@click.argument("cycle_id")
@click.pass_obj
@handle_api_error
def cycle_get(ctx: CliContext, cycle_id: str) -> None:
    """사이클 상세 정보를 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    result = ctx.client.cycles.retrieve(ws, project_id, cycle_id)
    format_output(result, ctx.output)


@cycle.command("create")
@click.option("--name", required=True, help="사이클 이름")
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="종료 날짜 (YYYY-MM-DD)")
@click.option("--description", default=None, help="사이클 설명")
@click.pass_obj
@handle_api_error
def cycle_create(
    ctx: CliContext,
    name: str,
    start_date: str | None,
    end_date: str | None,
    description: str | None,
) -> None:
    """새 사이클을 생성한다."""
    from plane.models.cycles import CreateCycle

    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    # 현재 사용자 ID를 owned_by로 사용
    me = ctx.client.users.get_me()
    if me is None or not me.id:
        raise click.UsageError("현재 사용자 ID를 가져올 수 없습니다.")
    owned_by = me.id

    data = CreateCycle(
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        owned_by=owned_by,
        project_id=project_id,
    )
    result = ctx.client.cycles.create(ws, project_id, data=data)
    format_output(result, ctx.output)


@cycle.command("update")
@click.argument("cycle_id")
@click.option("--name", default=None, help="사이클 이름")
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="종료 날짜 (YYYY-MM-DD)")
@click.option("--description", default=None, help="사이클 설명")
@click.pass_obj
@handle_api_error
def cycle_update(
    ctx: CliContext,
    cycle_id: str,
    name: str | None,
    start_date: str | None,
    end_date: str | None,
    description: str | None,
) -> None:
    """사이클 정보를 수정한다."""
    from plane.models.cycles import UpdateCycle

    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    data = UpdateCycle(
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
    )
    result = ctx.client.cycles.update(ws, project_id, cycle_id, data=data)
    format_output(result, ctx.output)


@cycle.command("delete")
@click.argument("cycle_id")
@click.pass_obj
@handle_api_error
def cycle_delete(ctx: CliContext, cycle_id: str) -> None:
    """사이클을 삭제한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    if not confirm_delete("사이클", cycle_id):
        raise click.Abort()

    ctx.client.cycles.delete(ws, project_id, cycle_id)
    click.echo(f"사이클 '{cycle_id}'을(를) 삭제했습니다.")


@cycle.command("archive")
@click.argument("cycle_id")
@click.pass_obj
@handle_api_error
def cycle_archive(ctx: CliContext, cycle_id: str) -> None:
    """사이클을 아카이브한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    ctx.client.cycles.archive(ws, project_id, cycle_id)
    click.echo(f"사이클 '{cycle_id}'을(를) 아카이브했습니다.")


@cycle.command("unarchive")
@click.argument("cycle_id")
@click.pass_obj
@handle_api_error
def cycle_unarchive(ctx: CliContext, cycle_id: str) -> None:
    """사이클 아카이브를 해제한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    ctx.client.cycles.unarchive(ws, project_id, cycle_id)
    click.echo(f"사이클 '{cycle_id}'의 아카이브를 해제했습니다.")


@cycle.command("items")
@click.argument("cycle_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def cycle_items(ctx: CliContext, cycle_id: str, per_page: int, fetch_all: bool) -> None:
    """사이클에 포함된 워크 아이템 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.cycles.list_work_items,
            ws,
            project_id,
            cycle_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_WORK_ITEM_COLUMNS)
    else:
        response = ctx.client.cycles.list_work_items(
            ws, project_id, cycle_id, params={"per_page": per_page}
        )
        format_output(response.results, ctx.output, columns=_WORK_ITEM_COLUMNS)
        format_pagination_hint(response, ctx.output)


@cycle.command("add-items")
@click.argument("cycle_id")
@click.option(
    "--items",
    multiple=True,
    required=True,
    help="추가할 워크 아이템 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def cycle_add_items(ctx: CliContext, cycle_id: str, items: tuple[str, ...]) -> None:
    """사이클에 워크 아이템을 추가한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    ctx.client.cycles.add_work_items(ws, project_id, cycle_id, issue_ids=list(items))
    click.echo(f"워크 아이템 {len(items)}개를 사이클 '{cycle_id}'에 추가했습니다.")


@cycle.command("remove-item")
@click.argument("cycle_id")
@click.argument("work_item_id")
@click.pass_obj
@handle_api_error
def cycle_remove_item(ctx: CliContext, cycle_id: str, work_item_id: str) -> None:
    """사이클에서 워크 아이템을 제거한다."""
    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    ctx.client.cycles.remove_work_item(ws, project_id, cycle_id, work_item_id)
    click.echo(f"워크 아이템 '{work_item_id}'을(를) 사이클 '{cycle_id}'에서 제거했습니다.")


@cycle.command("transfer")
@click.argument("cycle_id")
@click.option("--target", required=True, help="대상 사이클 UUID")
@click.pass_obj
@handle_api_error
def cycle_transfer(ctx: CliContext, cycle_id: str, target: str) -> None:
    """사이클의 워크 아이템을 다른 사이클로 이전한다."""
    from plane.models.cycles import TransferCycleWorkItemsRequest

    project_id = ctx.require_project()
    ws = ctx.require_workspace()

    data = TransferCycleWorkItemsRequest(new_cycle_id=target)
    ctx.client.cycles.transfer_work_items(ws, project_id, cycle_id, data=data)
    click.echo(f"사이클 '{cycle_id}'의 워크 아이템을 '{target}'으로 이전했습니다.")
