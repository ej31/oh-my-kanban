"""PostToolUse 훅: 수정된 파일을 세션 상태에 기록한다.

async=True이므로 Claude Code를 블로킹하지 않는다.
항상 exit 0 (fail-open). 세션 추적에 오류가 있어도 Claude는 계속 동작한다.

stdin: {"session_id": "...", "tool_name": "Edit|Write|MultiEdit", "tool_input": {...}}
"""

from __future__ import annotations

import contextlib
import fcntl
import re
import sys

from oh_my_kanban.config import load_config
from oh_my_kanban.hooks.common import (
    PLANE_API_TIMEOUT,
    exit_fail_open,
    get_session_id,
    output_context,
    read_hook_input,
    sanitize_comment,
)
from oh_my_kanban.session.manager import _session_path, load_session, save_session
from oh_my_kanban.session.tracker import extract_file_paths, update_files_touched

# git commit 해시 추출 패턴
_COMMIT_HASH_RE = re.compile(r'\[[\w/.-]+\s+([0-9a-f]{7,40})\]')


def _detect_git_commit(tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """Bash 도구 입력에서 git commit 명령을 감지한다."""
    if tool_name != "Bash":
        return False, ""
    command = str(tool_input.get("command", ""))
    # git commit이 포함되고, --no-commit 플래그가 없는 경우에만 감지
    if "git commit" in command and "--no-commit" not in command:
        return True, command
    return False, ""


def _extract_commit_hash(tool_response: str) -> str:
    """git commit 출력에서 커밋 해시를 추출한다."""
    if not tool_response:
        return ""
    match = _COMMIT_HASH_RE.search(str(tool_response))
    return match.group(1) if match else ""


def _post_commit_comment(state, commit_hash: str, commit_command: str) -> None:
    """WI에 커밋 정보 댓글을 추가하고 Claude에게 additionalContext를 주입한다 (ST-24)."""
    try:
        import httpx
    except ImportError:
        return

    cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return

    wi_ids = state.plane_context.work_item_ids
    project_id = state.plane_context.project_id or cfg.project_id
    if not wi_ids or not project_id:
        return

    focused = state.plane_context.focused_work_item_id
    target_ids = [focused] if focused else wi_ids[:1]

    hash_short = commit_hash[:7] if commit_hash else "(알 수 없음)"
    comment_body = sanitize_comment(
        f"## 커밋 기록\n\n**커밋**: `{hash_short}`\n"
        f"*omk에 의해 자동 기록됨*"
    )

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key, "Content-Type": "application/json"}

    for wi_id in target_ids:
        url = (
            f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
            f"/projects/{project_id}/issues/{wi_id}/comments/"
        )
        try:
            with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
                client.post(url, headers=headers, json={"comment_html": comment_body})
        except Exception as e:
            print(
                f"[omk] 커밋 댓글 추가 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
                file=sys.stderr,
            )
            continue

    # Claude에게 커밋 기록 완료 additionalContext 주입
    wi_id_short = target_ids[0][:8] if target_ids else ""
    output_context(
        "PostToolUse",
        f"[omk] 커밋 {hash_short}을 Work Item({wi_id_short}...)에 자동 기록했습니다.",
    )


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

        tool_response = str(hook_input.get("tool_response", "") or "")

        file_paths = extract_file_paths(tool_name, tool_input)

        # ST-24: git commit 감지
        is_git_commit, commit_command = _detect_git_commit(tool_name, tool_input)
        commit_hash = _extract_commit_hash(tool_response) if is_git_commit else ""

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

        # ST-24: WI에 커밋 댓글 추가 (잠금 밖에서 수행, fail-open)
        if is_git_commit and state.plane_context.work_item_ids:
            try:
                _post_commit_comment(state, commit_hash, commit_command)
            except Exception as e:
                print(
                    f"[omk] 커밋 추적 실패 (fail-open): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )

    except Exception as e:
        print(f"[omk] PostToolUse 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        exit_fail_open()


if __name__ == "__main__":
    main()
