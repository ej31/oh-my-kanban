"""omk doctor: 통합 진단 명령."""

from __future__ import annotations

import sys

import click

from oh_my_kanban.config import CONFIG_FILE, Config, load_config


# 진단 결과 상수
_PASS = "PASS"
_FAIL = "FAIL"
_SKIP = "SKIP"


def _check_config_file(cfg: Config) -> tuple[str, str]:
    """config.toml 파일 존재 및 유효성 검증."""
    if not CONFIG_FILE.exists():
        return _FAIL, f"설정 파일 없음: {CONFIG_FILE}"
    if not cfg.api_key:
        return _FAIL, "api_key 미설정"
    if not cfg.workspace_slug:
        return _FAIL, "workspace_slug 미설정"
    return _PASS, f"설정 로드 완료 (프로필: {cfg.profile})"


def _check_plane_sdk_version() -> tuple[str, str]:
    """plane-sdk 버전 호환성 검증."""
    try:
        import plane
        version = getattr(plane, "__version__", "알 수 없음")
        return _PASS, f"plane-sdk {version}"
    except ImportError:
        return _FAIL, "plane-sdk 미설치"


def _check_plane_api(cfg: Config) -> tuple[str, str]:
    """Plane API 연결 헬스체크 (/api/v1/users/me/)."""
    if not cfg.api_key or not cfg.workspace_slug:
        return _SKIP, "Plane API 미설정"
    try:
        import httpx
    except ImportError:
        return _SKIP, "httpx 미설치"

    base_url = cfg.base_url.rstrip("/")
    from oh_my_kanban.hooks.http_client import build_plane_headers
    headers = build_plane_headers(cfg.api_key)

    try:
        with httpx.Client(timeout=httpx.Timeout(5.0, connect=3.0), follow_redirects=False) as client:
            resp = client.get(f"{base_url}/api/v1/users/me/", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                return _PASS, f"인증 성공 ({email})"
            elif resp.status_code == 401:
                return _FAIL, "API 키 인증 실패 (401)"
            elif resp.status_code == 403:
                return _FAIL, "접근 권한 부족 (403)"
            else:
                return _FAIL, f"HTTP {resp.status_code}"
    except httpx.ConnectError:
        return _FAIL, f"서버 연결 실패: {base_url}"
    except httpx.TimeoutException:
        return _FAIL, "요청 시간 초과"
    except Exception as e:
        return _FAIL, f"예외: {type(e).__name__}: {e}"


def _check_linear_api(cfg: Config) -> tuple[str, str]:
    """Linear API 연결 헬스체크 (viewer { id email })."""
    if not cfg.linear_api_key:
        return _SKIP, "Linear API 미설정"
    try:
        import httpx
    except ImportError:
        return _SKIP, "httpx 미설치"

    try:
        with httpx.Client(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            resp = client.post(
                "https://api.linear.app/graphql",
                headers={
                    "Authorization": cfg.linear_api_key,
                    "Content-Type": "application/json",
                },
                json={"query": "{ viewer { id email } }"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if errors := data.get("errors"):
                    return _FAIL, f"GraphQL 오류: {errors[0].get('message', '알 수 없음')}"
                viewer = data.get("data", {}).get("viewer", {})
                email = viewer.get("email", "")
                return _PASS, f"인증 성공 ({email})"
            elif resp.status_code == 401:
                return _FAIL, "API 키 인증 실패 (401)"
            else:
                return _FAIL, f"HTTP {resp.status_code}"
    except httpx.ConnectError:
        return _FAIL, "Linear 서버 연결 실패"
    except httpx.TimeoutException:
        return _FAIL, "요청 시간 초과"
    except Exception as e:
        return _FAIL, f"예외: {type(e).__name__}: {e}"


@click.command("doctor")
def doctor() -> None:
    """설정 및 연결 상태를 진단한다."""
    click.echo("oh-my-kanban 진단을 시작합니다...")
    click.echo()

    try:
        cfg = load_config()
    except Exception as e:
        click.echo(f"  ✗ [FAIL] 설정 파일: 파싱 오류: {e}")
        sys.exit(1)

    checks: list[tuple[str, tuple[str, str]]] = [
        ("설정 파일", _check_config_file(cfg)),
        ("plane-sdk 버전", _check_plane_sdk_version()),
        ("Plane API 연결", _check_plane_api(cfg)),
        ("Linear API 연결", _check_linear_api(cfg)),
    ]

    has_failure = False
    for name, (status, detail) in checks:
        if status == _PASS:
            icon = "✓"
        elif status == _FAIL:
            icon = "✗"
            has_failure = True
        else:
            icon = "-"

        click.echo(f"  {icon} [{status:4s}] {name}: {detail}")

    click.echo()
    if has_failure:
        click.echo("일부 항목이 실패했습니다. 위 결과를 확인하세요.")
        sys.exit(1)
    else:
        click.echo("모든 진단이 통과했습니다.")
