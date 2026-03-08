"""US-001: Recording mode behavior 테스트.

upload_level 설정에 따라 session_end 훅의 댓글 동작이 달라지는지 검증한다.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from oh_my_kanban.config import Config
from oh_my_kanban.hooks.session_end import (
    UPLOAD_LEVEL_FULL,
    UPLOAD_LEVEL_METADATA,
    UPLOAD_LEVEL_NONE,
    _VALID_UPLOAD_LEVELS,
    _build_full_comment,
    _build_summary_comment,
    main,
)
from oh_my_kanban.session.state import (
    PlaneContext,
    ScopeState,
    SessionState,
    SessionStats,
    TimelineEvent,
)


def _make_state(
    session_id: str = "test-session-001",
    work_item_ids: list[str] | None = None,
    project_id: str = "proj-123",
) -> SessionState:
    """테스트용 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.plane_context = PlaneContext(
        project_id=project_id,
        work_item_ids=work_item_ids or ["wi-001"],
    )
    state.scope = ScopeState(summary="테스트 작업", topics=["auth", "api"])
    state.stats = SessionStats(
        total_prompts=5,
        drift_warnings=1,
        scope_expansions=0,
        files_touched=["src/main.py", "tests/test_main.py"],
    )
    state.timeline = [
        TimelineEvent(
            timestamp="2026-01-01T00:00:00+00:00",
            type="scope_init",
            summary="세션 시작",
        ),
        TimelineEvent(
            timestamp="2026-01-01T00:05:00+00:00",
            type="prompt",
            summary="코드 수정",
        ),
    ]
    return state


# ── 상수 검증 ──────────────────────────────────────────────────────────────────


def test_valid_upload_levels() -> None:
    """유효한 upload_level 집합이 올바르게 정의되어 있어야 한다."""
    assert _VALID_UPLOAD_LEVELS == {"none", "metadata", "full"}


# ── _build_full_comment 검증 ───────────────────────────────────────────────────


def test_build_full_comment_includes_timeline() -> None:
    """full 모드 댓글에 타임라인 이벤트가 포함되어야 한다."""
    state = _make_state()
    comment = _build_full_comment(state)
    assert "타임라인" in comment
    assert "scope_init" in comment
    assert "세션 시작" in comment
    assert "코드 수정" in comment


def test_build_full_comment_includes_summary() -> None:
    """full 모드 댓글에 기존 메타데이터 요약도 포함되어야 한다."""
    state = _make_state()
    comment = _build_full_comment(state)
    assert "테스트 작업" in comment
    assert "요청 횟수" in comment


# ── none 모드: 댓글 API 호출 없음 ──────────────────────────────────────────────


@patch("oh_my_kanban.hooks.session_end.save_session")
@patch("oh_my_kanban.hooks.session_end._post_plane_comment")
@patch("oh_my_kanban.hooks.session_end.load_config")
@patch("oh_my_kanban.hooks.session_end.load_session")
@patch("oh_my_kanban.hooks.session_end.read_hook_input")
def test_none_mode_skips_comment(
    mock_read: MagicMock,
    mock_load: MagicMock,
    mock_cfg: MagicMock,
    mock_post: MagicMock,
    mock_save: MagicMock,
) -> None:
    """none 모드에서는 post_plane_comment가 호출되지 않아야 한다."""
    mock_read.return_value = {"session_id": "test-session"}
    mock_load.return_value = _make_state()
    cfg = Config(upload_level="none", api_key="key", workspace_slug="ws")
    mock_cfg.return_value = cfg

    main()

    mock_post.assert_not_called()
    mock_save.assert_called_once()


# ── metadata 모드: 기존 요약 댓글 ─────────────────────────────────────────────


@patch("oh_my_kanban.hooks.session_end.save_session")
@patch("oh_my_kanban.hooks.session_end._post_plane_comment")
@patch("oh_my_kanban.hooks.session_end.load_config")
@patch("oh_my_kanban.hooks.session_end.load_session")
@patch("oh_my_kanban.hooks.session_end.read_hook_input")
def test_metadata_mode_posts_summary(
    mock_read: MagicMock,
    mock_load: MagicMock,
    mock_cfg: MagicMock,
    mock_post: MagicMock,
    mock_save: MagicMock,
) -> None:
    """metadata 모드에서는 요약 댓글이 올라가야 한다."""
    mock_read.return_value = {"session_id": "test-session"}
    state = _make_state()
    mock_load.return_value = state
    cfg = Config(upload_level="metadata", api_key="key", workspace_slug="ws")
    mock_cfg.return_value = cfg

    main()

    mock_post.assert_called_once()
    comment = mock_post.call_args[0][1]
    assert "세션 종료" in comment
    # full 모드 전용 타임라인 섹션은 없어야 한다
    assert "타임라인" not in comment


# ── full 모드: 타임라인 포함 댓글 ──────────────────────────────────────────────


@patch("oh_my_kanban.hooks.session_end.save_session")
@patch("oh_my_kanban.hooks.session_end._post_plane_comment")
@patch("oh_my_kanban.hooks.session_end.load_config")
@patch("oh_my_kanban.hooks.session_end.load_session")
@patch("oh_my_kanban.hooks.session_end.read_hook_input")
def test_full_mode_posts_full_comment(
    mock_read: MagicMock,
    mock_load: MagicMock,
    mock_cfg: MagicMock,
    mock_post: MagicMock,
    mock_save: MagicMock,
) -> None:
    """full 모드에서는 타임라인 포함 상세 댓글이 올라가야 한다."""
    mock_read.return_value = {"session_id": "test-session"}
    state = _make_state()
    mock_load.return_value = state
    cfg = Config(upload_level="full", api_key="key", workspace_slug="ws")
    mock_cfg.return_value = cfg

    main()

    mock_post.assert_called_once()
    comment = mock_post.call_args[0][1]
    assert "타임라인" in comment
    assert "scope_init" in comment


# ── 잘못된 upload_level → metadata fallback ────────────────────────────────────


@patch("oh_my_kanban.hooks.session_end.save_session")
@patch("oh_my_kanban.hooks.session_end._post_plane_comment")
@patch("oh_my_kanban.hooks.session_end.load_config")
@patch("oh_my_kanban.hooks.session_end.load_session")
@patch("oh_my_kanban.hooks.session_end.read_hook_input")
def test_invalid_upload_level_fallback_to_none(
    mock_read: MagicMock,
    mock_load: MagicMock,
    mock_cfg: MagicMock,
    mock_post: MagicMock,
    mock_save: MagicMock,
) -> None:
    """잘못된 upload_level은 none으로 fallback되어 댓글을 올리지 않아야 한다 (안전 기본값)."""
    mock_read.return_value = {"session_id": "test-session"}
    state = _make_state()
    mock_load.return_value = state
    cfg = Config(upload_level="invalid_value", api_key="key", workspace_slug="ws")
    mock_cfg.return_value = cfg

    main()

    # none 폴백이므로 댓글이 올라가지 않아야 한다
    mock_post.assert_not_called()
