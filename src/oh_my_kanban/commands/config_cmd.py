"""설정 관리 커맨드: config init/show/set/profile."""

from __future__ import annotations

import os
import re

import click

from oh_my_kanban.config import CONFIG_FILE, list_profiles, load_config, save_config

# plane.so 클라우드 API URL
_CLOUD_API_URL = "https://api.plane.so"


def _extract_slug_from_url(url: str) -> str:
    """URL에서 워크스페이스 슬러그를 추출한다.

    지원 형식:
      https://app.plane.so/my-workspace/
      https://app.plane.so/my-workspace/projects/...
      https://plane.example.com/my-workspace/
    """
    # URL에서 호스트 다음 첫 번째 경로 세그먼트 추출
    match = re.search(r"https?://[^/]+/([^/?#\s]+)", url)
    if match:
        return match.group(1)
    return ""


@click.group()
def config() -> None:
    """설정 파일 관리."""
    pass


@config.command("init")
def config_init() -> None:
    """대화형으로 ~/.config/oh-my-kanban/config.toml을 생성한다.

    \b
    환경변수로도 설정 가능합니다 (AI 에이전트 자동화 용도):
      PLANE_BASE_URL        - API 서버 URL
      PLANE_API_KEY         - API 키
      PLANE_WORKSPACE_SLUG  - 워크스페이스 슬러그
    """
    click.echo("oh-my-kanban 초기 설정을 시작합니다.")
    click.echo(f"설정 파일 위치: {CONFIG_FILE}")
    click.echo()

    # 환경변수에서 미리 값 가져오기
    env_base_url = os.environ.get("PLANE_BASE_URL", "")
    env_api_key = os.environ.get("PLANE_API_KEY", "")
    env_workspace_slug = os.environ.get("PLANE_WORKSPACE_SLUG", "")

    # 환경변수로 모든 값이 설정된 경우 대화형 없이 바로 저장
    if env_api_key and env_workspace_slug:
        base_url = env_base_url or _CLOUD_API_URL
        click.echo("환경변수에서 설정을 읽었습니다:")
        click.echo(f"  PLANE_BASE_URL        = {base_url}")
        click.echo(f"  PLANE_API_KEY         = {'*' * 8}")
        click.echo(f"  PLANE_WORKSPACE_SLUG  = {env_workspace_slug}")
        save_config(
            {
                "base_url": base_url,
                "api_key": env_api_key,
                "workspace_slug": env_workspace_slug,
            },
            profile="default",
        )
        click.echo()
        click.echo(f"설정이 저장되었습니다: {CONFIG_FILE}")
        return

    # 기존 설정 로드 (있으면 기본값으로 사용)
    existing = load_config()

    # 1단계: cloud vs self-hosted 선택
    click.echo("어떤 Plane 서버를 사용하시나요?")
    click.echo("  1) plane.so 클라우드 (https://app.plane.so)")
    click.echo("  2) 직접 설치한 서버 (self-hosted)")
    click.echo()

    server_type = click.prompt(
        "서버 종류 선택",
        type=click.Choice(["1", "2"]),
        default="1",
        show_choices=False,
    )

    if server_type == "1":
        # plane.so 클라우드
        base_url = _CLOUD_API_URL
        click.echo()
        click.echo("plane.so 클라우드를 사용합니다.")
        click.echo("  API 키: https://app.plane.so/profile/api-tokens/ 에서 발급")
        click.echo()
    else:
        # self-hosted
        click.echo()
        click.echo("self-hosted 서버 URL을 입력하세요.")
        click.echo("예) https://plane.example.com")
        click.echo()
        server_url = click.prompt(
            "서버 URL",
            default=existing.base_url if existing.base_url != _CLOUD_API_URL else "",
        )
        # self-hosted는 /api/v1 경로를 포함한 API URL 구성
        server_url = server_url.rstrip("/")
        # 이미 /api 가 포함되어 있으면 그대로, 아니면 그대로 사용 (SDK가 경로 처리)
        base_url = server_url

    # 2단계: API 키
    api_key = click.prompt(
        "API 키",
        default=env_api_key or existing.api_key or "",
        hide_input=True,
        prompt_suffix=" (PLANE_API_KEY): ",
    )

    if not api_key:
        raise click.UsageError("API 키는 필수입니다.")

    # 3단계: 워크스페이스 슬러그
    click.echo()
    click.echo("워크스페이스를 확인하려면 로그인 후 주소창의 URL을 복사해서 붙여넣으세요.")
    if server_type == "1":
        click.echo("예) https://app.plane.so/my-workspace/")
    else:
        click.echo("예) https://plane.example.com/my-workspace/")
    click.echo("또는 슬러그를 직접 입력하세요 (예: my-workspace)")
    click.echo()

    workspace_input = click.prompt(
        "워크스페이스 URL 또는 슬러그",
        default=env_workspace_slug or existing.workspace_slug or "",
        prompt_suffix=" (PLANE_WORKSPACE_SLUG): ",
    )

    # URL인 경우 슬러그 추출
    if workspace_input.startswith("http"):
        workspace_slug = _extract_slug_from_url(workspace_input)
        if not workspace_slug:
            raise click.UsageError(
                f"URL에서 워크스페이스 슬러그를 찾을 수 없습니다: {workspace_input}\n"
                "슬러그를 직접 입력해주세요 (예: my-workspace)"
            )
        click.echo(f"  → 슬러그 추출: {workspace_slug}")
    else:
        workspace_slug = workspace_input.strip()

    if not workspace_slug:
        raise click.UsageError("워크스페이스 슬러그는 필수입니다.")

    save_config(
        {
            "base_url": base_url,
            "api_key": api_key,
            "workspace_slug": workspace_slug,
        },
        profile="default",
    )

    click.echo()
    click.echo(f"설정이 저장되었습니다: {CONFIG_FILE}")
    click.echo()
    click.echo("설정 확인: omk config show")


