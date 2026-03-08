"""Provider 공통 타입과 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProviderContext:
    """세션 훅/MCP가 공통으로 다루는 provider 상태."""

    provider_name: str = "plane"
    project_id: str = ""
    work_item_ids: list[str] = field(default_factory=list)
    module_id: Optional[str] = None
    stale_work_item_ids: list[str] = field(default_factory=list)
    focused_work_item_id: Optional[str] = None
    last_comment_check: Optional[str] = None
    known_comment_ids: list[str] = field(default_factory=list)
    comment_poll_failures: int = 0
    last_subtask_check: Optional[str] = None
    subtask_check_failures: int = 0
    subtask_completion_nudged_ids: list[str] = field(default_factory=list)
    auto_created_task_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict를 반환한다."""
        return {
            "provider_name": self.provider_name,
            "project_id": self.project_id,
            "work_item_ids": self.work_item_ids,
            "module_id": self.module_id,
            "stale_work_item_ids": self.stale_work_item_ids,
            "focused_work_item_id": self.focused_work_item_id,
            "last_comment_check": self.last_comment_check,
            "known_comment_ids": self.known_comment_ids,
            "comment_poll_failures": self.comment_poll_failures,
            "last_subtask_check": self.last_subtask_check,
            "subtask_check_failures": self.subtask_check_failures,
            "subtask_completion_nudged_ids": self.subtask_completion_nudged_ids,
            "auto_created_task_id": self.auto_created_task_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, provider_name: str = "plane") -> "ProviderContext":
        """dict에서 ProviderContext를 복원한다."""
        src = data or {}
        return cls(
            provider_name=str(src.get("provider_name") or provider_name or "plane"),
            project_id=str(src.get("project_id", "")),
            work_item_ids=[str(x) for x in src.get("work_item_ids", [])],
            module_id=src.get("module_id"),
            stale_work_item_ids=[str(x) for x in src.get("stale_work_item_ids", [])],
            focused_work_item_id=src.get("focused_work_item_id"),
            last_comment_check=src.get("last_comment_check"),
            known_comment_ids=[str(x) for x in src.get("known_comment_ids", [])],
            comment_poll_failures=int(src.get("comment_poll_failures", 0) or 0),
            last_subtask_check=src.get("last_subtask_check"),
            subtask_check_failures=int(src.get("subtask_check_failures", 0) or 0),
            subtask_completion_nudged_ids=[str(x) for x in src.get("subtask_completion_nudged_ids", [])],
            auto_created_task_id=src.get("auto_created_task_id"),
        )


class ProviderClient(ABC):
    """Provider별 세션 훅/MCP 작업을 캡슐화한다."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 이름을 반환한다."""

    @abstractmethod
    def build_compact_context(self, context: ProviderContext) -> tuple[str, list[str]]:
        """compact 복원용 컨텍스트 문자열과 실패 ID 목록을 반환한다."""

    @abstractmethod
    def post_comment(
        self,
        context: ProviderContext,
        comment: str,
        work_item_id: str = "",
    ) -> list[dict[str, Any]]:
        """Work Item/Issue에 댓글을 추가한다."""

    @abstractmethod
    def poll_comments(
        self,
        context: ProviderContext,
        known_ids: set[str],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """새 댓글 목록과 전체 댓글 ID 목록을 반환한다."""

    @abstractmethod
    def check_subtask_completion(self, context: ProviderContext) -> int | None:
        """하위 작업이 모두 완료되었는지 확인한다."""

    @abstractmethod
    def create_work_item(
        self,
        context: ProviderContext,
        title: str,
        description: str = "",
    ) -> dict[str, Any]:
        """새 Work Item/Issue를 생성하고 핵심 식별자를 반환한다."""

    @abstractmethod
    def switch_task(
        self,
        context: ProviderContext,
        new_task_title: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """기존 작업을 보류하고 새 작업으로 전환한다."""
