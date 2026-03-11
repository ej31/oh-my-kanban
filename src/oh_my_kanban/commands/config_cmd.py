"""설정 관리 커맨드: config init/show/set/profile."""

from __future__ import annotations

import re

import click

from oh_my_kanban.config import CONFIG_FILE, Config, list_profiles, load_config, save_config

_CLOUD_API_URL = "https://api.plane.so"
_PUBLIC_CONFIG_KEYS = (
    "output",
    "plane.base_url",
    "plane.api_key",
    "plane.workspace_slug",
    "plane.project_id",
    "linear.api_key",
    "linear.team_id",
)
_MASKED_KEYS = {"plane.api_key", "linear.api_key"}


def _save_config_safe(data: dict, profile: str = "default") -> None:
    """save_config 호출 실패를 Click 친화적 UsageError로 변환한다."""

    try:
        save_config(data, profile=profile)
    except (OSError, ValueError) as e:
        raise click.UsageError(str(e)) from e


def _extract_slug_from_url(url: str) -> str:
    """URL에서 워크스페이스 슬러그를 추출한다."""

    match = re.search(r"https?://[^/]+/([^/?#\s]+)", url)
    if match:
        return match.group(1)
    return ""


def _mask_secret(raw_key: str, prefix: int = 4, suffix: int = 4) -> str:
    """Mask secrets for display."""

    if raw_key and len(raw_key) > prefix + suffix:
        return raw_key[:prefix] + "..." + raw_key[-suffix:]
    if raw_key:
        return "****"
    return "(미설정)"


def _prompt_plane_config(existing: Config) -> dict[str, str]:
    """Collect Plane config interactively."""

    click.echo()
    click.echo("Plane 서버를 설정합니다.")
    click.echo("  1) plane.so 클라우드 (https://app.plane.so)")
    click.echo("  2) 직접 설치한 서버 (self-hosted)")
    click.echo()

    default_server_type = "1" if existing.base_url in ("", _CLOUD_API_URL) else "2"
    server_type = click.prompt(
        "서버 종류 선택",
        type=click.Choice(["1", "2"]),
        default=default_server_type,
        show_choices=False,
    )

    if server_type == "1":
        base_url = _CLOUD_API_URL
    else:
        click.echo("self-hosted 서버 URL을 입력하세요. 예) https://plane.example.com")
        base_url = click.prompt(
            "서버 URL",
            default=existing.base_url if existing.base_url != _CLOUD_API_URL else "",
        ).rstrip("/")

    api_key = click.prompt(
        "API 키",
        default=existing.api_key or "",
        hide_input=True,
        prompt_suffix=" (PLANE_API_KEY): ",
    )
    if not api_key:
        raise click.UsageError("Plane API 키는 필수입니다.")

    click.echo()
    click.echo("워크스페이스 URL 또는 슬러그를 입력하세요.")
    workspace_input = click.prompt(
        "워크스페이스 URL 또는 슬러그",
        default=existing.workspace_slug or "",
        prompt_suffix=" (PLANE_WORKSPACE_SLUG): ",
    )

    if workspace_input.startswith("http"):
        workspace_slug = _extract_slug_from_url(workspace_input)
        if not workspace_slug:
            raise click.UsageError(
                f"URL에서 워크스페이스 슬러그를 찾을 수 없습니다: {workspace_input}"
            )
        click.echo(f"  → 슬러그 추출: {workspace_slug}")
    else:
        workspace_slug = workspace_input.strip()

    project_id = click.prompt(
        "기본 프로젝트 UUID (선택)",
        default=existing.project_id or "",
        prompt_suffix=" (PLANE_PROJECT_ID): ",
        show_default=False,
    ).strip()

    return {
        "plane.base_url": base_url,
        "plane.api_key": api_key,
        "plane.workspace_slug": workspace_slug,
        "plane.project_id": project_id,
    }


def _prompt_linear_config(existing: Config) -> dict[str, str]:
    """Collect Linear config interactively."""

    click.echo()
    click.echo("Linear 설정을 구성합니다.")
    api_key = click.prompt(
        "Linear API 키",
        default=existing.linear_api_key or "",
        hide_input=True,
        prompt_suffix=" (LINEAR_API_KEY): ",
    )
    if not api_key:
        raise click.UsageError("Linear API 키는 필수입니다.")

    team_id = click.prompt(
        "기본 팀 ID (선택)",
        default=existing.linear_team_id or "",
        prompt_suffix=" (LINEAR_TEAM_ID): ",
        show_default=False,
    ).strip()

    return {
        "linear.api_key": api_key,
        "linear.team_id": team_id,
    }


@click.group()
def config() -> None:
    """설정 파일 관리."""