@config.command("show")
@click.option("--profile", default="default", help="조회할 프로필")
def config_show(profile: str) -> None:
    """현재 설정을 출력한다. API 키는 마스킹 처리된다."""
    cfg = load_config(profile)

    # API 키 마스킹: pl_...xxxx 형식
    raw_key = cfg.api_key
    if raw_key and len(raw_key) > 8:
        masked_key = raw_key[:4] + "..." + raw_key[-4:]
    elif raw_key:
        masked_key = "****"
    else:
        masked_key = "(미설정)"

    click.echo(f"프로필      : {cfg.profile}")
    click.echo(f"base_url    : {cfg.base_url}")
    click.echo(f"api_key     : {masked_key}")
    click.echo(f"workspace   : {cfg.workspace_slug or '(미설정)'}")
    click.echo(f"project_id  : {cfg.project_id or '(미설정)'}")
    click.echo(f"output      : {cfg.output}")
    click.echo(f"설정 파일   : {CONFIG_FILE if CONFIG_FILE.exists() else str(CONFIG_FILE) + ' (없음)'}")
    click.echo()
    click.echo("환경변수로 덮어쓰기 가능:")
    click.echo("  PLANE_BASE_URL, PLANE_API_KEY, PLANE_WORKSPACE_SLUG, PLANE_PROJECT_ID")


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--profile", default="default", help="대상 프로필")
def config_set(key: str, value: str, profile: str) -> None:
    """설정 값을 변경한다.

    \b
    사용 가능한 키:
      base_url, api_key, workspace_slug, project_id, output
    """
    허용_키 = {"base_url", "api_key", "workspace_slug", "project_id", "output"}
    if key not in 허용_키:
        raise click.UsageError(
            f"알 수 없는 키: '{key}'\n허용 키: {', '.join(sorted(허용_키))}"
        )

    if key == "output" and value not in ("json", "table", "plain"):
        raise click.UsageError("output 값은 json, table, plain 중 하나여야 합니다.")

    save_config({key: value}, profile=profile)
    click.echo(f"[{profile}] {key} = {value if key != 'api_key' else '****'} 저장 완료")


@config.group("profile")
def config_profile() -> None:
    """프로필 관리."""
    pass


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

    # 기본 프로필 정보를 'active_profile' 키로 저장
    save_config({"active_profile": name}, profile="_meta")
    click.echo(f"기본 프로필이 '{name}'으로 변경되었습니다.")
    click.echo("다음 실행 시 '--profile' 옵션 또는 PLANE_PROFILE 환경변수로 적용하세요.")
