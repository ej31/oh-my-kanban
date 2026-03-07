"""Linear GraphQL API 클라이언트."""
from __future__ import annotations

import random
import time

import click
import httpx

from oh_my_kanban.linear_errors import LinearGraphQLError, LinearHttpError


class LinearClient:
    """Linear GraphQL API와 통신하는 클라이언트."""

    GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=5.0, read=30.0)

    # 재시도 대상 상태 코드
    _RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
    _MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        base_url: str = GRAPHQL_ENDPOINT,
        timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key는 빈 문자열일 수 없습니다.")
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def execute(self, query: str, variables: dict | None = None) -> dict:
        """GraphQL 쿼리를 실행하고 data 딕셔너리를 반환한다.

        5xx/429 응답 시 최대 3회 재시도한다 (exponential backoff + jitter).
        Retry-After 헤더가 있으면 해당 값을 우선 사용한다.
        """
        last_exc: httpx.HTTPStatusError | None = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                response = self._client.post(
                    "", json={"query": query, "variables": variables or {}}
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code in self._RETRYABLE_STATUS and attempt < self._MAX_RETRIES:
                    # Retry-After 헤더 우선 사용, 없으면 exponential backoff + jitter
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = float(retry_after)
                        except ValueError:
                            wait = 2 ** attempt + random.uniform(0, 1)
                    else:
                        wait = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(min(wait, 30.0))  # 최대 30초 대기
                    last_exc = e
                    continue
                raise LinearHttpError(e.response.status_code, str(e)) from e

            body = response.json()
            if errors := body.get("errors"):
                raise LinearGraphQLError(errors)
            return body.get("data", {})

        # 모든 재시도 실패
        if last_exc is not None:
            raise LinearHttpError(
                last_exc.response.status_code,
                f"최대 재시도 횟수({self._MAX_RETRIES})를 초과했습니다: {last_exc}",
            ) from last_exc
        raise RuntimeError("Unexpected retry loop exit")

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
