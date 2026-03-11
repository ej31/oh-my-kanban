"""Plane provider context."""

from __future__ import annotations

from dataclasses import dataclass, field

import click
from plane import PlaneClient


@dataclass
class PlaneContext:
    """Context object passed to Plane commands."""

    _base_url: str
    _api_key: str
    workspace: str
    project: str | None
    output: str
    _client: PlaneClient | None = field(default=None, repr=False)

    @property
    def client(self) -> PlaneClient:
        """Create PlaneClient lazily."""

        if self._client is None:
            if not self._api_key:
                raise click.UsageError(
                    "API 키가 필요합니다. 다음 중 하나를 사용하세요:\n"
                    "  PLANE_API_KEY 환경변수\n"
                    "  ~/.config/oh-my-kanban/config.toml의 plane.api_key\n"
                    "  omk config init 으로 설정"
                )
            self._client = PlaneClient(
                base_url=self._base_url,
                api_key=self._api_key,
            )
        return self._client

    def require_project(self) -> str:
        """Require project id."""

        if not self.project:
            raise click.UsageError(
                "Project is required. Use one of:\n"
                "  omk plane --project <UUID> <command>\n"
                "  PLANE_PROJECT_ID env var\n"
                "  CLAUDE.md plane_context.project_id"
            )
        return self.project

    def require_workspace(self) -> str:
        """Require workspace slug."""

        if not self.workspace:
            raise click.UsageError(
                "Workspace slug is required. Set omk plane --workspace or PLANE_WORKSPACE_SLUG."
            )
        return self.workspace


CliContext = PlaneContext

