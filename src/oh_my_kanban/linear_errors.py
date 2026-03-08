"""Linear GraphQL/HTTP 에러 처리."""
from __future__ import annotations

import functools
import json
import sys

import click
import httpx

# HTTP 상태 코드 → exit code (Plane과 통일)
_LINEAR_EXIT_CODES: dict[int, int] = {
    401: 77,  # EX_NOPERM
    403: 77,  # EX_NOPERM
    429: 69,  # EX_UNAVAILABLE (rate limit)
    500: 69,  # EX_UNAVAILABLE
    502: 69,
    503: 69,
    504: 69,  # Gateway Timeout
}


class LinearGraphQLError(Exception):
    """Linear GraphQL API가 errors 필드를 반환했을 때 발생한다."""

    def __init__(self, errors: list[dict]) -> None:
        self.errors = errors
        super().__init__(str(errors))


class LinearHttpError(Exception):
    """Linear API 호출 중 HTTP 오류가 발생했을 때 사용한다."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class LinearResponseParseError(Exception):
    """Linear API 응답 JSON 파싱에 실패했을 때 발생한다."""


def _exit_code_for_linear(e: Exception) -> int:
    """Linear 예외에 대응하는 exit code를 반환한다."""
    if isinstance(e, LinearHttpError):
        return _LINEAR_EXIT_CODES.get(e.status_code, 1)
    if isinstance(e, httpx.NetworkError):
        return 69  # EX_UNAVAILABLE
    return 1


def format_linear_error(e: Exception) -> str:
    """예외를 사용자 친화적 한글 메시지로 변환한다."""
    if isinstance(e, LinearGraphQLError):
        msgs = [err.get("message", "알 수 없는 오류") for err in e.errors]
        return "오류: " + "; ".join(msgs)
    if isinstance(e, LinearHttpError):
        mapping = {
            401: "인증 실패. LINEAR_API_KEY를 확인하세요",
            403: "권한이 부족합니다",
            404: "해당 리소스를 찾을 수 없습니다",
            429: "요청 한도를 초과했습니다. 잠시 후 다시 시도하세요",
            500: "Linear 서버 내부 오류가 발생했습니다",
            502: "Linear 서버에 연결할 수 없습니다 (Bad Gateway)",
            503: "Linear 서비스가 일시적으로 불가합니다. 잠시 후 다시 시도하세요",
        }
        detail = mapping.get(e.status_code, f"HTTP {e.status_code} 오류")
        return f"오류: {detail}"
    if isinstance(e, httpx.TimeoutException):
        return "오류: 요청 시간이 초과되었습니다. 네트워크 연결을 확인하세요"
    if isinstance(e, httpx.NetworkError):
        return "오류: 네트워크 연결 오류. 인터넷 연결 및 Linear 서비스 상태를 확인하세요"
    if isinstance(e, (json.JSONDecodeError, LinearResponseParseError)):
        return "오류: 서버 응답을 파싱할 수 없습니다. 응답이 손상되었을 수 있습니다"
    return f"오류: {e}"


def handle_linear_error(func):
    """Linear API 에러를 사용자 친화적 메시지로 변환하는 데코레이터."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.UsageError, click.Abort):
            raise
        except (
            LinearGraphQLError,
            LinearHttpError,
            httpx.TimeoutException,
            httpx.NetworkError,
            json.JSONDecodeError,
            LinearResponseParseError,
        ) as e:
            click.echo(format_linear_error(e), err=True)
            sys.exit(_exit_code_for_linear(e))

    return wrapper
