"""사용자 관련 커맨드."""

from __future__ import annotations

import click

from oh_my_kanban.providers.plane.context import PlaneContext as CliContext
from oh_my_kanban.providers.plane.errors import handle_api_error
from oh_my_kanban.output import format_output

# 사용자 정보 출력 컬럼
_USER_COLUMNS = ["id", "display_name", "email"]


@click.group()
def user() -> None:
    """사용자 관리."""
    pass


@user.command("me")
@click.pass_obj
@handle_api_error
def user_me(ctx: CliContext) -> None:
    """현재 로그인한 사용자 정보를 조회한다."""
    result = ctx.client.users.get_me()
    format_output(result, ctx.output, columns=_USER_COLUMNS)
