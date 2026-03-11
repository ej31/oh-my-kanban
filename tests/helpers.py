"""테스트 공통 헬퍼 함수."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


def paginated(items: list[Any]) -> MagicMock:
    """페이지네이션 응답 mock을 생성한다."""
    resp = MagicMock()
    resp.results = items
    resp.next_page_results = False
    return resp
