"""출력 포맷터: json / table / plain."""

from __future__ import annotations

import json
import sys
from typing import Any


def _to_dict(item: Any) -> dict:
    """Pydantic 모델 또는 dict를 dict로 변환한다."""
    if hasattr(item, "model_dump"):
        return item.model_dump(exclude_none=True)
    if isinstance(item, dict):
        return item
    return {"value": str(item)}


def format_output(
    data: Any,
    fmt: str,
    columns: list[str] | None = None,
    title: str | None = None,
) -> None:
    """데이터를 지정된 포맷으로 stdout에 출력한다."""
    # 리스트가 아닌 경우 단일 항목으로 처리
    is_single = not isinstance(data, list)
    items = [data] if is_single else data

    if not items:
        if fmt != "json":
            click_echo_err("결과 없음")
        else:
            sys.stdout.write("[]\n")
        return

    if fmt == "json":
        dicts = [_to_dict(item) for item in items]
        output = dicts[0] if is_single else dicts
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2, default=str)
        sys.stdout.write("\n")

    elif fmt == "table":
        _format_table(items, columns, title)

    elif fmt == "plain":
        _format_plain(items, columns)

    else:
        _format_plain(items, columns)


def _format_table(items: list, columns: list[str] | None, title: str | None) -> None:
    """rich.Table을 사용한 테이블 출력."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        # 컬럼이 없으면 첫 항목의 필드에서 자동 추출 (최대 8개)
        if not columns:
            first = _to_dict(items[0])
            columns = list(first.keys())[:8]

        table = Table(title=title, show_header=True, header_style="bold cyan")
        for col in columns:
            table.add_column(col, overflow="fold")

        for item in items:
            d = _to_dict(item)
            table.add_row(*[str(d.get(c, "")) for c in columns])

        console.print(table)

    except ImportError:
        # rich 없으면 plain으로 폴백
        _format_plain(items, columns)


def _format_plain(items: list, columns: list[str] | None) -> None:
    """탭 구분 일반 텍스트 출력."""
    first = _to_dict(items[0])
    cols = columns or list(first.keys())

    print("\t".join(cols))
    for item in items:
        d = _to_dict(item)
        print("\t".join(str(d.get(c, "")) for c in cols))


def click_echo_err(msg: str) -> None:
    """stderr에 메시지 출력."""
    import click

    click.echo(msg, err=True)


def format_pagination_hint(response: Any, fmt: str) -> None:
    """페이지네이션 힌트를 출력한다."""
    if fmt == "json":
        return
    if hasattr(response, "next_page_results") and response.next_page_results:
        cursor = getattr(response, "next_cursor", "")
        total = getattr(response, "total_results", "?")
        click_echo_err(f"  다음 페이지: --cursor {cursor}  (총 {total}건)")
