"""워크스페이스 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output

# 멤버 출력 컬럼
_MEMBER_COLUMNS = ["id", "display_name", "email", "role"]


@click.group()
def workspace() -> None:
    """워크스페이스 관리."""
    pass


@workspace.command("members")
@click.pass_obj
@handle_api_error
def workspace_members(ctx: CliContext) -> None:
    """워크스페이스 멤버 목록을 조회한다."""
    if not ctx.workspace:
        raise click.UsageError(
            "워크스페이스 슬러그가 필요합니다. --workspace 옵션 또는 PLANE_WORKSPACE_SLUG 환경변수를 설정하세요."
        )

    result = ctx.client.workspaces.get_members(workspace_slug=ctx.workspace)
    format_output(result, ctx.output, columns=_MEMBER_COLUMNS)


@workspace.command("features")
@click.pass_obj
@handle_api_error
def workspace_features(ctx: CliContext) -> None:
    """워크스페이스 기능(feature) 설정을 조회한다."""
    if not ctx.workspace:
        raise click.UsageError(
            "워크스페이스 슬러그가 필요합니다. --workspace 옵션 또는 PLANE_WORKSPACE_SLUG 환경변수를 설정하세요."
        )

    result = ctx.client.workspaces.get_features(workspace_slug=ctx.workspace)
    format_output(result, ctx.output)


@workspace.command("update-features")
@click.option("--project-grouping", type=bool, default=None, help="프로젝트 그룹핑 활성화 여부")
@click.option("--initiatives", type=bool, default=None, help="이니셔티브 기능 활성화 여부")
@click.option("--teams", type=bool, default=None, help="팀 기능 활성화 여부")
@click.option("--customers", type=bool, default=None, help="고객 기능 활성화 여부")
@click.option("--wiki", type=bool, default=None, help="위키 기능 활성화 여부")
@click.option("--pi", type=bool, default=None, help="PI 기능 활성화 여부")
@click.pass_obj
@handle_api_error
def workspace_update_features(
    ctx: CliContext,
    project_grouping: bool | None,
    initiatives: bool | None,
    teams: bool | None,
    customers: bool | None,
    wiki: bool | None,
    pi: bool | None,
) -> None:
    """워크스페이스 기능(feature) 설정을 변경한다."""
    if not ctx.workspace:
        raise click.UsageError(
            "워크스페이스 슬러그가 필요합니다. --workspace 옵션 또는 PLANE_WORKSPACE_SLUG 환경변수를 설정하세요."
        )

    # 변경할 값이 하나도 없으면 에러
    provided = {
        "project_grouping": project_grouping,
        "initiatives": initiatives,
        "teams": teams,
        "customers": customers,
        "wiki": wiki,
        "pi": pi,
    }
    updates = {k: v for k, v in provided.items() if v is not None}
    if not updates:
        raise click.UsageError(
            "변경할 기능 옵션을 하나 이상 지정하세요. (예: --wiki true)"
        )

    # 현재 설정을 기반으로 변경 사항 병합
    from plane.models.workspaces import WorkspaceFeature

    current = ctx.client.workspaces.get_features(workspace_slug=ctx.workspace)
    current_data = current.model_dump()
    current_data.update(updates)

    data = WorkspaceFeature(**current_data)
    result = ctx.client.workspaces.update_features(workspace_slug=ctx.workspace, data=data)
    format_output(result, ctx.output)
