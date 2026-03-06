"""Linear 프로바이더 전용 컨텍스트."""
from __future__ import annotations

from dataclasses import dataclass, field

import click

from oh_my_kanban.linear_client import LinearClient


@dataclass
class LinearContext:
    """Linear API 호출에 필요한 상태를 보관하는 컨텍스트."""

    _api_key: str
    team_id: str
    output: str = "table"
    _client: LinearClient | None = field(default=None, repr=False)

    @property
    def client(self) -> LinearClient:
        """Linear API 클라이언트를 반환한다. api_key 없으면 UsageError."""
        if not self._api_key:
            raise click.UsageError(
                "LINEAR_API_KEY가 설정되지 않았습니다.\n"
                "환경변수: export LINEAR_API_KEY=lin_api_...\n"
                "설정: omk config set linear_api_key lin_api_..."
            )
        if self._client is None:
            self._client = LinearClient(self._api_key)
        return self._client

    def require_team(self) -> str:
        """team_id가 없으면 UsageError를 발생시킨다."""
        if not self.team_id:
            raise click.UsageError(
                "--team TEAM_ID 옵션 또는 LINEAR_TEAM_ID 환경변수를 설정하세요."
            )
        return self.team_id
