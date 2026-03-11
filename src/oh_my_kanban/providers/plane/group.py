"""Plane provider group."""

from __future__ import annotations

import click

from oh_my_kanban.commands.agent_run import agent_run
from oh_my_kanban.commands.customer import customer
from oh_my_kanban.commands.cycle import cycle
from oh_my_kanban.commands.epic import epic
from oh_my_kanban.commands.initiative import initiative
from oh_my_kanban.commands.intake import intake
from oh_my_kanban.commands.label import label
from oh_my_kanban.commands.milestone import milestone
from oh_my_kanban.commands.module import module
from oh_my_kanban.commands.page import page
from oh_my_kanban.commands.project import project
from oh_my_kanban.commands.state import state
from oh_my_kanban.commands.sticky import sticky
from oh_my_kanban.commands.teamspace import teamspace
from oh_my_kanban.commands.user import user
from oh_my_kanban.commands.work_item import work_item
from oh_my_kanban.commands.work_item_property import work_item_property
from oh_my_kanban.commands.work_item_type import work_item_type
from oh_my_kanban.commands.workspace import workspace
from oh_my_kanban.config import load_config
from oh_my_kanban.core.app_context import AppContext

from .context import PlaneContext


@click.group(
    "plane",
    help="Plane 프로젝트 관리 (Work Items, Cycles, Modules 등).\n\n'pl'은 'plane'의 단축 alias입니다.",
)
@click.option("--workspace", "-w", envvar="PLANE_WORKSPACE_SLUG", default=None, help="워크스페이스 슬러그")
@click.option("--project", "-p", envvar="PLANE_PROJECT_ID", default=None, help="프로젝트 UUID")
@click.pass_context
def plane(ctx: click.Context, workspace: str | None, project: str | None) -> None:
    """Bind provider-neutral app context to Plane-specific context."""

    parent_obj = ctx.obj
    if isinstance(parent_obj, AppContext):
        cfg = parent_obj.config
        output = parent_obj.output
    else:
        cfg = load_config()
        output = cfg.output or "table"

    ctx.obj = PlaneContext(
        _base_url=cfg.base_url,
        _api_key=cfg.api_key,
        workspace=workspace or cfg.workspace_slug,
        project=project or cfg.project_id,
        output=output,
    )


plane.add_command(user)
plane.add_command(workspace)
plane.add_command(project)
plane.add_command(state)
plane.add_command(label)
plane.add_command(work_item, name="work-item")
plane.add_command(cycle)
plane.add_command(module)
plane.add_command(milestone)
plane.add_command(epic)
plane.add_command(page)
plane.add_command(intake)
plane.add_command(initiative)
plane.add_command(teamspace)
plane.add_command(customer)
plane.add_command(work_item_type, name="work-item-type")
plane.add_command(work_item_property, name="work-item-property")
plane.add_command(agent_run, name="agent-run")
plane.add_command(sticky)

