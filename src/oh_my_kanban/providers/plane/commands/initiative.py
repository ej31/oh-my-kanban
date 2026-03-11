"""이니셔티브(Initiative) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.initiatives import CreateInitiative, UpdateInitiative

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint
from oh_my_kanban.utils import confirm_delete, fetch_all_pages

# 이니셔티브 출력 컬럼
_COLUMNS = ["id", "name", "state", "start_date", "end_date", "lead"]

# 레이블 출력 컬럼
_LABEL_COLUMNS = ["id", "name", "color"]

# 에픽 출력 컬럼
_EPIC_COLUMNS = ["id", "name", "priority", "state"]

# 프로젝트 출력 컬럼
_PROJECT_COLUMNS = ["id", "name", "identifier"]


@click.group()
def initiative() -> None:
    """이니셔티브 관리 (워크스페이스 수준)."""
    pass


@initiative.command("list")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def initiative_list(ctx: CliContext, per_page: int, fetch_all: bool) -> None:
    """이니셔티브 목록 조회."""
    ws = ctx.workspace

    if fetch_all:
        results = fetch_all_pages(
            ctx.client.initiatives.list,
            ws,
            per_page=per_page,
        )
        format_output(results, ctx.output, columns=_COLUMNS)
    else:
        response = ctx.client.initiatives.list(ws, params={"per_page": per_page})
        format_output(response.results, ctx.output, columns=_COLUMNS)
        format_pagination_hint(response, ctx.output)


@initiative.command("get")
@click.argument("initiative_id")
@click.pass_obj
@handle_api_error
def initiative_get(ctx: CliContext, initiative_id: str) -> None:
    """이니셔티브 상세 조회."""
    result = ctx.client.initiatives.retrieve(ctx.workspace, initiative_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@initiative.command("create")
@click.option("--name", required=True, help="이니셔티브 이름")
@click.option("--description", default=None, help="설명 (HTML)")
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="종료 날짜 (YYYY-MM-DD)")
@click.option("--state", default=None, help="상태")
@click.option("--lead", default=None, help="담당자 UUID")
@click.pass_obj
@handle_api_error
def initiative_create(
    ctx: CliContext,
    name: str,
    description: str | None,
    start_date: str | None,
    end_date: str | None,
    state: str | None,
    lead: str | None,
) -> None:
    """새 이니셔티브 생성."""
    data = CreateInitiative(
        name=name,
        description_html=description,
        start_date=start_date,
        end_date=end_date,
        state=state,
        lead=lead,
    )
    result = ctx.client.initiatives.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@initiative.command("update")
@click.argument("initiative_id")
@click.option("--name", default=None, help="이니셔티브 이름")
@click.option("--description", default=None, help="설명 (HTML)")
@click.option("--start-date", default=None, help="시작 날짜 (YYYY-MM-DD)")
@click.option("--end-date", default=None, help="종료 날짜 (YYYY-MM-DD)")
@click.option("--state", default=None, help="상태")
@click.option("--lead", default=None, help="담당자 UUID")
@click.pass_obj
@handle_api_error
def initiative_update(
    ctx: CliContext,
    initiative_id: str,
    name: str | None,
    description: str | None,
    start_date: str | None,
    end_date: str | None,
    state: str | None,
    lead: str | None,
) -> None:
    """이니셔티브 수정."""
    data = UpdateInitiative(
        name=name,
        description_html=description,
        start_date=start_date,
        end_date=end_date,
        state=state,
        lead=lead,
    )
    result = ctx.client.initiatives.update(ctx.workspace, initiative_id, data)
    format_output(result, ctx.output, columns=_COLUMNS)


@initiative.command("delete")
@click.argument("initiative_id")
@click.pass_obj
@handle_api_error
def initiative_delete(ctx: CliContext, initiative_id: str) -> None:
    """이니셔티브 삭제."""
    if not confirm_delete("이니셔티브", initiative_id):
        click.echo("삭제를 취소했습니다.", err=True)
        return

    ctx.client.initiatives.delete(ctx.workspace, initiative_id)
    click.echo(f"이니셔티브 '{initiative_id}'을(를) 삭제했습니다.")


# ── 에픽 서브그룹 ─────────────────────────────────────────────────────────

@initiative.group("epic")
def initiative_epic() -> None:
    """이니셔티브 에픽 관리."""
    pass


@initiative_epic.command("list")
@click.argument("initiative_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def initiative_epic_list(ctx: CliContext, initiative_id: str, per_page: int) -> None:
    """이니셔티브에 연결된 에픽 목록 조회."""
    response = ctx.client.initiatives.epics.list(
        ctx.workspace, initiative_id, params={"per_page": per_page}
    )
    format_output(response.results, ctx.output, columns=_EPIC_COLUMNS)
    format_pagination_hint(response, ctx.output)


@initiative_epic.command("add")
@click.argument("initiative_id")
@click.option(
    "--epic-ids",
    multiple=True,
    required=True,
    help="추가할 에픽 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_epic_add(
    ctx: CliContext, initiative_id: str, epic_ids: tuple[str, ...]
) -> None:
    """이니셔티브에 에픽을 추가한다."""
    ctx.client.initiatives.epics.add(ctx.workspace, initiative_id, epic_ids=list(epic_ids))
    click.echo(f"에픽 {len(epic_ids)}개를 이니셔티브 '{initiative_id}'에 추가했습니다.")


@initiative_epic.command("remove")
@click.argument("initiative_id")
@click.option(
    "--epic-ids",
    multiple=True,
    required=True,
    help="제거할 에픽 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_epic_remove(
    ctx: CliContext, initiative_id: str, epic_ids: tuple[str, ...]
) -> None:
    """이니셔티브에서 에픽을 제거한다."""
    ctx.client.initiatives.epics.remove(ctx.workspace, initiative_id, epic_ids=list(epic_ids))
    click.echo(f"에픽 {len(epic_ids)}개를 이니셔티브 '{initiative_id}'에서 제거했습니다.")


# ── 레이블 서브그룹 ───────────────────────────────────────────────────────

@initiative.group("label")
def initiative_label() -> None:
    """이니셔티브 레이블 관리."""
    pass


@initiative_label.command("list")
@click.argument("initiative_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def initiative_label_list(ctx: CliContext, initiative_id: str, per_page: int) -> None:
    """이니셔티브에 연결된 레이블 목록 조회."""
    response = ctx.client.initiatives.labels.list_labels(
        ctx.workspace, initiative_id, params={"per_page": per_page}
    )
    format_output(response.results, ctx.output, columns=_LABEL_COLUMNS)
    format_pagination_hint(response, ctx.output)


@initiative_label.command("add")
@click.argument("initiative_id")
@click.option(
    "--label-ids",
    multiple=True,
    required=True,
    help="추가할 레이블 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_label_add(
    ctx: CliContext, initiative_id: str, label_ids: tuple[str, ...]
) -> None:
    """이니셔티브에 레이블을 추가한다."""
    ctx.client.initiatives.labels.add_labels(
        ctx.workspace, initiative_id, label_ids=list(label_ids)
    )
    click.echo(f"레이블 {len(label_ids)}개를 이니셔티브 '{initiative_id}'에 추가했습니다.")


@initiative_label.command("remove")
@click.argument("initiative_id")
@click.option(
    "--label-ids",
    multiple=True,
    required=True,
    help="제거할 레이블 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_label_remove(
    ctx: CliContext, initiative_id: str, label_ids: tuple[str, ...]
) -> None:
    """이니셔티브에서 레이블을 제거한다."""
    ctx.client.initiatives.labels.remove_labels(
        ctx.workspace, initiative_id, label_ids=list(label_ids)
    )
    click.echo(f"레이블 {len(label_ids)}개를 이니셔티브 '{initiative_id}'에서 제거했습니다.")


# ── 프로젝트 서브그룹 ─────────────────────────────────────────────────────

@initiative.group("project")
def initiative_project() -> None:
    """이니셔티브 프로젝트 관리."""
    pass


@initiative_project.command("list")
@click.argument("initiative_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.pass_obj
@handle_api_error
def initiative_project_list(ctx: CliContext, initiative_id: str, per_page: int) -> None:
    """이니셔티브에 연결된 프로젝트 목록 조회."""
    response = ctx.client.initiatives.projects.list(
        ctx.workspace, initiative_id, params={"per_page": per_page}
    )
    format_output(response.results, ctx.output, columns=_PROJECT_COLUMNS)
    format_pagination_hint(response, ctx.output)


@initiative_project.command("add")
@click.argument("initiative_id")
@click.option(
    "--project-ids",
    multiple=True,
    required=True,
    help="추가할 프로젝트 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_project_add(
    ctx: CliContext, initiative_id: str, project_ids: tuple[str, ...]
) -> None:
    """이니셔티브에 프로젝트를 추가한다."""
    ctx.client.initiatives.projects.add(
        ctx.workspace, initiative_id, project_ids=list(project_ids)
    )
    click.echo(f"프로젝트 {len(project_ids)}개를 이니셔티브 '{initiative_id}'에 추가했습니다.")


@initiative_project.command("remove")
@click.argument("initiative_id")
@click.option(
    "--project-ids",
    multiple=True,
    required=True,
    help="제거할 프로젝트 UUID (여러 개 지정 가능)",
)
@click.pass_obj
@handle_api_error
def initiative_project_remove(
    ctx: CliContext, initiative_id: str, project_ids: tuple[str, ...]
) -> None:
    """이니셔티브에서 프로젝트를 제거한다."""
    ctx.client.initiatives.projects.remove(
        ctx.workspace, initiative_id, project_ids=list(project_ids)
    )
    click.echo(f"프로젝트 {len(project_ids)}개를 이니셔티브 '{initiative_id}'에서 제거했습니다.")
