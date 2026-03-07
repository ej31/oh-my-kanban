"""Linear 프로바이더 전용 컨텍스트."""
from __future__ import annotations

from dataclasses import dataclass, field

import click
import httpx

from oh_my_kanban.linear_client import LinearClient
from oh_my_kanban.linear_errors import LinearGraphQLError, LinearHttpError, LinearResponseParseError


@dataclass
class LinearContext:
    """Linear API 호출에 필요한 상태를 보관하는 컨텍스트."""

    _api_key: str
    team_id: str
    output: str = "table"
    _client: LinearClient | None = field(default=None, repr=False)
    _validated_team_id: str | None = field(default=None, repr=False)

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

    def validate_team(self) -> str:
        """team_id가 실제로 존재하는지 검증한다. 캐시하여 중복 호출 방지."""
        team_id = self.require_team()
        if self._validated_team_id == team_id:
            return team_id
        try:
            result = self.client.execute(
                "query($id: String!) { team(id: $id) { id name } }",
                variables={"id": team_id},
            )
            if not result.get("team"):
                raise click.UsageError(
                    f"Linear 팀을 찾을 수 없습니다 (team_id={team_id}). "
                    "삭제되었거나 잘못된 ID일 수 있습니다.\n"
                    "확인: omk linear team list"
                )
            self._validated_team_id = team_id
        except click.UsageError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError, LinearHttpError, LinearGraphQLError, LinearResponseParseError) as e:
            # 검증 실패가 작업을 차단하지 않도록 — 경고만 출력
            click.echo(f"경고: 팀 검증 실패 ({type(e).__name__}). 후속 명령에서 에러가 발생할 수 있습니다.", err=True)
        return team_id
