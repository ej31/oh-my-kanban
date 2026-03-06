"""Linear 프로바이더 커맨드 그룹."""
from __future__ import annotations

import click

from oh_my_kanban.config import load_config
from oh_my_kanban.linear_context import LinearContext

from .cycle import cycle
from .issue import issue as _issue_cmd
from .label import label
from .me import me
from .project import project
from .state import state
from .team import team


@click.group()
@click.pass_context
def linear(ctx: click.Context) -> None:
    """Linear 프로젝트 관리."""
    parent_obj = ctx.obj
    output = parent_obj.output if parent_obj else "table"
    cfg = load_config()
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
