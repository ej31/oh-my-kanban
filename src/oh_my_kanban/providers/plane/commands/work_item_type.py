"""워크 아이템 타입(Work Item Type) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.work_item_types import CreateWorkItemType, UpdateWorkItemType

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output
from oh_my_kanban.utils import confirm_delete

# 워크 아이템 타입 출력 컬럼
_COLUMNS = ["id", "name", "description", "is_epic", "is_default", "is_active", "level"]


@click.group()
def work_item_type() -> None:
    """워크 아이템 타입 관리 (프로젝트 수준)."""
    pass


@work_item_type.command("list")
@click.pass_obj
@handle_api_error
def work_item_type_list(ctx: CliContext) -> None:
    """워크 아이템 타입 목록 조회."""
    project_id = ctx.require_project()
    results = ctx.client.work_item_types.list(ctx.workspace, project_id)
    format_output(results, ctx.output, columns=_COLUMNS)


@work_item_type.command("get")
@click.argument("type_id")
@click.pass_obj
@handle_api_error
def work_item_type_get(ctx: CliContext, type_id: str) -> None:
    """워크 아이템 타입 상세 조회."""
    project_id = ctx.require_project()
    result = ctx.client.work_item_types.retrieve(ctx.workspace, project_id, type_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@work_item_type.command("create")
@click.option("--name", required=True, help="타입 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-epic", is_flag=True, default=False, help="에픽 타입 여부")
@click.option("--is-active", is_flag=True, default=True, help="활성화 여부")
@click.pass_obj
@handle_api_error
def work_item_type_create(
    ctx: CliContext,
    name: str,
    description: str | None,
    is_epic: bool,
    is_active: bool,
) -> None:
    """새 워크 아이템 타입 생성."""
    project_id = ctx.require_project()

    data = CreateWorkItemType(
        name=name,
        description=description,
        is_epic=is_epic,
        is_active=is_active,
        project_ids=[project_id],
    )
    result = ctx.client.work_item_types.create(ctx.workspace, project_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@work_item_type.command("update")
@click.argument("type_id")
@click.option("--name", default=None, help="타입 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-epic", default=None, type=bool, help="에픽 타입 여부")
@click.option("--is-active", default=None, type=bool, help="활성화 여부")
@click.pass_obj
@handle_api_error
def work_item_type_update(
    ctx: CliContext,
    type_id: str,
    name: str | None,
    description: str | None,
    is_epic: bool | None,
    is_active: bool | None,
) -> None:
    """워크 아이템 타입 수정."""
    project_id = ctx.require_project()

    data = UpdateWorkItemType(
        name=name,
        description=description,
        is_epic=is_epic,
        is_active=is_active,
    )
    result = ctx.client.work_item_types.update(ctx.workspace, project_id, type_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@work_item_type.command("delete")
@click.argument("type_id")
@click.pass_obj
@handle_api_error
def work_item_type_delete(ctx: CliContext, type_id: str) -> None:
    """워크 아이템 타입 삭제."""
    project_id = ctx.require_project()

    if not confirm_delete("워크 아이템 타입", type_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.work_item_types.delete(ctx.workspace, project_id, type_id)
    click.echo(f"워크 아이템 타입 '{type_id}'을(를) 삭제했습니다.")
