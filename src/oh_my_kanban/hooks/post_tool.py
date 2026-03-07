"""PostToolUse 훅: 수정된 파일을 세션 상태에 기록한다.

async=True이므로 Claude Code를 블로킹하지 않는다.
항상 exit 0 (fail-open). 세션 추적에 오류가 있어도 Claude는 계속 동작한다.

stdin: {"session_id": "...", "tool_name": "Edit|Write|MultiEdit", "tool_input": {...}}
"""

from __future__ import annotations

import contextlib
import fcntl
import sys

from oh_my_kanban.hooks.common import exit_fail_open, get_session_id, read_hook_input
from oh_my_kanban.session.manager import _session_path, load_session, save_session
from oh_my_kanban.session.tracker import extract_file_paths, update_files_touched


@contextlib.contextmanager
def _session_write_lock(session_id: str):
    """세션 파일에 대한 배타적 잠금 — async 훅 동시 실행 시 lost-update 방지."""
    lock_path = _session_path(session_id).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def main() -> None:
    """PostToolUse 훅 메인. 예외는 모두 catch해 fail-open으로 처리한다."""
    try:
        hook_input = read_hook_input()
        session_id = get_session_id(hook_input)
        if not session_id:
            exit_fail_open()
            return

        tool_name = str(hook_input.get("tool_name", ""))
        tool_input = hook_input.get("tool_input", {})
        if not isinstance(tool_input, dict):
            tool_input = {}

        file_paths = extract_file_paths(tool_name, tool_input)

        # 배타적 잠금 후 reload → 수정 → save (lost-update 방지)
        with _session_write_lock(session_id):
            state = load_session(session_id)
            if state is None:
                exit_fail_open()
                return
            if state.opted_out:
                exit_fail_open()
                return
            update_files_touched(state, file_paths)
            save_session(state)

    except Exception as e:
        print(f"[omk] PostToolUse 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        exit_fail_open()


if __name__ == "__main__":
    main()
