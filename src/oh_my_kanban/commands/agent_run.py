"""에이전트 실행(Agent Run) 관련 커맨드."""

from __future__ import annotations

import click
from plane.models.agent_runs import CreateAgentRun

from oh_my_kanban.context import CliContext
from oh_my_kanban.errors import handle_api_error
from oh_my_kanban.output import format_output, format_pagination_hint

# 에이전트 실행 출력 컬럼
_COLUMNS = ["id", "status", "type", "started_at", "ended_at", "agent_user"]

# 활동 출력 컬럼
_ACTIVITY_COLUMNS = ["id", "type", "signal", "ephemeral", "created_at"]


@click.group()
def agent_run() -> None:
    """에이전트 실행 관리 (워크스페이스 수준)."""
    pass


@agent_run.command("get")
@click.argument("run_id")
@click.pass_obj
@handle_api_error
def agent_run_get(ctx: CliContext, run_id: str) -> None:
    """에이전트 실행 상세 조회."""
    result = ctx.client.agent_runs.retrieve(ctx.workspace, run_id)
    format_output(result, ctx.output, columns=_COLUMNS)


@agent_run.command("create")
@click.option("--agent-slug", required=True, help="에이전트 슬러그")
@click.option("--issue", default=None, help="연결할 이슈 UUID")
@click.option("--project", default=None, help="프로젝트 UUID")
@click.option("--comment", default=None, help="초기 댓글 내용")
@click.option("--external-link", default=None, help="외부 링크 URL")
@click.pass_obj
@handle_api_error
def agent_run_create(
    ctx: CliContext,
    agent_slug: str,
    issue: str | None,
    project: str | None,
    comment: str | None,
    external_link: str | None,
) -> None:
    """새 에이전트 실행 생성."""
    data = CreateAgentRun(
        agent_slug=agent_slug,
        issue=issue,
        project=project,
        comment=comment,
        external_link=external_link,
    )
    result = ctx.client.agent_runs.create(ctx.workspace, data)
    format_output(result, ctx.output, columns=_COLUMNS)


# ── 활동 서브그룹 ─────────────────────────────────────────────────────────

@agent_run.group("activity")
def agent_run_activity() -> None:
    """에이전트 실행 활동 관리."""
    pass


@agent_run_activity.command("list")
@click.argument("run_id")
@click.option("--per-page", default=50, show_default=True, help="페이지당 항목 수")
@click.option("--all", "fetch_all", is_flag=True, default=False, help="모든 페이지 조회")
@click.pass_obj
@handle_api_error
def activity_list(ctx: CliContext, run_id: str, per_page: int, fetch_all: bool) -> None:
    """에이전트 실행의 활동 목록 조회."""
    if fetch_all:
        # SDK activities.list()는 params dict를 받으므로 fetch_all_pages 대신 직접 순회한다.
        all_results = []
        cursor = None
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
            params: dict = {"per_page": per_page}
            if cursor:
                params["cursor"] = cursor
            response = ctx.client.agent_runs.activities.list(ctx.workspace, run_id, params=params)
            all_results.extend(getattr(response, "results", []))
            if not getattr(response, "next_page_results", False):
                break
            cursor = getattr(response, "next_cursor", None)
            if not cursor:
                break
        format_output(all_results, ctx.output, columns=_ACTIVITY_COLUMNS)
    else:
        response = ctx.client.agent_runs.activities.list(
            ctx.workspace, run_id, params={"per_page": per_page}
        )
        format_output(response.results, ctx.output, columns=_ACTIVITY_COLUMNS)
        format_pagination_hint(response, ctx.output)
