"""에러 처리: HttpError → 사용자 메시지 변환 및 exit code."""

from __future__ import annotations

import functools
import sys
from typing import Callable, TypeVar

import click

F = TypeVar("F", bound=Callable)

# HTTP 상태 코드 → 사용자 메시지
_STATUS_MESSAGES: dict[int, str] = {
    400: "잘못된 요청입니다",
    401: "인증에 실패했습니다. API 키를 확인하세요 (PLANE_API_KEY)",
    403: "접근 권한이 없습니다",
    404: "요청한 리소스를 찾을 수 없습니다",
    409: "충돌이 발생했습니다 (이미 존재하거나 상태 불일치)",
    422: "입력 데이터가 유효하지 않습니다",
    429: "요청 제한을 초과했습니다. 잠시 후 다시 시도하세요",
    500: "서버 내부 오류가 발생했습니다",
    502: "게이트웨이 오류가 발생했습니다",
    503: "서비스를 일시적으로 사용할 수 없습니다",
}

# HTTP 상태 코드 → exit code (POSIX 규약)
_EXIT_CODES: dict[int, int] = {
    400: 64,  # EX_DATAERR
    401: 77,  # EX_NOPERM
    403: 77,  # EX_NOPERM
    404: 1,
    409: 1,
    422: 64,  # EX_DATAERR
    429: 1,
    500: 69,  # EX_UNAVAILABLE
    502: 69,
    503: 69,
}


def _format_http_error(e: Exception) -> str:
    """HttpError를 사용자가 이해할 수 있는 메시지로 변환한다."""
    status_code = getattr(e, "status_code", None)
    response = getattr(e, "response", None)

    base = _STATUS_MESSAGES.get(status_code, f"HTTP {status_code}") if status_code else str(e)

    if isinstance(response, dict):
        detail = response.get("detail") or response.get("error") or response.get("message")
        if detail:
            if isinstance(detail, list):
                detail = "; ".join(str(d) for d in detail)
            # 404 + "Page not found"는 엔터프라이즈 전용 기능일 가능성이 높음
            if status_code == 404 and "Page not found" in str(detail):
                return f"{base}. 이 기능은 현재 서버에서 지원하지 않습니다 (Plane Enterprise 전용일 수 있습니다)"
            return f"{base}: {detail}"

    return base


def _exit_code_for_status(status_code: int | None) -> int:
    """HTTP 상태 코드에 대응하는 exit code를 반환한다."""
    if status_code is None:
        return 1
    return _EXIT_CODES.get(status_code, 1)


def handle_api_error(func: F) -> F:
    """CLI 커맨드를 감싸는 에러 핸들러 데코레이터."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except click.exceptions.Exit:
            raise
        except click.exceptions.Abort:
            raise
        except click.UsageError:
            raise
        except Exception as e:
            # plane.errors 임포트는 런타임에 (순환 임포트 방지)
            try:
                from plane.errors.errors import ConfigurationError, HttpError

                if isinstance(e, HttpError):
                    msg = _format_http_error(e)
                    click.echo(f"오류: {msg}", err=True)
                    sys.exit(_exit_code_for_status(e.status_code))
                if isinstance(e, ConfigurationError):
                    click.echo(f"설정 오류: {e}", err=True)
                    sys.exit(78)  # EX_CONFIG
            except ImportError as ie:
                # plane.errors 모듈 경로가 변경된 경우 경고 출력 (순환 임포트 방지 목적의 런타임 import)
                click.echo(f"경고: 내부 모듈 임포트 실패 - {ie}", err=True)

            click.echo(f"오류: {e}", err=True)
            sys.exit(1)

    return wrapper  # type: ignore[return-value]
