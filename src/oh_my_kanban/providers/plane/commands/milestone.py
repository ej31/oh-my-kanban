"""마일스톤 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 마일스톤 목록 출력 컬럼
_MILESTONE_COLUMNS = ["id", "title", "target_date", "created_at"]

# 마일스톤 워크 아이템 출력 컬럼
_WORK_ITEM_COLUMNS = ["id", "issue", "milestone"]


@click.group()
def milestone() -> None:
    """마일스톤 관리."""
    pass


@milestone.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 결과 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def milestone_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """마일스톤 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.milestones.list,
            ws,
            project_id,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_MILESTONE_COLUMNS)
    else:
        response = ctx.client.milestones.list(ws, project_id, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_MILESTONE_COLUMNS)
        format_pagination_hint(response, ctx.output)


@milestone.command("get")
@click.argument("milestone_id")
@click.pass_obj
@handle_api_error
def milestone_get(ctx: CliContext, milestone_id: str) -> None:
    """마일스톤 상세 정보를 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    result = ctx.client.milestones.retrieve(ws, project_id, milestone_id)
    format_output(result, ctx.output)


@milestone.command("create")
@click.option("--title", required=True, help="마일스톤 제목")
@click.option("--target-date", default=None, help="목표 날짜 (YYYY-MM-DD)")
@click.pass_obj
@handle_api_error
def milestone_create(
    ctx: CliContext,
    title: str,
    target_date: str | None,
) -> None:
    """새 마일스톤을 생성한다."""
    from plane.models.milestones import CreateMilestone

    project_id = ctx.require_project()
    ws = ctx.workspace

    data = CreateMilestone(
        title=title,
        target_date=target_date,
    )
    result = ctx.client.milestones.create(ws, project_id, data=data)
    format_output(result, ctx.output)


@milestone.command("update")
@click.argument("milestone_id")
@click.option("--title", default=None, help="마일스톤 제목")
@click.option("--target-date", default=None, help="목표 날짜 (YYYY-MM-DD)")
@click.pass_obj
@handle_api_error
def milestone_update(
    ctx: CliContext,
    milestone_id: str,
    title: str | None,
    target_date: str | None,
) -> None:
    """마일스톤 정보를 수정한다."""
    from plane.models.milestones import UpdateMilestone

    project_id = ctx.require_project()
    ws = ctx.workspace

    data = UpdateMilestone(
        title=title,
        target_date=target_date,
    )
    result = ctx.client.milestones.update(ws, project_id, milestone_id, data=data)
    format_output(result, ctx.output)


@milestone.command("delete")
@click.argument("milestone_id")
@click.pass_obj
@handle_api_error
def milestone_delete(ctx: CliContext, milestone_id: str) -> None:
    """마일스톤을 삭제한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    if not confirm_delete("마일스톤", milestone_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.milestones.delete(ws, project_id, milestone_id)
    click.echo(f"마일스톤 '{milestone_id}'을(를) 삭제했습니다.")


@milestone.command("items")
@click.argument("milestone_id")
@click.pass_obj
@handle_api_error
def milestone_items(ctx: CliContext, milestone_id: str) -> None:
    """마일스톤에 포함된 워크 아이템 목록을 조회한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    response = ctx.client.milestones.list_work_items(ws, project_id, milestone_id)
    format_output(response.results, ctx.output, columns=_WORK_ITEM_COLUMNS)


@milestone.command("add-items")
@click.argument("milestone_id")
@click.option(
    "--items",
    multiple=True,
    required=True,
    help="추가할 워크 아이템 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def milestone_add_items(ctx: CliContext, milestone_id: str, items: tuple[str, ...]) -> None:
    """마일스톤에 워크 아이템을 추가한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.milestones.add_work_items(ws, project_id, milestone_id, issue_ids=list(items))
    click.echo(f"워크 아이템 {len(items)}개를 마일스톤 '{milestone_id}'에 추가했습니다.")


@milestone.command("remove-items")
@click.argument("milestone_id")
@click.option(
    "--items",
    multiple=True,
    required=True,
    help="제거할 워크 아이템 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def milestone_remove_items(ctx: CliContext, milestone_id: str, items: tuple[str, ...]) -> None:
    """마일스톤에서 워크 아이템을 제거한다."""
    project_id = ctx.require_project()
    ws = ctx.workspace

    ctx.client.milestones.remove_work_items(ws, project_id, milestone_id, issue_ids=list(items))
    click.echo(f"워크 아이템 {len(items)}개를 마일스톤 '{milestone_id}'에서 제거했습니다.")
