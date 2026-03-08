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
    """oh-my-kanban - 경량 프로젝트 관리 CLI.

    커맨드 구조:
      omk plane <command>   Plane 프로젝트 관리 (pl은 단축 alias)
      omk github <command>  GitHub 프로젝트 관리 (gh는 단축 alias)
      omk config <command>  설정 관리 (provider 독립)

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
    # config는 최상위 유지 (provider 독립적)
    from oh_my_kanban.commands.config_cmd import config
    cli.add_command(config)

    # ── GitHub 커맨드 그룹 ─────────────────────────────────────────────
    from oh_my_kanban.commands.github_stub import github
    cli.add_command(github, name="github")
    cli.add_command(github, name="gh")  # alias

    # ── Plane 커맨드 그룹 ─────────────────────────────────────────────
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

    # plane 서브그룹 생성
    plane = click.Group(
        "plane",
        help="Plane 프로젝트 관리 (Work Items, Cycles, Modules 등).\n\n'pl'은 'plane'의 단축 alias입니다.",
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

    cli.add_command(plane, name="plane")
    cli.add_command(plane, name="pl")  # alias

    # ── Linear 커맨드 그룹 ────────────────────────────────────────────
    from oh_my_kanban.commands.linear import linear
    cli.add_command(linear, name="linear")
    cli.add_command(linear, name="ln")  # alias

    # ── Project 커맨드 그룹 ───────────────────────────────────────────
    from oh_my_kanban.commands.project_cmd import project_cmd
    cli.add_command(project_cmd, name="project")

    # ── Hooks 커맨드 그룹 ─────────────────────────────────────────────
    from oh_my_kanban.commands.hooks import hooks
    cli.add_command(hooks)

    # ── MCP 커맨드 그룹 ───────────────────────────────────────────────
    from oh_my_kanban.commands.mcp_cmd import mcp_group
    cli.add_command(mcp_group, name="mcp")

    # ── Doctor 커맨드 ───────────────────────────────────────────────
    from oh_my_kanban.commands.doctor import doctor
    cli.add_command(doctor)


_register_commands()
