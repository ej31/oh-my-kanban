"""프로젝트 바인딩 관리: .omk/project.toml 생성/삭제/조회."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from oh_my_kanban.config import (
    OMK_DIR_NAME,
    SOURCE_LABELS,
    UUID_RE,
    escape_toml_string,
    load_config,
)

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]


def _omk_dir(cwd: Path | None = None) -> Path:
    """cwd 기준 .omk 디렉토리 경로를 반환한다."""
    return (cwd or Path.cwd()) / OMK_DIR_NAME


def _project_toml(cwd: Path | None = None) -> Path:
    """cwd 기준 .omk/project.toml 경로를 반환한다."""
    return _omk_dir(cwd) / "project.toml"


def _ensure_omk_gitignore() -> None:
    """git 저장소 루트의 .gitignore에 .omk/ 항목을 추가한다.

    git 저장소가 아니거나 실패하면 경고만 출력하고 계속 진행한다.
    """
    ENTRY = ".omk/"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
            timeout=5,
        )
        if result.returncode != 0:
            return
        git_root = Path(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return

    gitignore_path = git_root / ".gitignore"
    try:
        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            if ENTRY in lines:
                return  # 이미 등록되어 있음
            if not content.endswith("\n"):
                content += "\n"
            content += f"{ENTRY}\n"
            gitignore_path.write_text(content, encoding="utf-8")
        else:
            gitignore_path.write_text(f"{ENTRY}\n", encoding="utf-8")
        click.echo(f"  .gitignore에 {ENTRY} 자동 추가: {gitignore_path}")
    except OSError as e:
        click.echo(f"  경고: .gitignore 업데이트 실패: {e}", err=True)


@click.group()
def project_cmd() -> None:
    """프로젝트 바인딩 관리: .omk/project.toml 생성/삭제/조회."""
    pass


@project_cmd.command("bind")
@click.argument("project_id")
@click.option(
    "--provider",
    default="plane",
    type=click.Choice(["plane", "linear"]),
    help="프로젝트 관리 도구 (기본: plane)",
)
def project_bind(project_id: str, provider: str) -> None:
    """현재 디렉토리에 프로젝트를 바인딩한다.

    \b
    PROJECT_ID: 바인딩할 프로젝트 UUID
    생성 위치: .omk/project.toml

    \b
    예시:
      omk project bind a1b2c3d4-e5f6-7890-abcd-ef1234567890
      omk project bind a1b2c3d4-e5f6-7890-abcd-ef1234567890 --provider linear
    """
    # project_id 형식 검증: UUID 패턴 [a-f0-9-]{36}
    if not UUID_RE.match(project_id.lower()):
        raise click.UsageError(
            f"project_id 형식이 올바르지 않습니다: '{project_id}'\n"
            "UUID 형식이어야 합니다 (예: a1b2c3d4-e5f6-7890-abcd-ef1234567890)"
        )

    toml_path = _project_toml()

    # 이미 존재하면 덮어쓰기 안내
    if toml_path.exists():
        click.echo(f"기존 바인딩이 존재합니다: {toml_path}")
        click.echo("덮어씁니다.")

    # .omk/ 디렉토리 생성 (없으면)
    try:
        _omk_dir().mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise click.ClickException(f".omk 디렉토리 생성 실패: {e}") from e

    # .omk/project.toml 작성 (tomllib은 읽기 전용이므로 직접 문자열 작성)
    escaped_pid = escape_toml_string(project_id)
    escaped_provider = escape_toml_string(provider)
    toml_content = (
        "[project]\n"
        f'project_id = "{escaped_pid}"\n'
        f'provider = "{escaped_provider}"\n'
    )
    try:
        toml_path.write_text(toml_content, encoding="utf-8")
    except OSError as e:
        raise click.ClickException(f".omk/project.toml 쓰기 실패: {e}") from e

    click.echo(f"프로젝트 바인딩 완료: {toml_path}")
    click.echo(f"  project_id : {project_id}")
    click.echo(f"  provider   : {provider}")

    # git 저장소의 .gitignore에 .omk/ 항목 안내
    _ensure_omk_gitignore()
    click.echo()
    click.echo("팁: .omk/ 디렉토리는 .gitignore에 추가하는 것을 권장합니다.")


@project_cmd.command("unbind")
def project_unbind() -> None:
    """현재 디렉토리의 프로젝트 바인딩을 해제한다.

    .omk/project.toml과 .omk/.prompted 마커 파일을 삭제한다.
    다음 세션에서 프로젝트 안내를 다시 받을 수 있다.
    """
    toml_path = _project_toml()

    if not toml_path.exists():
        click.echo("바인딩된 프로젝트가 없습니다. (.omk/project.toml 파일 없음)")
        return

    # .omk/project.toml 삭제
    try:
        toml_path.unlink()
    except OSError as e:
        raise click.ClickException(f".omk/project.toml 삭제 실패: {e}") from e

    click.echo(f"프로젝트 바인딩 해제: {toml_path}")

    # .omk/.prompted 마커 삭제 (다음 세션에서 다시 안내받을 수 있도록)
    prompted_path = _omk_dir() / ".prompted"
    if prompted_path.exists():
        try:
            prompted_path.unlink()
            click.echo(f"  .prompted 마커 삭제: {prompted_path}")
        except OSError as e:
            click.echo(f"  경고: .prompted 마커 삭제 실패: {e}", err=True)


@project_cmd.command("show")
def project_show() -> None:
    """현재 프로젝트 바인딩 상태를 출력한다.

    .omk/project.toml, CLAUDE.md, config.toml, 환경변수 순서로 탐색한다.
    """
    cfg = load_config()

    click.echo("=== 프로젝트 바인딩 상태 ===")
    if cfg.project_id:
        source_label = SOURCE_LABELS.get(cfg.project_id_source, cfg.project_id_source)
        click.echo(f"  project_id  : {cfg.project_id} (소스: {source_label})")
    else:
        click.echo("  project_id  : (미설정)")

    # .omk/project.toml에서 직접 provider 조회 (load_config는 provider를 노출하지 않음)
    provider_str = "(미설정)"
    toml_path = _project_toml()
    if toml_path.exists():
        try:
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
            provider_str = data.get("project", {}).get("provider", "plane")
        except (OSError, tomllib.TOMLDecodeError, AttributeError) as e:
            provider_str = "(읽기 오류)"
            click.echo(f"  경고: provider 읽기 실패: {type(e).__name__}: {e}", err=True)

    click.echo(f"  provider    : {provider_str}")

    if toml_path.exists():
        click.echo(f"  설정 파일   : {toml_path.resolve()}")
    else:
        click.echo(f"  설정 파일   : {toml_path} (없음)")


@project_cmd.command("opt-out")
def project_opt_out() -> None:
    """이 프로젝트에서 omk 세션 추적을 비활성화한다.

    .omk/disabled 파일을 생성해 세션 훅이 동작하지 않도록 한다.
    """
    omk = _omk_dir()

    # .omk/ 디렉토리 생성 (없으면)
    try:
        omk.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise click.ClickException(f".omk 디렉토리 생성 실패: {e}") from e

    disabled_path = omk / "disabled"
    # 현재 시각 ISO 문자열 기록
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    try:
        disabled_path.write_text(now_iso, encoding="utf-8")
    except OSError as e:
        raise click.ClickException(f".omk/disabled 파일 생성 실패: {e}") from e

    click.echo("이 프로젝트에서 omk 세션 추적이 비활성화되었습니다.")
    click.echo(f"  비활성화 시각: {now_iso}")
    click.echo(f"  마커 파일: {disabled_path}")
    click.echo("재활성화하려면: omk project opt-in")


@project_cmd.command("opt-in")
def project_opt_in() -> None:
    """이 프로젝트에서 omk 세션 추적을 활성화한다.

    .omk/disabled 파일을 삭제해 세션 훅이 다시 동작하도록 한다.
    """
    disabled_path = _omk_dir() / "disabled"

    if not disabled_path.exists():
        click.echo("이미 활성화 상태입니다. (.omk/disabled 파일 없음)")
        return

    try:
        disabled_path.unlink()
    except OSError as e:
        raise click.ClickException(f".omk/disabled 파일 삭제 실패: {e}") from e

    click.echo("omk 세션 추적이 활성화되었습니다.")
    click.echo(f"  삭제된 마커 파일: {disabled_path}")
