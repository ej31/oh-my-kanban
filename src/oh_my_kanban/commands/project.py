"""프로젝트 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.projects import CreateProject, ProjectFeature, UpdateProject

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint

# 출력 컬럼 정의
_LIST_COLUMNS = ["id", "name", "identifier", "network", "total_members"]
_GET_COLUMNS = ["id", "name", "identifier", "description", "timezone", "created_at"]
_MEMBER_COLUMNS = ["id", "display_name", "email"]
_FEATURE_COLUMNS = ["epics", "modules", "cycles", "views", "pages", "intakes", "work_item_types"]
_WORKLOG_COLUMNS = ["issue_id", "duration"]


@click.group()
def project() -> None:
    """프로젝트 관리."""
    pass


@project.command("list")
@click.option("--per-page", type=int, default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, help="모든 페이지 가져오기")
@click.pass_obj
@handle_api_error
def project_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """프로젝트 목록 조회."""
    ws = ctx.require_workspace()

    if fetch_all:
        # projects.list()는 params=PaginatedQueryParams 방식만 지원하므로 직접 순회한다.
        from plane.models.query_params import PaginatedQueryParams

        all_results = []
        cursor: str | None = None
        page_count = 0
        max_pages = 500
        while True:
            page_count += 1
            if page_count > max_pages:
                click.echo(
                    f"경고: 최대 페이지 수({max_pages})에 도달했습니다. 결과가 잘렸을 수 있습니다.",
                    err=True,
                )
                break
            kw: dict = {"per_page": per_page}
            if cursor:
                kw["cursor"] = cursor
            response = ctx.client.projects.list(ws, params=PaginatedQueryParams(**kw))
            all_results.extend(response.results or [])
            if not getattr(response, "next_page_results", False):
                break
            cursor = getattr(response, "next_cursor", None)
            if not cursor:
                break
        format_output(all_results, ctx.output, columns=_LIST_COLUMNS)
    else:
        from plane.models.query_params import PaginatedQueryParams

        response = ctx.client.projects.list(
            ws, params=PaginatedQueryParams(per_page=per_page)
        )
        format_output(response.results, ctx.output, columns=_LIST_COLUMNS)
        format_pagination_hint(response, ctx.output)


@project.command("get")
@click.argument("project_id")
@click.pass_obj
@handle_api_error
def project_get(ctx: CliContext, project_id: str) -> None:
    """프로젝트 상세 조회."""
    ws = ctx.require_workspace()

    result = ctx.client.projects.retrieve(ws, project_id)
    format_output(result, ctx.output, columns=_GET_COLUMNS)


@project.command("create")
@click.option("--name", required=True, help="프로젝트 이름 (plane.so 클라우드에서는 하이픈 등 특수문자 불가)")
@click.option("--identifier", required=True, help="프로젝트 식별자 (대문자, 예: PROJ)")
@click.option("--description", default=None, help="프로젝트 설명")
@click.option("--timezone", default=None, help="타임존 (예: Asia/Seoul)")
@click.pass_obj
@handle_api_error
def project_create(
    ctx: CliContext,
    name: str,
    identifier: str,
    description: str | None,
    timezone: str | None,
) -> None:
    """새 프로젝트 생성.

    \b
    참고: plane.so 클라우드의 경우 프로젝트 이름에 하이픈(-) 등
    특수문자가 포함되면 서버가 거부할 수 있습니다.
    """
    ws = ctx.require_workspace()

    data = CreateProject(
        name=name,
        identifier=identifier,
        description=description,
        timezone=timezone,
    )
    result = ctx.client.projects.create(ws, data=data)
    format_output(result, ctx.output, columns=_GET_COLUMNS)


@project.command("update")
@click.argument("project_id")
@click.option("--name", default=None, help="새 프로젝트 이름")
@click.option("--description", default=None, help="새 프로젝트 설명")
@click.pass_obj
@handle_api_error
def project_update(
    ctx: CliContext,
    project_id: str,
    name: str | None,
    description: str | None,
) -> None:
    """프로젝트 수정."""
    ws = ctx.require_workspace()

    data = UpdateProject(name=name, description=description)
    result = ctx.client.projects.update(ws, project_id, data=data)
    format_output(result, ctx.output, columns=_GET_COLUMNS)


@project.command("delete")
@click.argument("project_id")
@click.pass_obj
@handle_api_error
def project_delete(ctx: CliContext, project_id: str) -> None:
    """프로젝트 삭제."""
    ws = ctx.require_workspace()

    if not click.confirm(f"프로젝트 '{project_id}'를 삭제하시겠습니까?"):
        raise click.Abort()

    ctx.client.projects.delete(ws, project_id)
    click.echo(f"프로젝트 '{project_id}'가 삭제되었습니다.")


@project.command("members")
@click.argument("project_id")
@click.pass_obj
@handle_api_error
def project_members(ctx: CliContext, project_id: str) -> None:
    """프로젝트 멤버 목록 조회."""
    ws = ctx.require_workspace()

    result = ctx.client.projects.get_members(ws, project_id)
    format_output(result, ctx.output, columns=_MEMBER_COLUMNS)


@project.command("features")
@click.argument("project_id")
@click.pass_obj
@handle_api_error
def project_features(ctx: CliContext, project_id: str) -> None:
    """프로젝트 기능 설정 조회."""
    ws = ctx.require_workspace()

    result = ctx.client.projects.get_features(ws, project_id)
    format_output(result, ctx.output, columns=_FEATURE_COLUMNS)


@project.command("update-features")
@click.argument("project_id")
@click.option("--epics/--no-epics", default=None, help="에픽 기능 활성화 여부")
@click.option("--modules/--no-modules", default=None, help="모듈 기능 활성화 여부")
@click.option("--cycles/--no-cycles", default=None, help="사이클 기능 활성화 여부")
@click.option("--views/--no-views", default=None, help="뷰 기능 활성화 여부")
@click.option("--pages/--no-pages", default=None, help="페이지 기능 활성화 여부")
@click.option("--intakes/--no-intakes", default=None, help="인테이크 기능 활성화 여부")
@click.option(
    "--work-item-types/--no-work-item-types", default=None, help="작업 항목 유형 기능 활성화 여부"
)
@click.pass_obj
@handle_api_error
def project_update_features(
    ctx: CliContext,
    project_id: str,
    epics: bool | None,
    modules: bool | None,
    cycles: bool | None,
    views: bool | None,
    pages: bool | None,
    intakes: bool | None,
    work_item_types: bool | None,
) -> None:
    """프로젝트 기능 설정 수정."""
    ws = ctx.require_workspace()

    data = ProjectFeature(
        epics=epics,
        modules=modules,
        cycles=cycles,
        views=views,
        pages=pages,
        intakes=intakes,
        work_item_types=work_item_types,
    )
    result = ctx.client.projects.update_features(ws, project_id, data=data)
    format_output(result, ctx.output, columns=_FEATURE_COLUMNS)


@project.command("worklog-summary")
@click.argument("project_id")
@click.pass_obj
@handle_api_error
def project_worklog_summary(ctx: CliContext, project_id: str) -> None:
    """프로젝트 워크로그 요약 조회."""
    ws = ctx.require_workspace()

    result = ctx.client.projects.get_worklog_summary(ws, project_id)
    format_output(result, ctx.output, columns=_WORKLOG_COLUMNS)
