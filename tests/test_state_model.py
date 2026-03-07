"""PlaneContext 확장 필드 직렬화/역직렬화 테스트."""
import pytest
from oh_my_kanban.session.state import (
    PlaneContext, SessionState, ErrorThrottle,
)


def test_plane_context_new_fields_defaults():
    ctx = PlaneContext()
    assert ctx.main_task_id is None
    assert ctx.focused_work_item_id is None
    assert ctx.last_comment_check is None
    assert ctx.known_comment_ids == []
    assert ctx.stale_work_item_ids == []


def test_plane_context_serialization():
    ctx = PlaneContext(
        project_id="proj-1",
        work_item_ids=["wi-1"],
        main_task_id="mt-1",
        focused_work_item_id="wi-1",
        known_comment_ids=["c-1", "c-2"],
        stale_work_item_ids=["wi-old"],
    )
    from dataclasses import asdict
    d = asdict(ctx)
    assert d["main_task_id"] == "mt-1"
    assert d["known_comment_ids"] == ["c-1", "c-2"]


def test_session_state_no_tasks_deleted():
    """tasks_deleted 필드가 SessionState에 없어야 한다."""
    state = SessionState(session_id="test-123")
    assert not hasattr(state, "tasks_deleted")


def test_from_dict_backward_compat():
    """이전 버전 JSON(tasks_deleted 있음)도 복원 가능해야 한다."""
    old_data = {
        "session_id": "old-session",
        "tasks_deleted": True,  # 이전 버전 필드 - 무시되어야 함
        "plane_context": {
            "project_id": "proj-1",
            "work_item_ids": [],
        }
    }
    state = SessionState.from_dict(old_data)
    assert state.session_id == "old-session"
    assert state.plane_context.main_task_id is None
    assert state.plane_context.known_comment_ids == []


def test_from_dict_new_fields():
    """새 PlaneContext 필드가 올바르게 복원된다."""
    data = {
        "session_id": "new-session",
        "plane_context": {
            "project_id": "proj-1",
            "work_item_ids": ["wi-1"],
            "main_task_id": "mt-1",
            "focused_work_item_id": "wi-1",
            "known_comment_ids": ["c-1"],
            "stale_work_item_ids": ["wi-dead"],
        }
    }
    state = SessionState.from_dict(data)
    assert state.plane_context.main_task_id == "mt-1"
    assert state.plane_context.known_comment_ids == ["c-1"]
    assert state.plane_context.stale_work_item_ids == ["wi-dead"]


def test_error_throttle_defaults():
    t = ErrorThrottle()
    assert t.category == ""
    assert t.last_error_at is None
    assert t.cooldown_seconds == 300


def test_session_state_error_throttle():
    state = SessionState(session_id="x")
    assert state.error_throttle is None
