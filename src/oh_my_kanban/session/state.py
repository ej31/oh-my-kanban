"""세션 상태 데이터클래스 및 JSON 직렬화."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── 세션 상태 상수 ──────────────────────────────────────────────────────────
STATUS_ACTIVE = "active"
STATUS_COMPLETED = "completed"
STATUS_OPTED_OUT = "opted_out"

# ── 표시 길이 제한 상수 ─────────────────────────────────────────────────────
SUMMARY_DISPLAY_MAX = 200
SUMMARY_COMPACT_MAX = 150
SUMMARY_RESUME_MAX = 100
SUMMARY_SHORT_MAX = 50
SESSION_ID_DISPLAY_LEN = 8
FILES_DISPLAY_MAX = 10
FILES_COMPACT_MAX = 5
WORK_ITEMS_DISPLAY_MAX = 3
WORK_ITEMS_RESUME_MAX = 2
ACTIVE_SESSIONS_DISPLAY_MAX = 10
TIMELINE_DISPLAY_MAX = 50


def now_iso() -> str:
    """현재 UTC 시각을 ISO 포맷 문자열로 반환한다."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScopeState:
    """세션 목표/범위 정보."""

    summary: str = ""
    tokens: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    topic_scores: dict[str, int] = field(default_factory=dict)
    file_refs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    expanded_topics: list[str] = field(default_factory=list)


@dataclass
class PlaneContext:
    """Plane 연동 정보."""

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


@dataclass
class TimelineEvent:
    """세션 타임라인 이벤트."""

    timestamp: str
    # scope_init | prompt | drift_detected | scope_expanded | opted_out | compact_restored
    type: str
    summary: str
    drift_score: Optional[float] = None
    # drift_detected 이벤트의 레벨 (none|minor|significant|major). 파싱 없이 직접 참조
    drift_level: Optional[str] = None


@dataclass
class DriftResult:
    """드리프트 감지 결과."""

    score: float
    # 'none' | 'minor' | 'significant' | 'major'
    level: str
    components: dict
    suppressed: bool


@dataclass
class SessionStats:
    """세션 통계."""

    total_prompts: int = 0
    drift_warnings: int = 0
    scope_expansions: int = 0
    cooldown_remaining: int = 0
    files_touched: list[str] = field(default_factory=list)


@dataclass
class SessionConfig:
    """세션별 설정."""

    sensitivity: float = 0.5
    cooldown: int = 3
    auto_expand: bool = True


@dataclass
class SessionState:
    """세션 전체 상태. 로컬 JSON으로 저장."""

    session_id: str
    status: str = STATUS_ACTIVE  # STATUS_ACTIVE | STATUS_COMPLETED | STATUS_OPTED_OUT
    opted_out: bool = False
    tasks_deleted: bool = False
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    scope: ScopeState = field(default_factory=ScopeState)
    plane_context: PlaneContext = field(default_factory=PlaneContext)
    timeline: list[TimelineEvent] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    config: SessionConfig = field(default_factory=SessionConfig)

    def touch(self) -> None:
        """updated_at 갱신. 저장 직전에 명시적으로 호출한다."""
        self.updated_at = now_iso()

    def to_dict(self) -> dict:
        """JSON 직렬화용 dict 반환."""
        return asdict(self)

    def to_json(self) -> str:
        """JSON 문자열로 직렬화."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """dict에서 SessionState를 복원한다."""
        scope_data = data.get("scope", {})
        plane_data = data.get("plane_context", {})
        stats_data = data.get("stats", {})
        config_data = data.get("config", {})
        timeline_data = data.get("timeline", [])

        return cls(
            session_id=data["session_id"],
            status=data.get("status", STATUS_ACTIVE),
            opted_out=data.get("opted_out", False),
            tasks_deleted=data.get("tasks_deleted", False),
            created_at=data.get("created_at", now_iso()),
            updated_at=data.get("updated_at", now_iso()),
            scope=ScopeState(
                summary=scope_data.get("summary", ""),
                tokens=scope_data.get("tokens", []),
                topics=scope_data.get("topics", []),
                topic_scores=scope_data.get("topic_scores", {}),
                file_refs=scope_data.get("file_refs", []),
                keywords=scope_data.get("keywords", []),
                expanded_topics=scope_data.get("expanded_topics", []),
            ),
            plane_context=PlaneContext(
                project_id=plane_data.get("project_id", ""),
                work_item_ids=plane_data.get("work_item_ids", []),
                module_id=plane_data.get("module_id"),
                stale_work_item_ids=plane_data.get("stale_work_item_ids", []),
                focused_work_item_id=plane_data.get("focused_work_item_id"),
                last_comment_check=plane_data.get("last_comment_check"),
                known_comment_ids=plane_data.get("known_comment_ids", []),
                comment_poll_failures=plane_data.get("comment_poll_failures", 0),
                last_subtask_check=plane_data.get("last_subtask_check"),
                subtask_check_failures=plane_data.get("subtask_check_failures", 0),
                subtask_completion_nudged_ids=plane_data.get("subtask_completion_nudged_ids", []),
            ),
            timeline=[
                TimelineEvent(
                    # 필수 필드가 누락된 이벤트는 빈 문자열로 복원해 데이터 손실 방지
                    timestamp=e.get("timestamp", ""),
                    type=e.get("type", ""),
                    summary=e.get("summary", ""),
                    drift_score=e.get("drift_score"),
                    drift_level=e.get("drift_level"),
                )
                for e in timeline_data
                if isinstance(e, dict)
            ],
            stats=SessionStats(
                total_prompts=stats_data.get("total_prompts", 0),
                drift_warnings=stats_data.get("drift_warnings", 0),
                scope_expansions=stats_data.get("scope_expansions", 0),
                cooldown_remaining=stats_data.get("cooldown_remaining", 0),
                files_touched=stats_data.get("files_touched", []),
            ),
            config=SessionConfig(
                sensitivity=config_data.get("sensitivity", 0.5),
                cooldown=config_data.get("cooldown", 3),
                auto_expand=config_data.get("auto_expand", True),
            ),
        )
