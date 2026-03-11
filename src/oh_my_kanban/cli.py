"""최상위 CLI 엔트리포인트."""

from __future__ import annotations

import click

from oh_my_kanban.core.app_context import AppContext
from oh_my_kanban.core.provider_registry import iter_provider_specs
from oh_my_kanban.config import load_config

@click.group()
@click.version_option(package_name="oh-my-kanban")
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
    output: str | None,
    profile: str,
) -> None:
    """oh-my-kanban - 경량 프로젝트 관리 CLI.

    커맨드 구조:
      omk plane <command>   Plane 프로젝트 관리 (pl은 단축 alias)
      omk linear <command>  Linear 프로젝트 관리 (ln은 단축 alias)
      omk config <command>  설정 관리 (provider 독립)
    """
    cfg = load_config(profile)
    final_output = output or cfg.output or "table"
    ctx.obj = AppContext(profile=profile, output=final_output, config=cfg)


# ── 커맨드 그룹 등록 ──────────────────────────────────────────────────────
def _register_commands() -> None:
    # config는 최상위 유지 (provider 독립적)
    from oh_my_kanban.commands.config_cmd import config
    cli.add_command(config, name="config")

    for provider in iter_provider_specs():
        cli.add_command(provider.command, name=provider.name)
        for alias in provider.aliases:
            cli.add_command(provider.command, name=alias)


_register_commands()
