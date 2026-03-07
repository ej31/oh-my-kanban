"""omk hooks 커맨드 그룹: Claude Code 훅 설치/제거/상태/opt-out."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from oh_my_kanban.session.manager import SESSIONS_DIR, list_sessions
from oh_my_kanban.session.state import (
    ACTIVE_SESSIONS_DISPLAY_MAX,
    SESSION_ID_DISPLAY_LEN,
    STATUS_ACTIVE,
    SUMMARY_SHORT_MAX,
)


# ── 훅 타임아웃 상수 (초 단위) ─────────────────────────────────────────────
HOOK_TIMEOUT_SESSION_START = 15
HOOK_TIMEOUT_PROMPT = 5
HOOK_TIMEOUT_POST_TOOL = 5
HOOK_TIMEOUT_SESSION_END = 30


# ── 내부 헬퍼 ──────────────────────────────────────────────────────────────

def _settings_path(local: bool, local_only: bool = False) -> Path:
    """대상에 따라 settings 파일 경로를 반환한다.

    local_only=True  → .claude/settings.local.json  (개인용, git 무시)
    local=True       → .claude/settings.json         (프로젝트 공유)
    둘 다 False      → ~/.claude/settings.json       (전역)
    """
    if local_only:
        return Path.cwd() / ".claude" / "settings.local.json"
    if local:
        return Path.cwd() / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def _build_omk_hooks_config(python_path: str, hooks_dir: Path) -> dict:
    """omk 훅 설정 블록을 생성한다. timeout은 초(seconds) 단위."""
    return {
        "SessionStart": [
            {
                "matcher": "startup|resume|compact",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            f'"{python_path}" '
                            f'"{hooks_dir / "session_start.py"}"'
                        ),
                        "timeout": HOOK_TIMEOUT_SESSION_START,
                        "statusMessage": "omk: 세션 맥락 로딩 중...",
                    }
                ],
            }
        ],
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            f'"{python_path}" '
                            f'"{hooks_dir / "user_prompt.py"}"'
                        ),
                        "timeout": HOOK_TIMEOUT_PROMPT,
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            f'"{python_path}" '
                            f'"{hooks_dir / "post_tool.py"}"'
                        ),
                        "timeout": HOOK_TIMEOUT_POST_TOOL,
                        "async": True,
                    }
                ],
            }
        ],
        "SessionEnd": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            f'"{python_path}" '
                            f'"{hooks_dir / "session_end.py"}"'
                        ),
                        "timeout": HOOK_TIMEOUT_SESSION_END,
                    }
                ]
            }
        ],
    }


def _is_omk_command(command: str) -> bool:
    """훅 명령이 oh_my_kanban 패키지 것인지 확인한다."""
    return "oh_my_kanban" in command


def _merge_hooks(
    existing_hooks: dict,
    omk_config: dict,
) -> dict:
    """기존 훅을 보존하면서 omk 훅만 교체한다 (idempotent)."""
    merged = dict(existing_hooks)
    for event, new_groups in omk_config.items():
        existing_groups = merged.get(event, [])
        # 기존 non-omk 훅 보존
        cleaned = []
        for group in existing_groups:
            non_omk_hooks = [
                h
                for h in group.get("hooks", [])
                if not _is_omk_command(h.get("command", ""))
            ]
            if non_omk_hooks:
                cleaned.append({**group, "hooks": non_omk_hooks})
        merged[event] = cleaned + new_groups
    return merged


def _remove_omk_hooks(existing_hooks: dict) -> dict:
    """기존 훅에서 omk 훅만 제거한다."""
    result = {}
    for event, groups in existing_hooks.items():
        cleaned = []
        for group in groups:
            non_omk_hooks = [
                h
                for h in group.get("hooks", [])
                if not _is_omk_command(h.get("command", ""))
            ]
            if non_omk_hooks:
                cleaned.append({**group, "hooks": non_omk_hooks})
        if cleaned:
            result[event] = cleaned
    return result


def _write_settings_atomic(settings_path: Path, settings: dict) -> None:
    """settings.json을 원자적으로 쓴다 (tmp → rename)."""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings_path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.rename(settings_path)
    except OSError as e:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise click.ClickException(f"settings.json 쓰기 실패: {e}") from e


def _install_hooks(local: bool, local_only: bool = False) -> None:
    """Claude Code settings 파일에 omk 훅을 등록한다."""
    python_path = sys.executable

    # hooks 패키지 디렉토리 탐색
    import oh_my_kanban.hooks as _hooks_pkg

    hooks_dir = Path(_hooks_pkg.__file__).parent

    # 경로에 큰따옴표가 포함되면 명령어 구성 시 이스케이프가 깨질 수 있으므로 차단
    if '"' in python_path or '"' in str(hooks_dir):
        raise click.ClickException(
            f"Python 경로 또는 훅 디렉토리 경로에 큰따옴표가 포함되어 있어 설치할 수 없습니다.\n"
            f"  Python: {python_path}\n"
            f"  훅 디렉토리: {hooks_dir}"
        )

    settings_path = _settings_path(local, local_only)

    # 기존 설정 로드
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise click.ClickException(
                f"기존 settings.json 파싱 실패: {e}\n"
                f"수동으로 확인 후 재시도하세요: {settings_path}"
            ) from e
        # 덮어쓰기 전 백업
        backup = settings_path.with_suffix(".json.bak")
        try:
            backup.write_bytes(settings_path.read_bytes())
        except OSError:
            pass  # 백업 실패는 치명적이지 않음
    else:
        existing = {}

    omk_config = _build_omk_hooks_config(python_path, hooks_dir)
    merged = _merge_hooks(existing.get("hooks", {}), omk_config)
    settings = {**existing, "hooks": merged}

    _write_settings_atomic(settings_path, settings)

    click.echo("")
    click.echo("  oh-my-kanban 세션 추적 활성화")
    click.echo("")
    click.echo(
        "  펜스로 집을 둘러싸듯이, Claude Code 작업 시 언제나 같은 맥락을 유지합니다."
    )
    click.echo(
        "  어디까지 했는지, 무엇을 결정했는지, 범위가 벗어났는지 자동으로 기록됩니다."
    )
    click.echo("")
    click.echo("  비활성화: /omk-off-this-session       (이 세션만)")
    click.echo(
        "           /omk-off-this-session-with-delete-task  (+ task 삭제)"
    )
    click.echo("")
    click.echo(f"  설정 위치: {settings_path}")
    click.echo(f"  Python:    {python_path}")
    click.echo(f"  훅 패키지:  {hooks_dir}")
    click.echo("")


def _uninstall_hooks(local: bool, local_only: bool = False) -> None:
    """Claude Code settings 파일에서 omk 훅을 제거한다."""
    settings_path = _settings_path(local, local_only)
    if not settings_path.exists():
        click.echo(f"settings.json 없음: {settings_path}")
        return

    try:
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise click.ClickException(f"settings.json 파싱 실패: {e}") from e

    cleaned_hooks = _remove_omk_hooks(existing.get("hooks", {}))
    settings = {**existing, "hooks": cleaned_hooks}

    _write_settings_atomic(settings_path, settings)
    click.echo(f"omk 훅 제거 완료: {settings_path}")


def _show_status() -> None:
    """설치된 훅 상태와 활성 세션 목록을 출력한다."""
    global_path = _settings_path(local=False)
    local_path = _settings_path(local=True)
    local_only_path = _settings_path(local=False, local_only=True)

    click.echo("=== omk 훅 설치 상태 ===")
    for label, path in [("전역", global_path), ("프로젝트", local_path), ("개인로컬", local_only_path)]:
        if not path.exists():
            click.echo(f"  [{label}] {path} — 없음")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            click.echo(f"  [{label}] {path} — 읽기 실패")
            continue

        hooks = data.get("hooks", {})
        omk_events = set()
        for event, groups in hooks.items():
            for group in groups:
                for h in group.get("hooks", []):
                    if _is_omk_command(h.get("command", "")):
                        omk_events.add(event)

        if omk_events:
            click.echo(f"  [{label}] {path}")
            for event in sorted(omk_events):
                click.echo(f"    ✓ {event}")
        else:
            click.echo(f"  [{label}] {path} — omk 훅 없음")

    click.echo("")
    click.echo("=== 활성 세션 ===")
    sessions = list_sessions()
    active = sorted(
        [s for s in sessions if s.status == STATUS_ACTIVE],
        key=lambda x: x.created_at,
        reverse=True,
    )

    if not active:
        click.echo("  활성 세션 없음")
    else:
        for s in active[:ACTIVE_SESSIONS_DISPLAY_MAX]:
            summary = s.scope.summary[:SUMMARY_SHORT_MAX] if s.scope.summary else "목표 미설정"
            wi_count = len(s.plane_context.work_item_ids)
            wi_text = f" | WI: {wi_count}개" if wi_count else ""
            click.echo(
                f"  {s.session_id[:SESSION_ID_DISPLAY_LEN]}...  "
                f"{summary}  "
                f"요청 {s.stats.total_prompts}회{wi_text}"
            )

    click.echo(f"\n세션 파일 위치: {SESSIONS_DIR}")


# ── Click 커맨드 그룹 ───────────────────────────────────────────────────────

@click.group("hooks")
def hooks() -> None:
    """Claude Code 훅 관리 (세션 자동 추적)."""


@hooks.command("install")
@click.option(
    "--local",
    "local",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.json에 설치 — 저장소 전체 공유 (프로젝트 scope)",
)
@click.option(
    "--local-only",
    "local_only",
    is_flag=True,
    default=False,
    help="현재 디렉토리의 .claude/settings.local.json에 설치 — 개인 전용, git 무시 (local scope)",
)
def install(local: bool, local_only: bool) -> None:
    """Claude Code에 omk 세션 추적 훅을 설치한다."""
    _install_hooks(local, local_only)


@hooks.command("uninstall")
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
    """Claude Code에서 omk 세션 추적 훅을 제거한다."""
    _uninstall_hooks(local, local_only)


@hooks.command("status")
def status() -> None:
    """설치된 훅 상태와 활성 세션을 표시한다."""
    _show_status()


@hooks.command("opt-out")
@click.option("--session-id", "session_id", default=None, help="세션 ID (기본: 최근 활성 세션)")
@click.option(
    "--delete-tasks",
    "delete_tasks",
    is_flag=True,
    default=False,
    help="생성된 Plane Work Item도 삭제",
)
def opt_out(session_id: Optional[str], delete_tasks: bool) -> None:
    """현재 세션의 omk 자동 추적을 중단한다."""
    from oh_my_kanban.hooks.opt_out import opt_out as _opt_out
    from oh_my_kanban.session.manager import list_sessions as _list_sessions

    target_id = session_id

    # session_id 미지정 시 최근 활성 세션 자동 선택
    if not target_id:
        active = sorted(
            [s for s in _list_sessions() if s.status == STATUS_ACTIVE],
            key=lambda x: x.updated_at,
            reverse=True,
        )
        if not active:
            raise click.ClickException("활성 세션이 없습니다. omk hooks status로 확인하세요.")
        target_id = active[0].session_id
        click.echo(f"대상 세션: {target_id[:SESSION_ID_DISPLAY_LEN]}...")

    _opt_out(target_id, delete_tasks=delete_tasks)
