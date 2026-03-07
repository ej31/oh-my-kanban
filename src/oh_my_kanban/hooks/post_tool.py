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
    create_plane_http_client,
    exit_fail_open,
    get_session_id,
    output_context,
    output_system_message,
    read_hook_input,
    sanitize_comment,
)
from oh_my_kanban.session.manager import get_session_lock_path, load_session, save_session
from oh_my_kanban.session.tracker import extract_file_paths, update_files_touched

# git commit 해시 추출 패턴
_COMMIT_HASH_RE = re.compile(r'\[[\w/.-]+\s+([0-9a-f]{7,40})\]')
# 커밋 메시지에서 WI 식별자 패턴 (예: OMK-123, YCF-42, ABC-1)
_WI_IDENTIFIER_RE = re.compile(r'\b([A-Z]{2,6}-\d+)\b')
# 파일 핫스팟 임계값: 이 이상 세션에서 수정된 파일은 리팩토링 후보로 알림 (ST-31)
_HOTSPOT_SESSION_THRESHOLD = 5


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
    """WI에 커밋 정보 댓글을 추가하고 Claude에게 additionalContext를 주입한다 (ST-24).

    성공 시 stats.commit_hashes에 커밋 해시를 기록한다.
    """
    cfg = load_config()
    if not cfg.api_key or not cfg.workspace_slug:
        return

    wi_ids = state.plane_context.work_item_ids
    project_id = state.plane_context.project_id or cfg.project_id
    if not wi_ids or not project_id:
        return

    client = create_plane_http_client(cfg)
    if client is None:
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

    any_success = False
    with client as c:
        for wi_id in target_ids:
            url = (
                f"{base_url}/api/v1/workspaces/{cfg.workspace_slug}"
                f"/projects/{project_id}/issues/{wi_id}/comments/"
            )
            try:
                resp = c.post(url, headers=headers, json={"comment_html": comment_body})
                if resp.status_code in (200, 201):
                    any_success = True
                else:
                    print(
                        f"[omk] 커밋 댓글 HTTP {resp.status_code} (wi_id={wi_id!r})",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(
                    f"[omk] 커밋 댓글 추가 실패 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )
                continue

    # 커밋 해시를 세션 통계에 기록 — POST 성공 시에만 (ST-24)
    if commit_hash and any_success and commit_hash not in state.stats.commit_hashes:
        state.stats.commit_hashes.append(commit_hash)

    # Claude에게 커밋 기록 완료 additionalContext 주입
    wi_id_short = target_ids[0][:8] if target_ids else ""
    output_context(
        "PostToolUse",
        f"[omk] 커밋 {hash_short}을 Work Item({wi_id_short}...)에 자동 기록했습니다.",
    )


def _suggest_wi_link_from_commit(state, commit_command: str) -> None:
    """커밋 메시지에서 WI 식별자를 찾아 세션 연결을 Claude에게 제안한다 (ST-27).

    세션에 WI가 없을 때만 동작. 식별자 발견 시 additionalContext로 연결 제안.
    """
    if state.plane_context.work_item_ids:
        return  # 이미 WI가 연결됨 — ST-24가 처리

    identifiers = _WI_IDENTIFIER_RE.findall(commit_command)
    if not identifiers:
        return

    # 중복 제거, 최대 3개
    unique_ids = list(dict.fromkeys(identifiers))[:3]
    ids_str = ", ".join(unique_ids)

    output_context(
        "PostToolUse",
        f"[omk] 커밋 메시지에서 Work Item 식별자를 감지했습니다: {ids_str}\n"
        f"세션이 Work Item에 연결되지 않은 상태입니다.\n"
        f"/oh-my-kanban:focus {unique_ids[0]} 를 사용하여 세션을 연결할 수 있습니다.",
    )


def _get_file_session_counts(current_session_id: str) -> dict[str, int]:
    """과거 세션 데이터에서 파일별 수정 세션 수를 집계한다 (현재 세션 제외)."""
    from oh_my_kanban.session.manager import list_sessions

    counts: dict[str, int] = {}
    try:
        for session in list_sessions():
            if session.session_id == current_session_id:
                continue
            for f in session.stats.files_touched:
                counts[f] = counts.get(f, 0) + 1
    except Exception as e:
        print(f"[omk] 세션 집계 실패 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
    return counts


def _check_file_hotspot(state, file_paths: list[str]) -> None:
    """수정된 파일이 핫스팟(다수 세션에서 반복 수정)인지 확인하고 Claude에게 알린다 (ST-31).

    이미 알림을 보낸 파일은 건너뜀 (state.plane_context.hotspot_alerted_files로 추적).
    """
    if not file_paths:
        return

    # 이미 알림한 파일은 제외
    alerted = set(state.plane_context.hotspot_alerted_files)
    new_files = [f for f in file_paths if f not in alerted]
    if not new_files:
        return

    try:
        counts = _get_file_session_counts(state.session_id)
    except Exception:
        return

    for f in new_files:
        session_count = counts.get(f, 0)
        if session_count >= _HOTSPOT_SESSION_THRESHOLD:
            output_system_message(
                f"[omk] {f}이(가) 최근 {session_count}개 세션에서 수정되었습니다. "
                "리팩토링 대상일 수 있습니다."
            )
            state.plane_context.hotspot_alerted_files.append(f)


@contextlib.contextmanager
def _session_write_lock(session_id: str):
    """세션 파일에 대한 배타적 잠금 — async 훅 동시 실행 시 lost-update 방지."""
    lock_path = get_session_lock_path(session_id)
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
            # ST-31: 파일 핫스팟 확인 (hotspot_alerted_files 갱신 포함)
            try:
                _check_file_hotspot(state, file_paths)
            except Exception as e:
                print(
                    f"[omk] 핫스팟 확인 실패 (fail-open): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )
            save_session(state)

        # ST-24: WI에 커밋 댓글 추가 (잠금 밖에서 수행, fail-open)
        if is_git_commit and state.plane_context.work_item_ids:
            try:
                _post_commit_comment(state, commit_hash, commit_command)
                # commit_hashes 갱신을 세션 파일에 반영 (잠금 밖에서 원자적 저장)
                with _session_write_lock(session_id):
                    saved = load_session(session_id)
                    if saved is not None:
                        # 두 리스트를 병합 (중복 제거, 순서 유지) — 덮어쓰기 방지
                        merged = list(
                            dict.fromkeys(
                                saved.stats.commit_hashes + state.stats.commit_hashes
                            )
                        )
                        saved.stats.commit_hashes = merged
                        save_session(saved)
            except Exception as e:
                print(
                    f"[omk] 커밋 추적 실패 (fail-open): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )
        # ST-27: WI 미연결 상태에서 커밋 메시지에 WI 식별자 발견 시 연결 제안
        elif is_git_commit:
            try:
                _suggest_wi_link_from_commit(state, commit_command)
            except Exception as e:
                print(
                    f"[omk] WI 연결 제안 실패 (fail-open): {type(e).__name__}: {e}",
                    file=sys.stderr,
                )

    except Exception as e:
        print(f"[omk] PostToolUse 훅 예외 (fail-open): {type(e).__name__}: {e}", file=sys.stderr)
        exit_fail_open()


if __name__ == "__main__":
    main()
