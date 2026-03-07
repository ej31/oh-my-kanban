"""CLI 컨텍스트: PlaneClient + 설정을 커맨드 간 전달."""

from __future__ import annotations

from dataclasses import dataclass, field

import click
import requests
from plane import PlaneClient
from plane.config import RetryConfig
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _mount_retry_adapters(client: PlaneClient) -> None:
    """PlaneClient의 모든 리소스 세션에 retry 어댑터를 장착한다.

    PlaneClient 생성자가 retry 파라미터를 지원하지 않으므로,
    생성 후 각 리소스의 requests.Session에 직접 어댑터를 마운트한다.
    """
    cfg = client.config
    if not cfg.retry:
        return
    retry = Retry(
        total=cfg.retry.total,
        backoff_factor=cfg.retry.backoff_factor,
        status_forcelist=cfg.retry.status_forcelist,
        allowed_methods=cfg.retry.allowed_methods,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    for attr in vars(client).values():
        session = getattr(attr, "session", None)
        if isinstance(session, requests.Session):
            session.mount("http://", adapter)
            session.mount("https://", adapter)


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
    _validated_project: bool = field(default=False, repr=False)

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
            # Plane SDK RetryConfig 활성화 (429/5xx 자동 재시도)
            self._client.config.retry = RetryConfig()
            self._client.config.timeout = (5.0, 30.0)
            _mount_retry_adapters(self._client)
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

    def validate_project(self) -> str:
        """project_id가 실제로 존재하는지 검증한다. 캐시하여 중복 호출 방지."""
        project_id = self.require_project()
        if self._validated_project:
            return project_id
        try:
            ws = self.require_workspace()
            self.client.projects.get(
                workspace_slug=ws,
                project_id=project_id,
            )
            self._validated_project = True
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status == 404:
                raise click.UsageError(
                    f"프로젝트를 찾을 수 없습니다 (project_id={project_id}). "
                    "삭제되었거나 잘못된 ID일 수 있습니다.\n"
                    "확인: omk plane project list"
                ) from e
            raise
        return project_id
