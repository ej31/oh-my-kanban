"""공통 헬퍼: 페이지네이션, 식별자 파싱 등."""

from __future__ import annotations

import re
from typing import Any, Callable

import click


def fetch_all_pages(
    fetcher: Callable[..., Any],
    *args: Any,
    per_page: int = 100,
    max_pages: int = 500,
    **kwargs: Any,
) -> list[Any]:
    """모든 페이지를 순회하며 results를 합쳐 반환한다.

    cursor/per_page를 kwargs로 직접 받는 SDK 메서드용.
    params=dict 방식 메서드는 fetch_all_pages_with_params를 사용할 것.

    Args:
        fetcher: 페이지 데이터를 가져오는 callable.
        per_page: 페이지당 결과 수.
        max_pages: 무한루프 방지를 위한 최대 페이지 수 상한.
    """
    all_results: list[Any] = []
    cursor: str | None = None
    page_count = 0

    while True:
        page_count += 1
        if page_count > max_pages:
            click.echo(
                f"경고: 최대 페이지 수({max_pages})에 도달했습니다. 결과가 잘렸을 수 있습니다.",
                err=True,
            )
            break

        response = fetcher(*args, cursor=cursor, per_page=per_page, **kwargs)
        results = getattr(response, "results", [])
        all_results.extend(results)

        if not getattr(response, "next_page_results", False):
            break
        cursor = getattr(response, "next_cursor", None)
        if not cursor:
            break

    return all_results


def fetch_all_pages_with_params(
    fetcher: Callable[..., Any],
    *args: Any,
    per_page: int = 100,
    max_pages: int = 500,
) -> list[Any]:
    """params=dict 방식 SDK 메서드를 위한 전체 페이지 순회 헬퍼.

    cursor/per_page를 params dict에 담아 전달한다.
    예: ctx.client.agent_runs.activities.list(..., params={...})

    Args:
        fetcher: params=dict 를 받는 페이지 데이터 callable.
        per_page: 페이지당 결과 수.
        max_pages: 무한루프 방지를 위한 최대 페이지 수 상한.
    """
    all_results: list[Any] = []
    cursor: str | None = None
    page_count = 0

    while True:
        page_count += 1
        if page_count > max_pages:
            click.echo(
                f"경고: 최대 페이지 수({max_pages})에 도달했습니다. 결과가 잘렸을 수 있습니다.",
                err=True,
            )
            break

        params: dict = {"per_page": per_page}
        if cursor:
            params["cursor"] = cursor

        response = fetcher(*args, params=params)
        all_results.extend(getattr(response, "results", []))

        if not getattr(response, "next_page_results", False):
            break
        cursor = getattr(response, "next_cursor", None)
        if not cursor:
            break

    return all_results


# PROJECT-123 형식 패턴 (대문자 식별자 + 숫자)
_IDENTIFIER_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*)-(\d+)$")


def parse_work_item_ref(ref: str) -> tuple[str, int] | None:
    """
    'PROJECT-123' 형식을 (project_identifier, issue_number)로 파싱한다.
    일치하지 않으면 None 반환 (UUID로 처리).
    """
    m = _IDENTIFIER_PATTERN.match(ref.upper())
    if m:
        return m.group(1), int(m.group(2))
    return None


def confirm_delete(resource_type: str, resource_id: str) -> bool:
    """삭제 전 사용자 확인을 요청한다."""
    return click.confirm(f"{resource_type} '{resource_id}'를 삭제하시겠습니까?")


def truncate(text: str | None, max_len: int = 60) -> str:
    """긴 텍스트를 잘라 표시한다."""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
