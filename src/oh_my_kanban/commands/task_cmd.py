"""omk task 커맨드 그룹: 현재 세션 Task 조회."""

from __future__ import annotations

import click

from oh_my_kanban.session.manager import list_sessions
from oh_my_kanban.session.state import STATUS_ACTIVE


@click.group("task")
def task_cmd() -> None:
    """현재 세션 Task(Work Item) 조회."""


@task_cmd.command("list")
def task_list() -> None:
    """현재 활성 세션에 연결된 Task 목록을 출력한다."""
    sessions = [s for s in list_sessions() if s.status == STATUS_ACTIVE]
    if not sessions:
        click.echo("활성 세션이 없습니다.")
        return

    for state in sessions:
        ctx = state.plane_context
        click.echo(f"\n세션: {state.session_id}")
        click.echo(f"project: {ctx.project_id or '(없음)'}")

        auto_task_id = ctx.auto_created_task_id
        if auto_task_id:
            click.echo(f"Main Task (auto): {auto_task_id}")

        if ctx.work_item_ids:
            click.echo("Work Items:")
            for wi_id in ctx.work_item_ids:
                marker = " [focused]" if wi_id == ctx.focused_work_item_id else ""
                click.echo(f"  - {wi_id}{marker}")
        else:
            click.echo("  (등록된 Work Item 없음)")


@task_cmd.command("show")
def task_show() -> None:
    """현재 집중 Task(focused WI)의 정보를 출력한다."""
    sessions = [s for s in list_sessions() if s.status == STATUS_ACTIVE]
    if not sessions:
        click.echo("활성 세션이 없습니다.")
        return

    # updated_at 기준으로 가장 최근 세션 선택
    state = max(sessions, key=lambda s: s.updated_at or "")
    ctx = state.plane_context
    click.echo(f"세션: {state.session_id}")
    click.echo(f"project: {ctx.project_id or '(없음)'}")

    auto_task_id = ctx.auto_created_task_id

    if ctx.focused_work_item_id:
        click.echo(f"focused WI: {ctx.focused_work_item_id}")
        if auto_task_id:
            click.echo(f"Main Task:  {auto_task_id}")
    else:
        click.echo("현재 집중 중인 Task가 없습니다.")
