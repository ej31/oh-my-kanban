"""Plane ProviderClient 구현 (stub — 향후 완전 구현 예정)."""

from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING, Any

from oh_my_kanban.provider import ProviderClient

if TYPE_CHECKING:
    from oh_my_kanban.config import Config
    from oh_my_kanban.provider import ProviderContext

_SLUG_RE = _re.compile(r'^[A-Za-z0-9_-]{1,64}$')
_UUID_RE = _re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
    _re.IGNORECASE,
)


def _validate_slug(value: str, label: str = "slug") -> str:
    """경로 세그먼트로 안전한 slug인지 검증한다."""
    if not _SLUG_RE.match(value):
        raise ValueError(f"유효하지 않은 {label}: {value!r}")
    return value


def _validate_uuid(value: str, label: str = "UUID") -> str:
    """UUID 형식인지 검증한다."""
    if not _UUID_RE.match(value):
        raise ValueError(f"유효하지 않은 {label}: {value!r}")
    return value


class PlaneProviderClient(ProviderClient):
    """Plane API를 통해 Work Item을 관리하는 클라이언트."""

    def __init__(self, cfg: "Config") -> None:
        self._cfg = cfg

    @property
    def name(self) -> str:
        return "plane"

    def build_compact_context(self, context: "ProviderContext") -> tuple[str, list[str]]:
        from oh_my_kanban.session.plane_context_builder import build_plane_context
        cfg = self._cfg
        project_id = context.project_id or cfg.project_id
        if not project_id or not cfg.api_key or not cfg.workspace_slug:
            return "", []
        return build_plane_context(
            work_item_ids=context.work_item_ids,
            project_id=project_id,
            base_url=cfg.base_url,
            api_key=cfg.api_key,
            workspace_slug=cfg.workspace_slug,
        )

    def post_comment(
        self,
        context: "ProviderContext",
        comment: str,
        work_item_id: str = "",
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("PlaneProviderClient.post_comment는 아직 구현되지 않았습니다.")

    def poll_comments(
        self,
        context: "ProviderContext",
        known_ids: set[str],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        raise NotImplementedError("PlaneProviderClient.poll_comments는 아직 구현되지 않았습니다.")

    def check_subtask_completion(self, context: "ProviderContext") -> int | None:
        raise NotImplementedError("PlaneProviderClient.check_subtask_completion는 아직 구현되지 않았습니다.")

    def create_work_item(
        self,
        context: "ProviderContext",
        title: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Plane API로 새 Issue를 생성하고 id를 포함한 dict를 반환한다."""
        import httpx

        cfg = self._cfg
        project_id = context.project_id or cfg.project_id
        if not project_id or not cfg.api_key or not cfg.workspace_slug:
            raise RuntimeError(
                "Plane WI 생성에 필요한 설정(project_id, api_key, workspace_slug)이 누락되었습니다."
            )

        base_url = cfg.base_url.rstrip("/")
        url = (
            f"{base_url}/api/v1/workspaces/{_validate_slug(cfg.workspace_slug, 'workspace_slug')}"
            f"/projects/{_validate_uuid(project_id, 'project_id')}/issues/"
        )
        headers = {"X-API-Key": cfg.api_key, "Content-Type": "application/json"}
        payload: dict[str, Any] = {"name": title}
        if description:
            payload["description_html"] = description

        with httpx.Client(timeout=30.0, follow_redirects=False) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def switch_task(
        self,
        context: "ProviderContext",
        new_task_title: str,
        reason: str = "",
    ) -> dict[str, Any]:
        raise NotImplementedError("PlaneProviderClient.switch_task는 아직 구현되지 않았습니다.")
