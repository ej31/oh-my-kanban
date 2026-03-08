"""PostToolUse 훅용 파일 추적 순수 로직."""

from __future__ import annotations

import os

from oh_my_kanban.session.state import SessionState


def extract_file_paths(tool_name: str, tool_input: dict) -> list[str]:
    """tool_name과 tool_input에서 수정된 파일 경로를 추출한다."""
    try:
        if tool_name in ("Edit", "Write"):
            path = tool_input.get("file_path")
            return [path] if path else []
        elif tool_name == "MultiEdit":
            edits = tool_input.get("edits", [])
            paths = []
            for edit in edits:
                if isinstance(edit, dict):
                    p = edit.get("file_path")
                    if p:
                        paths.append(p)
            return paths
        return []
    except (KeyError, TypeError):
        return []


def update_files_touched(state: SessionState, file_paths: list[str]) -> None:
    """file_paths를 state.stats.files_touched에 중복 없이 추가한다."""
    normalized = [os.path.normpath(p) for p in file_paths if p]
    existing = list(state.stats.files_touched)
    merged = list(dict.fromkeys(existing + normalized))
    state.stats.files_touched = merged
