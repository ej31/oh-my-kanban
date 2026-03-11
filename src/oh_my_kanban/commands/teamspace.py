"""팀스페이스(Teamspace) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.teamspaces import CreateTeamspace, UpdateTeamspace

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 팀스페이스 출력 컬럼
_COLUMNS = ["id", "name", "lead", "workspace"]

# 멤버 출력 컬럼
_MEMBER_COLUMNS = ["id", "display_name", "email"]

# 프로젝트 출력 컬럼
_PROJECT_COLUMNS = ["id", "name", "identifier"]


@click.group()
def teamspace() -> None:
    """팀스페이스 관리 (워크스페이스 수준)."""
    pass


@teamspace.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def teamspace_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """팀스페이스 목록 조회."""
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.teamspaces.list,
            ws,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_COLUMNS)
    else:
        response = ctx.client.teamspaces.list(ws, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@teamspace.command("get")
@click.argument("teamspace_id")
@click.pass_obj
@handle_api_error
def teamspace_get(ctx: CliContext, teamspace_id: str) -> None:
    """팀스페이스 상세 조회."""
    result = ctx.client.teamspaces.retrieve(ctx.workspace, teamspace_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@teamspace.command("create")
@click.option("--name", required=True, help="팀스페이스 이름")
@click.option("--description", default=None, help="설명 (HTML)")
@click.option("--lead", default=None, help="담당자 UUID")
@click.pass_obj
@handle_api_error
def teamspace_create(
    ctx: CliContext,
    name: str,
    description: str | None,
    lead: str | None,
) -> None:
    """새 팀스페이스 생성."""
    data = CreateTeamspace(
        name=name,
        description_html=description,
        lead=lead,
    )
    result = ctx.client.teamspaces.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@teamspace.command("update")
@click.argument("teamspace_id")
@click.option("--name", default=None, help="팀스페이스 이름")
@click.option("--description", default=None, help="설명 (HTML)")
@click.option("--lead", default=None, help="담당자 UUID")
@click.pass_obj
@handle_api_error
def teamspace_update(
    ctx: CliContext,
    teamspace_id: str,
    name: str | None,
    description: str | None,
    lead: str | None,
) -> None:
    """팀스페이스 수정."""
    data = UpdateTeamspace(
        name=name,
        description_html=description,
        lead=lead,
    )
    result = ctx.client.teamspaces.update(ctx.workspace, teamspace_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@teamspace.command("delete")
@click.argument("teamspace_id")
@click.pass_obj
@handle_api_error
def teamspace_delete(ctx: CliContext, teamspace_id: str) -> None:
    """팀스페이스 삭제."""
    if not confirm_delete("팀스페이스", teamspace_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.teamspaces.delete(ctx.workspace, teamspace_id)
    click.echo(f"팀스페이스 '{teamspace_id}'을(를) 삭제했습니다.")


# ── 멤버 서브그룹 ─────────────────────────────────────────────────────────

@teamspace.group("member")
def teamspace_member() -> None:
    """팀스페이스 멤버 관리."""
    pass


@teamspace_member.command("list")
@click.argument("teamspace_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def teamspace_member_list(ctx: CliContext, teamspace_id: str, per_page: int) -> None:
    """팀스페이스 멤버 목록 조회."""
    response = ctx.client.teamspaces.members.list(
        ctx.workspace, teamspace_id, params={"per_page": per_page}
    )
    format_output(response.results, ctx.output, columns=_MEMBER_COLUMNS)
    format_pagination_hint(response, ctx.output)


@teamspace_member.command("add")
@click.argument("teamspace_id")
@click.option(
    "--member-ids",
    multiple=True,
    required=True,
    help="추가할 멤버 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def teamspace_member_add(
    ctx: CliContext, teamspace_id: str, member_ids: tuple[str, ...]
) -> None:
    """팀스페이스에 멤버를 추가한다."""
    ctx.client.teamspaces.members.add(
        ctx.workspace, teamspace_id, member_ids=list(member_ids)
    )
    click.echo(f"멤버 {len(member_ids)}명을 팀스페이스 '{teamspace_id}'에 추가했습니다.")


@teamspace_member.command("remove")
@click.argument("teamspace_id")
@click.option(
    "--member-ids",
    multiple=True,
    required=True,
    help="제거할 멤버 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def teamspace_member_remove(
    ctx: CliContext, teamspace_id: str, member_ids: tuple[str, ...]
) -> None:
    """팀스페이스에서 멤버를 제거한다."""
    ctx.client.teamspaces.members.remove(
        ctx.workspace, teamspace_id, member_ids=list(member_ids)
    )
    click.echo(f"멤버 {len(member_ids)}명을 팀스페이스 '{teamspace_id}'에서 제거했습니다.")


# ── 프로젝트 서브그룹 ─────────────────────────────────────────────────────

@teamspace.group("project")
def teamspace_project() -> None:
    """팀스페이스 프로젝트 관리."""
    pass


@teamspace_project.command("list")
@click.argument("teamspace_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def teamspace_project_list(ctx: CliContext, teamspace_id: str, per_page: int) -> None:
    """팀스페이스에 연결된 프로젝트 목록 조회."""
    response = ctx.client.teamspaces.projects.list(
        ctx.workspace, teamspace_id, params={"per_page": per_page}
    )
    format_output(response.results, ctx.output, columns=_PROJECT_COLUMNS)
    format_pagination_hint(response, ctx.output)


@teamspace_project.command("add")
@click.argument("teamspace_id")
@click.option(
    "--project-ids",
    multiple=True,
    required=True,
    help="추가할 프로젝트 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def teamspace_project_add(
    ctx: CliContext, teamspace_id: str, project_ids: tuple[str, ...]
) -> None:
    """팀스페이스에 프로젝트를 추가한다."""
    ctx.client.teamspaces.projects.add(
        ctx.workspace, teamspace_id, project_ids=list(project_ids)
    )
    click.echo(f"프로젝트 {len(project_ids)}개를 팀스페이스 '{teamspace_id}'에 추가했습니다.")


@teamspace_project.command("remove")
@click.argument("teamspace_id")
@click.option(
    "--project-ids",
    multiple=True,
    required=True,
    help="제거할 프로젝트 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def teamspace_project_remove(
    ctx: CliContext, teamspace_id: str, project_ids: tuple[str, ...]
) -> None:
    """팀스페이스에서 프로젝트를 제거한다."""
    ctx.client.teamspaces.projects.remove(
        ctx.workspace, teamspace_id, project_ids=list(project_ids)
    )
    click.echo(f"프로젝트 {len(project_ids)}개를 팀스페이스 '{teamspace_id}'에서 제거했습니다.")
