"""Linear GraphQL/HTTP 에러 처리."""
from __future__ import annotations

import functools
import sys

import click
import httpx


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
        }
        detail = mapping.get(e.status_code, f"HTTP {e.status_code} 오류")
        return f"오류: {detail}"
    if isinstance(e, httpx.TimeoutException):
        return "오류: 요청 시간이 초과되었습니다. 네트워크 연결을 확인하세요"
    return f"오류: {e}"


def handle_linear_error(func):
    """Linear API 에러를 사용자 친화적 메시지로 변환하는 데코레이터."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.UsageError, click.Abort):
            raise
        except (LinearGraphQLError, LinearHttpError, httpx.TimeoutException) as e:
            click.echo(format_linear_error(e), err=True)
            sys.exit(1)

    return wrapper