@config.command("init")
@click.option("--profile", default="default", help="초기화할 프로필")
def config_init(profile: str) -> None:
    """대화형으로 provider-aware 설정을 생성한다."""

    click.echo("oh-my-kanban 초기 설정을 시작합니다.")
    click.echo(f"설정 파일 위치: {CONFIG_FILE}")
    click.echo()

    existing = load_config(profile)
    payload: dict[str, str] = {}

    configure_plane = click.confirm("Plane 설정을 구성하시겠습니까?", default=True)
    configure_linear = click.confirm(
        "Linear 설정을 구성하시겠습니까?",
        default=bool(existing.linear_api_key or existing.linear_team_id),
    )

    if not configure_plane and not configure_linear:
        raise click.UsageError("최소 하나의 provider를 선택해야 합니다.")

    if configure_plane:
        payload.update(_prompt_plane_config(existing))
    if configure_linear:
        payload.update(_prompt_linear_config(existing))

    payload["output"] = click.prompt(
        "기본 출력 형식",
        type=click.Choice(["table", "json", "plain"]),
        default=existing.output or "table",
        show_choices=True,
    )

    _save_config_safe(payload, profile=profile)
    click.echo()
    click.echo(f"[{profile}] 설정이 저장되었습니다: {CONFIG_FILE}")
    click.echo("설정 확인: omk config show")


@config.command("show")
@click.option("--profile", default="default", help="조회할 프로필")
def config_show(profile: str) -> None:
    """현재 설정을 출력한다. API 키는 마스킹 처리된다."""

    cfg = load_config(profile)
    click.echo(f"프로필      : {cfg.profile}")
    click.echo(f"output      : {cfg.output}")
    click.echo(f"설정 파일   : {CONFIG_FILE if CONFIG_FILE.exists() else str(CONFIG_FILE) + ' (없음)'}")
    click.echo()
    click.echo("환경변수로 덮어쓰기 가능:")
    click.echo(
        "  PLANE_BASE_URL, PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_PROJECT_ID, "
        "LINEAR_API_KEY, LINEAR_TEAM_ID"
    )
    click.echo()
    click.echo("--- Plane ---")
    click.echo(f"base_url          : {cfg.base_url}")
    click.echo(f"api_key           : {_mask_secret(cfg.api_key)}")
    click.echo(f"workspace_slug    : {cfg.workspace_slug or '(미설정)'}")
    click.echo(f"project_id        : {cfg.project_id or '(미설정)'}")
    click.echo()
    click.echo("--- Linear ---")
    click.echo(f"api_key           : {_mask_secret(cfg.linear_api_key, prefix=8, suffix=0)}")
    click.echo(f"team_id           : {cfg.linear_team_id or '(미설정)'}")


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--profile", default="default", help="대상 프로필")
def config_set(key: str, value: str, profile: str) -> None:
    """설정 값을 변경한다.

    \b
    사용 가능한 키:
      output
      plane.base_url
      plane.api_key
      plane.workspace_slug
      plane.project_id
      linear.api_key
      linear.team_id
    """

    if key not in _PUBLIC_CONFIG_KEYS:
        raise click.UsageError(
            f"알 수 없는 키: '{key}'\n허용 키: {', '.join(_PUBLIC_CONFIG_KEYS)}"
        )

    if key == "output" and value not in ("json", "table", "plain"):
        raise click.UsageError("output 값은 json, table, plain 중 하나여야 합니다.")

    _save_config_safe({key: value}, profile=profile)
    display_value = "****" if key in _MASKED_KEYS else value
    click.echo(f"[{profile}] {key} = {display_value} 저장 완료")


@config.group("profile")
def config_profile() -> None:
    """프로필 관리."""


@config_profile.command("list")
def profile_list() -> None:
    """저장된 프로필 목록을 출력한다."""

    profiles = list_profiles()
    if not profiles:
        click.echo("저장된 프로필이 없습니다. 'omk config init'으로 설정하세요.")
        return

    click.echo("저장된 프로필:")
    for p in profiles:
        click.echo(f"  - {p}")


@config_profile.command("use")
@click.argument("name")
def profile_use(name: str) -> None:
    """기본 프로필을 변경한다.

    NAME: 사용할 프로필 이름
    """

    profiles = list_profiles()
    if name not in profiles:
        available = ", ".join(profiles) if profiles else "(없음)"
        raise click.UsageError(
            f"프로필 '{name}'이 존재하지 않습니다. 사용 가능한 프로필: {available}"
        )

    _save_config_safe({"active_profile": name}, profile="_meta")
    click.echo(f"기본 프로필이 '{name}'으로 변경되었습니다.")
    click.echo("다음 실행 시 '--profile' 옵션 또는 PLANE_PROFILE 환경변수로 적용하세요.")
