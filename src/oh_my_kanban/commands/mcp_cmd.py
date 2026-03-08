"""omk mcp 커맨드 그룹: MCP 서버 실행/설치/제거 및 설정 안내."""

from __future__ import annotations

import json
import sys

import click

# MCP 서버 설정 상수
MCP_SERVER_KEY = "oh-my-kanban"
MCP_SERVER_CONFIG = {
    "command": "omk",
    "args": ["mcp", "serve"],
}


@click.group("mcp")
def mcp_group() -> None:
    """MCP(Model Context Protocol) 서버 관리."""


@mcp_group.command("serve")
def serve() -> None:
    """MCP 서버를 stdio 모드로 실행한다.

    Claude Code 또는 MCP 클라이언트에서 이 명령을 서버로 등록해 사용한다.

    설정 예시 (~/.claude/claude_desktop_config.json):

    \b
    {
      "mcpServers": {
        "oh-my-kanban": {
          "command": "/path/to/python",
          "args": ["-m", "oh_my_kanban.mcp.server"]
        }
      }
    }

    또는 omk 명령 직접 사용:

    \b
    {
      "mcpServers": {
        "oh-my-kanban": {
          "command": "omk",
          "args": ["mcp", "serve"]
        }
      }
    }
    """
    # mcp 패키지 설치 여부를 미리 확인해 명확한 에러를 낸다
    try:
        from oh_my_kanban.mcp.server import main
    except ImportError as e:
        raise click.ClickException(f"MCP 서버 임포트 실패: {e}") from e

    main()


def _install_mcp(local: bool, local_only: bool = False) -> None:
    """Claude Code settings 파일에 oh-my-kanban MCP 서버를 등록한다."""
    from oh_my_kanban.commands.hooks import _settings_path, _write_settings_atomic

    settings_path = _settings_path(local, local_only)

    # 기존 설정 로드
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise click.ClickException(
                f"settings.json 파싱 실패: {e}\n"
                f"수동으로 확인 후 재시도하세요: {settings_path}"
            ) from e
    else:
        existing = {}

    # mcpServers에 oh-my-kanban 등록 (기존 항목 보존, 원본 mutation 방지)
    mcp_servers = {**existing.get("mcpServers", {}), MCP_SERVER_KEY: MCP_SERVER_CONFIG}
    settings = {**existing, "mcpServers": mcp_servers}

    _write_settings_atomic(settings_path, settings)
    click.echo(f"MCP 서버 등록 완료: {settings_path}")


def _uninstall_mcp(local: bool, local_only: bool = False) -> None:
    """Claude Code settings 파일에서 oh-my-kanban MCP 서버를 제거한다."""
    from oh_my_kanban.commands.hooks import _settings_path, _write_settings_atomic

    settings_path = _settings_path(local, local_only)
    if not settings_path.exists():
        click.echo(f"settings.json 없음: {settings_path}")
        return

    try:
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise click.ClickException(f"settings.json 파싱 실패: {e}") from e

    existing_mcp = existing.get("mcpServers", {})
    if MCP_SERVER_KEY not in existing_mcp:
        click.echo("oh-my-kanban MCP 서버가 등록되어 있지 않습니다.")
        return

    # 원본 mutation 방지 — oh-my-kanban만 제외한 새 dict 생성
    remaining = {k: v for k, v in existing_mcp.items() if k != MCP_SERVER_KEY}
    settings = {**existing}
    if remaining:
        settings["mcpServers"] = remaining
    else:
        settings.pop("mcpServers", None)

    _write_settings_atomic(settings_path, settings)
    click.echo(f"MCP 서버 제거 완료: {settings_path}")


@mcp_group.command("install")
@click.option(
    "--local",
    "local",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.json에 등록 (프로젝트 scope)",
)
@click.option(
    "--local-only",
    "local_only",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.local.json에 등록 (local scope)",
)
def install(local: bool, local_only: bool) -> None:
    """Claude Code에 oh-my-kanban MCP 서버를 등록한다."""
    if local and local_only:
        raise click.UsageError("--local과 --local-only는 동시에 사용할 수 없습니다.")
    _install_mcp(local, local_only)


@mcp_group.command("uninstall")
@click.option(
    "--local",
    "local",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.json에서 제거 (프로젝트 scope)",
)
@click.option(
    "--local-only",
    "local_only",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.local.json에서 제거 (local scope)",
)
def uninstall(local: bool, local_only: bool) -> None:
    """Claude Code에서 oh-my-kanban MCP 서버를 제거한다."""
    if local and local_only:
        raise click.UsageError("--local과 --local-only는 동시에 사용할 수 없습니다.")
    _uninstall_mcp(local, local_only)


@mcp_group.command("config")
def show_config() -> None:
    """Claude Code에 MCP 서버를 등록하는 설정 예시를 출력한다."""
    python_path = sys.executable

    click.echo("")
    click.echo("  oh-my-kanban MCP 서버 설정")
    click.echo("")
    click.echo("  ~/.claude/claude_desktop_config.json 에 아래 내용을 추가하세요:")
    click.echo("")
    click.echo('  {')
    click.echo('    "mcpServers": {')
    click.echo('      "oh-my-kanban": {')
    click.echo(f'        "command": "{python_path}",')
    click.echo('        "args": ["-m", "oh_my_kanban.mcp.server"]')
    click.echo('      }')
    click.echo('    }')
    click.echo('  }')
    click.echo("")
    click.echo("  또는 omk 명령을 직접 사용:")
    click.echo("")
    click.echo('  {')
    click.echo('    "mcpServers": {')
    click.echo('      "oh-my-kanban": {')
    click.echo('        "command": "omk",')
    click.echo('        "args": ["mcp", "serve"]')
    click.echo('      }')
    click.echo('    }')
    click.echo('  }')
    click.echo("")
    click.echo("  제공되는 MCP tools:")
    click.echo("    omk_get_session_status  — 현재 세션 상태 조회")
    click.echo("    omk_link_work_item      — Work Item ID를 세션에 연결")
    click.echo("    omk_update_scope        — 세션 범위 수동 업데이트")
    click.echo("    omk_get_timeline        — 세션 타임라인 조회")
    click.echo("    omk_add_comment         — Work Item에 댓글 즉시 추가")
    click.echo("")
