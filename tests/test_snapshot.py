"""US-002: Snapshot tooling 테스트.

세션 스냅샷 저장/조회/복원 기능을 검증한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from oh_my_kanban.session.snapshot import (
    SNAPSHOTS_DIR,
    SnapshotMeta,
    _validate_snapshot_id,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)
from oh_my_kanban.session.state import (
    PlaneContext,
    ScopeState,
    SessionState,
    SessionStats,
)


def _make_state(session_id: str = "snap-test-001") -> SessionState:
    """테스트용 SessionState를 생성한다."""
    state = SessionState(session_id=session_id)
    state.scope = ScopeState(summary="스냅샷 테스트 작업", topics=["snapshot"])
    state.stats = SessionStats(total_prompts=3, files_touched=["a.py"])
    state.plane_context = PlaneContext(project_id="proj-1", work_item_ids=["wi-1"])
    return state


# ── save_snapshot ──────────────────────────────────────────────────────────────


class TestSaveSnapshot:
    """save_snapshot 함수 테스트."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """스냅샷 저장 시 JSON 파일이 생성되어야 한다."""
        with patch("oh_my_kanban.session.snapshot.SNAPSHOTS_DIR", tmp_path):
            with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
                path = save_snapshot(_make_state())
                assert path.exists()
                assert path.suffix == ".json"

    def test_saved_snapshot_contains_version(self, tmp_path: Path) -> None:
        """저장된 스냅샷에 snapshot_version 필드가 포함되어야 한다."""
        with patch("oh_my_kanban.session.snapshot.SNAPSHOTS_DIR", tmp_path):
            with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
                path = save_snapshot(_make_state())
                data = json.loads(path.read_text(encoding="utf-8"))
                assert data["snapshot_version"] == 1
                assert "snapshot_created_at" in data

    def test_saved_snapshot_contains_state(self, tmp_path: Path) -> None:
        """저장된 스냅샷에 세션 상태가 포함되어야 한다."""
        with patch("oh_my_kanban.session.snapshot.SNAPSHOTS_DIR", tmp_path):
            with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
                path = save_snapshot(_make_state("my-session-123"))
                data = json.loads(path.read_text(encoding="utf-8"))
                assert data["session_id"] == "my-session-123"
                assert data["scope"]["summary"] == "스냅샷 테스트 작업"


# ── list_snapshots ─────────────────────────────────────────────────────────────


class TestListSnapshots:
    """list_snapshots 함수 테스트."""

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        """스냅샷이 없으면 빈 리스트를 반환해야 한다."""
        with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
            assert list_snapshots() == []

    def test_list_returns_metadata(self, tmp_path: Path) -> None:
        """스냅샷 목록에 메타데이터가 포함되어야 한다."""
        # 직접 스냅샷 파일 생성
        snap_data = _make_state("list-test-001").to_dict()
        snap_data["snapshot_version"] = 1
        snap_data["snapshot_created_at"] = "2026-01-01T00:00:00+00:00"
        snap_file = tmp_path / "list_test_20260101T000000.json"
        snap_file.write_text(json.dumps(snap_data, ensure_ascii=False), encoding="utf-8")

        with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
            result = list_snapshots()
            assert len(result) == 1
            assert result[0].session_id == "list-test-001"
            assert result[0].scope_summary == "스냅샷 테스트 작업"


# ── load_snapshot ──────────────────────────────────────────────────────────────


class TestLoadSnapshot:
    """load_snapshot 함수 테스트."""

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """존재하지 않는 스냅샷은 None을 반환해야 한다."""
        with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
            assert load_snapshot("nonexistent_snap") is None

    def test_load_restores_state(self, tmp_path: Path) -> None:
        """스냅샷 로드 시 SessionState로 복원되어야 한다."""
        snap_data = _make_state("restore-001").to_dict()
        snap_data["snapshot_version"] = 1
        snap_data["snapshot_created_at"] = "2026-01-01T00:00:00+00:00"
        snap_file = tmp_path / "my_snapshot.json"
        snap_file.write_text(json.dumps(snap_data, ensure_ascii=False), encoding="utf-8")

        with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
            state = load_snapshot("my_snapshot")
            assert state is not None
            assert state.session_id == "restore-001"
            assert state.scope.summary == "스냅샷 테스트 작업"

    def test_load_removes_snapshot_metadata(self, tmp_path: Path) -> None:
        """복원된 SessionState에 스냅샷 메타데이터 필드가 없어야 한다."""
        snap_data = _make_state().to_dict()
        snap_data["snapshot_version"] = 1
        snap_data["snapshot_created_at"] = "2026-01-01T00:00:00+00:00"
        snap_file = tmp_path / "clean_snap.json"
        snap_file.write_text(json.dumps(snap_data, ensure_ascii=False), encoding="utf-8")

        with patch("oh_my_kanban.session.snapshot._snapshots_dir", return_value=tmp_path):
            state = load_snapshot("clean_snap")
            assert state is not None
            state_dict = state.to_dict()
            assert "snapshot_version" not in state_dict
            assert "snapshot_created_at" not in state_dict


# ── _validate_snapshot_id ──────────────────────────────────────────────────────


class TestValidateSnapshotId:
    """snapshot_id 검증 테스트."""

    def test_valid_id(self) -> None:
        """유효한 snapshot_id는 예외 없이 통과해야 한다."""
        _validate_snapshot_id("snap_20260101T000000")

    def test_empty_id_raises(self) -> None:
        """빈 snapshot_id는 ValueError를 발생시켜야 한다."""
        with pytest.raises(ValueError, match="비어있습니다"):
            _validate_snapshot_id("")

    def test_path_traversal_raises(self) -> None:
        """경로 트래버설 문자가 포함된 id는 ValueError를 발생시켜야 한다."""
        with pytest.raises(ValueError, match="허용되지 않는 문자"):
            _validate_snapshot_id("../../etc/passwd")

    def test_too_long_raises(self) -> None:
        """너무 긴 snapshot_id는 ValueError를 발생시켜야 한다."""
        with pytest.raises(ValueError, match="너무 깁니다"):
            _validate_snapshot_id("a" * 201)
