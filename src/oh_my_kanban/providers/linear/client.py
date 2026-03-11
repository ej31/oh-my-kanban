"""Linear GraphQL API 클라이언트."""
from __future__ import annotations

import click
import httpx

from oh_my_kanban.linear_errors import LinearGraphQLError, LinearHttpError


class LinearClient:
    """Linear GraphQL API와 통신하는 클라이언트."""

    GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str,
        base_url: str = GRAPHQL_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key는 빈 문자열일 수 없습니다.")
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def execute(self, query: str, variables: dict | None = None) -> dict:
        """GraphQL 쿼리를 실행하고 data 딕셔너리를 반환한다."""
        try:
            response = self._client.post("", json={"query": query, "variables": variables or {}})
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LinearHttpError(e.response.status_code, str(e)) from e
        body = response.json()
        if errors := body.get("errors"):
            raise LinearGraphQLError(errors)
        return body.get("data", {})

    def paginate_relay(
        self,
        query: str,
        variables: dict | None,
        path: str,
        max_pages: int = 500,
    ) -> list[dict]:
        """Relay 스타일 cursor 페이지네이션을 자동 순회한다."""
        variables = dict(variables or {})
        results: list[dict] = []
        for _ in range(max_pages):
            data = self.execute(query, variables)
            # path로 connection 접근 (예: "issues", "team.issues")
            conn = data
            for key in path.split("."):
                conn = conn[key]
            results.extend(conn.get("nodes", []))
            page_info = conn.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            variables["after"] = page_info["endCursor"]
        else:
            click.echo(f"경고: 최대 페이지 수({max_pages})에 도달했습니다.", err=True)
        return results

    def close(self) -> None:
        """httpx 클라이언트를 닫는다."""
        self._client.close()
