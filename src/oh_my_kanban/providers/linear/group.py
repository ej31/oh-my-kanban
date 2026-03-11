"""Linear provider group."""

from __future__ import annotations

import click

from oh_my_kanban.config import load_config
from oh_my_kanban.core.app_context import AppContext

from .commands.cycle import cycle
from .commands.issue import issue as _issue_cmd
from .commands.label import label
from .commands.me import me
from .commands.project import project
from .commands.state import state
from .commands.team import team
from .context import LinearContext


@click.group("linear")
@click.pass_context
def linear(ctx: click.Context) -> None:
    """Linear 프로젝트 관리."""

    parent_obj = ctx.obj
    if isinstance(parent_obj, AppContext):
        cfg = parent_obj.config
        output = parent_obj.output
    else:
        cfg = load_config()
        output = cfg.output or "table"

    ctx.obj = LinearContext(
        _api_key=cfg.linear_api_key,
        team_id=cfg.linear_team_id,
        output=output,
    )


linear.add_command(me)
linear.add_command(team)
linear.add_command(state)
linear.add_command(label)
linear.add_command(project)
linear.add_command(cycle)
linear.add_command(_issue_cmd)

__all__ = ["linear"]
