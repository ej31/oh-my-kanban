"""PostToolUse 훅: 수정된 파일을 세션 상태에 기록한다.

async=True이므로 Claude Code를 블로킹하지 않는다.
항상 exit 0 (fail-open). 세션 추적에 오류가 있어도 Claude는 계속 동작한다.

stdin: {"session_id": "...", "tool_name": "Edit|Write|MultiEdit", "tool_input": {...}}
"""

from __future__ import annotations

import sys

from oh_my_kanban.hooks.common import exit_fail_open, get_session_id, read_hook_input
from oh_my_kanban.session.manager import load_session, save_session
from oh_my_kanban.session.tracker import extract_file_paths, update_files_touched


def main() -> None:
    """PostToolUse 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
    try:
        hook_input = read_hook_input()
        session_id = get_session_id(hook_input)
        if not session_id:
            exit_fail_open()
            return

        state = load_session(session_id)
        if state is None:
            exit_fail_open()
            return

        if state.opted_out:
            exit_fail_open()
            return

        tool_name = str(hook_input.get("tool_name", ""))
        tool_input = hook_input.get("tool_input", {})
        if not isinstance(tool_input, dict):
            tool_input = {}

        file_paths = extract_file_paths(tool_name, tool_input)
        update_files_touched(state, file_paths)
        save_session(state)

    except Exception as e:
        print(f"[omk] PostToolUse 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        exit_fail_open()


if __name__ == "__main__":
    main()
