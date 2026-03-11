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
    """oh-my-kanban unified CLI for Plane and Linear.

    Root-only options:
      --output   default output format
      --profile  config profile to load

    Command discovery order:
      1. omk config --help
      2. omk plane --help
      3. omk linear --help

    Provider-specific options live under each provider group.
    Example: omk plane --workspace MY_WORKSPACE --project PROJECT_UUID ...
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
