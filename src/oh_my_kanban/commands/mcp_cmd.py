"""omk mcp 커맨드 그룹: MCP 서버 실행 및 설정 안내."""

from __future__ import annotations

import sys

import click


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
