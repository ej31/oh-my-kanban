"""워크 아이템 속성(Work Item Property) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.work_item_properties import (
    CreateWorkItemProperty,
    CreateWorkItemPropertyOption,
    CreateWorkItemPropertyValue,
    UpdateWorkItemProperty,
    UpdateWorkItemPropertyOption,
)

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output
from oh_my_kanban.utils import confirm_delete

# 속성 출력 컬럼
_PROPERTY_COLUMNS = [
    "id", "display_name", "property_type", "is_required", "is_active", "is_multi",
]

# 옵션 출력 컬럼
_OPTION_COLUMNS = ["id", "name", "is_active", "is_default", "sort_order"]

# 값 출력 컬럼
_VALUE_COLUMNS = ["id", "property_id", "issue_id", "value", "value_type"]


@click.group()
def work_item_property() -> None:
    """워크 아이템 속성 관리 (프로젝트 수준)."""
    pass


@work_item_property.command("list")
@click.option("--type-id", required=True, help="워크 아이템 타입 UUID")
@click.pass_obj
@handle_api_error
def work_item_property_list(ctx: CliContext, type_id: str) -> None:
    """워크 아이템 속성 목록 조회."""
    project_id = ctx.require_project()
    results = ctx.client.work_item_properties.list(ctx.workspace, project_id, type_id)
    format_output(results, ctx.output, columns=_PROPERTY_COLUMNS)


@work_item_property.command("get")
@click.argument("property_id")
@click.option("--type-id", required=True, help="워크 아이템 타입 UUID")
@click.pass_obj
@handle_api_error
def work_item_property_get(ctx: CliContext, property_id: str, type_id: str) -> None:
    """워크 아이템 속성 상세 조회."""
    project_id = ctx.require_project()
    result = ctx.client.work_item_properties.retrieve(
        ctx.workspace, project_id, type_id, property_id
    )
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@work_item_property.command("create")
@click.option("--type-id", required=True, help="워크 아이템 타입 UUID")
@click.option("--display-name", required=True, help="속성 표시 이름")
@click.option(
    "--property-type",
    required=True,
    type=click.Choice(
        ["text", "number", "checkbox", "select", "multi_select", "date", "member", "url", "email", "file", "relation"],
        case_sensitive=False,
    ),
    help="속성 타입",
)
@click.option("--description", default=None, help="설명")
@click.option("--is-required", is_flag=True, default=False, help="필수 여부")
@click.option("--is-active", is_flag=True, default=True, help="활성화 여부")
@click.option("--is-multi", is_flag=True, default=False, help="다중값 허용 여부")
@click.pass_obj
@handle_api_error
def work_item_property_create(
    ctx: CliContext,
    type_id: str,
    display_name: str,
    property_type: str,
    description: str | None,
    is_required: bool,
    is_active: bool,
    is_multi: bool,
) -> None:
    """새 워크 아이템 속성 생성."""
    from plane.models.enums import PropertyType

    project_id = ctx.require_project()

    data = CreateWorkItemProperty(
        display_name=display_name,
        property_type=PropertyType(property_type.lower()),
        description=description,
        is_required=is_required,
        is_active=is_active,
        is_multi=is_multi,
    )
    result = ctx.client.work_item_properties.create(ctx.workspace, project_id, type_id, data)
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@work_item_property.command("update")
@click.argument("property_id")
@click.option("--type-id", required=True, help="워크 아이템 타입 UUID")
@click.option("--display-name", default=None, help="속성 표시 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-required", default=None, type=bool, help="필수 여부")
@click.option("--is-active", default=None, type=bool, help="활성화 여부")
@click.option("--is-multi", default=None, type=bool, help="다중값 허용 여부")
@click.pass_obj
@handle_api_error
def work_item_property_update(
    ctx: CliContext,
    property_id: str,
    type_id: str,
    display_name: str | None,
    description: str | None,
    is_required: bool | None,
    is_active: bool | None,
    is_multi: bool | None,
) -> None:
    """워크 아이템 속성 수정."""
    project_id = ctx.require_project()

    data = UpdateWorkItemProperty(
        display_name=display_name,
        description=description,
        is_required=is_required,
        is_active=is_active,
        is_multi=is_multi,
    )
    result = ctx.client.work_item_properties.update(
        ctx.workspace, project_id, type_id, property_id, data
    )
    format_output(result, ctx.output, columns=_PROPERTY_COLUMNS)


@work_item_property.command("delete")
@click.argument("property_id")
@click.option("--type-id", required=True, help="워크 아이템 타입 UUID")
@click.pass_obj
@handle_api_error
def work_item_property_delete(ctx: CliContext, property_id: str, type_id: str) -> None:
    """워크 아이템 속성 삭제."""
    project_id = ctx.require_project()

    if not confirm_delete("워크 아이템 속성", property_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.work_item_properties.delete(ctx.workspace, project_id, type_id, property_id)
    click.echo(f"워크 아이템 속성 '{property_id}'을(를) 삭제했습니다.")


# ── 옵션 서브그룹 ─────────────────────────────────────────────────────────

@work_item_property.group("option")
def work_item_property_option() -> None:
    """워크 아이템 속성 옵션 관리."""
    pass


@work_item_property_option.command("list")
@click.argument("property_id")
@click.pass_obj
@handle_api_error
def option_list(ctx: CliContext, property_id: str) -> None:
    """속성 옵션 목록 조회."""
    project_id = ctx.require_project()
    results = ctx.client.work_item_properties.options.list(
        ctx.workspace, project_id, property_id
    )
    format_output(results, ctx.output, columns=_OPTION_COLUMNS)


@work_item_property_option.command("get")
@click.argument("property_id")
@click.argument("option_id")
@click.pass_obj
@handle_api_error
def option_get(ctx: CliContext, property_id: str, option_id: str) -> None:
    """속성 옵션 상세 조회."""
    project_id = ctx.require_project()
    result = ctx.client.work_item_properties.options.retrieve(
        ctx.workspace, project_id, property_id, option_id
    )
    format_output(result, ctx.output, columns=_OPTION_COLUMNS)


@work_item_property_option.command("create")
@click.argument("property_id")
@click.option("--name", required=True, help="옵션 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-active", is_flag=True, default=True, help="활성화 여부")
@click.option("--is-default", is_flag=True, default=False, help="기본값 여부")
@click.option("--parent", default=None, help="부모 옵션 UUID")
@click.pass_obj
@handle_api_error
def option_create(
    ctx: CliContext,
    property_id: str,
    name: str,
    description: str | None,
    is_active: bool,
    is_default: bool,
    parent: str | None,
) -> None:
    """속성 옵션 생성."""
    project_id = ctx.require_project()

    data = CreateWorkItemPropertyOption(
        name=name,
        description=description,
        is_active=is_active,
        is_default=is_default,
        parent=parent,
    )
    result = ctx.client.work_item_properties.options.create(
        ctx.workspace, project_id, property_id, data
    )
    format_output(result, ctx.output, columns=_OPTION_COLUMNS)


@work_item_property_option.command("update")
@click.argument("property_id")
@click.argument("option_id")
@click.option("--name", default=None, help="옵션 이름")
@click.option("--description", default=None, help="설명")
@click.option("--is-active", default=None, type=bool, help="활성화 여부")
@click.option("--is-default", default=None, type=bool, help="기본값 여부")
@click.pass_obj
@handle_api_error
def option_update(
    ctx: CliContext,
    property_id: str,
    option_id: str,
    name: str | None,
    description: str | None,
    is_active: bool | None,
    is_default: bool | None,
) -> None:
    """속성 옵션 수정."""
    project_id = ctx.require_project()

    data = UpdateWorkItemPropertyOption(
        name=name,
        description=description,
        is_active=is_active,
        is_default=is_default,
    )
    result = ctx.client.work_item_properties.options.update(
        ctx.workspace, project_id, property_id, option_id, data
    )
    format_output(result, ctx.output, columns=_OPTION_COLUMNS)


@work_item_property_option.command("delete")
@click.argument("property_id")
@click.argument("option_id")
@click.pass_obj
@handle_api_error
def option_delete(ctx: CliContext, property_id: str, option_id: str) -> None:
    """속성 옵션 삭제."""
    project_id = ctx.require_project()

    if not confirm_delete("속성 옵션", option_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.work_item_properties.options.delete(
        ctx.workspace, project_id, property_id, option_id
    )
    click.echo(f"속성 옵션 '{option_id}'을(를) 삭제했습니다.")


# ── 값 서브그룹 ───────────────────────────────────────────────────────────

@work_item_property.group("value")
def work_item_property_value() -> None:
    """워크 아이템 속성 값 관리."""
    pass


@work_item_property_value.command("list")
@click.argument("work_item_id")
@click.argument("property_id")
@click.pass_obj
@handle_api_error
def value_list(ctx: CliContext, work_item_id: str, property_id: str) -> None:
    """워크 아이템의 속성 값 조회."""
    project_id = ctx.require_project()
    result = ctx.client.work_item_properties.values.retrieve(
        ctx.workspace, project_id, work_item_id, property_id
    )
    # 단일 값 또는 목록 모두 처리
    if isinstance(result, list):
        format_output(result, ctx.output, columns=_VALUE_COLUMNS)
    else:
        format_output(result, ctx.output, columns=_VALUE_COLUMNS)


@work_item_property_value.command("update")
@click.argument("work_item_id")
@click.argument("property_id")
@click.option("--value", required=True, help="설정할 값")
@click.pass_obj
@handle_api_error
def value_update(
    ctx: CliContext,
    work_item_id: str,
    property_id: str,
    value: str,
) -> None:
    """워크 아이템의 속성 값을 설정(upsert)한다."""
    project_id = ctx.require_project()

    data = CreateWorkItemPropertyValue(value=value)
    result = ctx.client.work_item_properties.values.create(
        ctx.workspace, project_id, work_item_id, property_id, data
    )
    if isinstance(result, list):
        format_output(result, ctx.output, columns=_VALUE_COLUMNS)
    else:
        format_output(result, ctx.output, columns=_VALUE_COLUMNS)
    click.echo(f"속성 '{property_id}'의 값을 설정했습니다.", err=True)
