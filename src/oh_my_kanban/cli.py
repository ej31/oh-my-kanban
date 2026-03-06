"""최상위 CLI 엔트리포인트."""

from __future__ import annotations

import click

from oh_my_kanban.config import load_config
from oh_my_kanban.context import CliContext


@click.group()
@click.version_option(package_name="oh-my-kanban")
@click.option("--workspace", "-w", envvar="PLANE_WORKSPACE_SLUG", help="워크스페이스 슬러그")
@click.option("--project", "-p", envvar="PLANE_PROJECT_ID", help="프로젝트 UUID")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "plain"]),
    default=None,
    help="출력 포맷 (기본: table)",
)
@click.option("--profile", default="default", envvar="PLANE_PROFILE", help="설정 프로필")
@click.pass_context
def cli(
    ctx: click.Context,
    workspace: str | None,
    project: str | None,
    output: str | None,
    profile: str,
) -> None:
    """Plane CLI - 경량 프로젝트 관리 도구.

    환경변수: PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_PROJECT_ID, PLANE_BASE_URL
    """
    # 설정 로드 (TOML + env + CLAUDE.md)
    cfg = load_config(profile)

    # 명령행 옵션이 env/config보다 우선
    final_workspace = workspace or cfg.workspace_slug
    final_project = project or cfg.project_id
    final_output = output or cfg.output or "table"

    # 모든 경우에 동일하게 생성 (client는 lazy 초기화)
    ctx.obj = CliContext(
        _base_url=cfg.base_url,
        _api_key=cfg.api_key,
        workspace=final_workspace,
        project=final_project,
        output=final_output,
    )


# ── 커맨드 그룹 등록 ──────────────────────────────────────────────────────
def _register_commands() -> None:
    from oh_my_kanban.commands.agent_run import agent_run
    from oh_my_kanban.commands.config_cmd import config
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

    cli.add_command(config)
    cli.add_command(user)
    cli.add_command(workspace)
    cli.add_command(project)
    cli.add_command(state)
    cli.add_command(label)
    cli.add_command(work_item, name="work-item")
    cli.add_command(cycle)
    cli.add_command(module)
    cli.add_command(milestone)
    cli.add_command(epic)
    cli.add_command(page)
    cli.add_command(intake)
    cli.add_command(initiative)
    cli.add_command(teamspace)
    cli.add_command(customer)
    cli.add_command(work_item_type, name="work-item-type")
    cli.add_command(work_item_property, name="work-item-property")
    cli.add_command(agent_run, name="agent-run")
    cli.add_command(sticky)


_register_commands()
