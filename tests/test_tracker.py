"""session/tracker.py 단위 테스트."""

from __future__ import annotations

import os

import pytest

from oh_my_kanban.session.state import SessionState
from oh_my_kanban.session.tracker import extract_file_paths, update_files_touched


# ── extract_file_paths 테스트 ────────────────────────────────────────────────

def test_edit_tool_returns_file_path():
    """Edit 도구는 file_path를 리스트로 반환한다."""
    result = extract_file_paths("Edit", {"file_path": "/a/b/c.py"})
    assert result == ["/a/b/c.py"]


def test_write_tool_returns_file_path():
    """Write 도구는 file_path를 리스트로 반환한다."""
    result = extract_file_paths("Write", {"file_path": "/x/y/z.py"})
    assert result == ["/x/y/z.py"]


def test_multiedit_returns_multiple_paths():
    """MultiEdit은 edits 내 모든 file_path를 반환한다."""
    tool_input = {
        "edits": [
            {"file_path": "/a/foo.py", "old_string": "x", "new_string": "y"},
            {"file_path": "/b/bar.py", "old_string": "a", "new_string": "b"},
        ]
    }
    result = extract_file_paths("MultiEdit", tool_input)
    assert result == ["/a/foo.py", "/b/bar.py"]


def test_multiedit_empty_edits_returns_empty_list():
    """MultiEdit의 edits가 빈 리스트이면 빈 리스트를 반환한다."""
    result = extract_file_paths("MultiEdit", {"edits": []})
    assert result == []


def test_unknown_tool_returns_empty_list():
    """알 수 없는 도구명은 빈 리스트를 반환한다."""
    result = extract_file_paths("Bash", {"command": "ls"})
    assert result == []


def test_edit_without_file_path_key_returns_empty():
    """tool_input에 file_path 키가 없으면 빈 리스트를 반환한다."""
    result = extract_file_paths("Edit", {})
    assert result == []


def test_multiedit_edits_without_file_path_skipped():
    """MultiEdit edits 항목에 file_path가 없으면 건너뛴다."""
    tool_input = {
        "edits": [
            {"old_string": "x", "new_string": "y"},  # file_path 없음
            {"file_path": "/valid/path.py", "old_string": "a", "new_string": "b"},
        ]
    }
    result = extract_file_paths("MultiEdit", tool_input)
    assert result == ["/valid/path.py"]


# ── update_files_touched 테스트 ──────────────────────────────────────────────

def _make_state() -> SessionState:
    return SessionState(session_id="test-session")


def test_update_files_touched_basic_add():
    """새 경로가 files_touched에 추가된다."""
    state = _make_state()
    update_files_touched(state, ["/a/b.py"])
    assert "/a/b.py" in state.stats.files_touched


def test_update_files_touched_deduplication():
    """동일 경로를 두 번 추가해도 중복이 제거된다."""
    state = _make_state()
    update_files_touched(state, ["/a/b.py"])
    update_files_touched(state, ["/a/b.py"])
    assert state.stats.files_touched.count("/a/b.py") == 1


def test_update_files_touched_same_file_twice_in_one_call():
    """한 번의 호출에서 같은 파일이 두 번 포함되어도 1개만 저장된다."""
    state = _make_state()
    update_files_touched(state, ["/a/b.py", "/a/b.py"])
    assert state.stats.files_touched.count("/a/b.py") == 1


def test_update_files_touched_normpath():
    """경로에 ..가 포함되어도 normpath로 정규화된다."""
    state = _make_state()
    update_files_touched(state, ["a/b/../c.py"])
    normalized = os.path.normpath("a/b/../c.py")
    assert normalized in state.stats.files_touched
    assert "a/b/../c.py" not in state.stats.files_touched


def test_update_files_touched_empty_list_preserves_existing():
    """빈 file_paths를 전달하면 기존 목록이 유지된다."""
    state = _make_state()
    state.stats.files_touched = ["/existing/file.py"]
    update_files_touched(state, [])
    assert state.stats.files_touched == ["/existing/file.py"]
