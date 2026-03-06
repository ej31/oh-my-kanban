"""CLI 컨텍스트: PlaneClient + 설정을 커맨드 간 전달."""

from __future__ import annotations

from dataclasses import dataclass, field

import click
from plane import PlaneClient


@dataclass
class CliContext:
    """Click pass_obj로 전달되는 전역 컨텍스트.

    client는 처음 사용 시 lazy 생성 (--help 시 API 키 불필요).
    """

    _base_url: str
    _api_key: str
    workspace: str
    project: str | None
    output: str  # "json" | "table" | "plain"
    _client: PlaneClient | None = field(default=None, repr=False)

    @property
    def client(self) -> PlaneClient:
        """PlaneClient를 lazy 생성한다."""
        if self._client is None:
            if not self._api_key:
                raise click.UsageError(
                    "API 키가 필요합니다. 다음 중 하나를 사용하세요:\n"
                    "  PLANE_API_KEY 환경변수\n"
                    "  ~/.config/oh-my-kanban/config.toml의 api_key\n"
                    "  plane config init 으로 설정"
                )
            self._client = PlaneClient(
                base_url=self._base_url,
                api_key=self._api_key,
            )
        return self._client

    def require_project(self) -> str:
        """project_id가 필요한 커맨드에서 호출. 없으면 명확한 에러."""
        if not self.project:
            raise click.UsageError(
                "Project is required. Use one of:\n"
                "  --project <UUID>\n"
                "  PLANE_PROJECT_ID env var\n"
                "  CLAUDE.md plane_context.project_id"
            )
        return self.project

    def require_workspace(self) -> str:
        """workspace 슬러그가 필요한 커맨드에서 호출. 없으면 명확한 에러."""
        if not self.workspace:
            raise click.UsageError(
                "Workspace slug is required. Set --workspace or PLANE_WORKSPACE_SLUG env var."
            )
        return self.workspace
