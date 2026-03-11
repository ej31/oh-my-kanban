"""Linear 현재 사용자 조회 커맨드."""
from __future__ import annotations

import click

from oh_my_kanban.providers.linear.context import LinearContext
from oh_my_kanban.providers.linear.errors import handle_linear_error
from oh_my_kanban.output import format_output

_VIEWER_QUERY = """
{ viewer { id name email } }
"""


@click.command("me")
@click.pass_obj
@handle_linear_error
def me(ctx: LinearContext) -> None:
    """현재 Linear 사용자 정보를 조회한다."""
    data = ctx.client.execute(_VIEWER_QUERY)
    format_output(data.get("viewer", {}), ctx.output)
