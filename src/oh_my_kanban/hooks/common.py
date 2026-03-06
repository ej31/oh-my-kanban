"""훅 공통 유틸리티: fail-open 래퍼, stdin 파싱, 상태 주입."""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

from oh_my_kanban.session.manager import load_session
from oh_my_kanban.session.state import SessionState

# Plane API 호출 타임아웃 (초 단위)
PLANE_API_TIMEOUT = 10.0


def read_hook_input() -> dict[str, Any]:
    """stdin에서 훅 입력 JSON을 파싱한다. 실패 시 빈 dict 반환 (fail-open)."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError, ValueError):
        return {}


def get_session_id(hook_input: dict[str, Any]) -> str:
    """훅 입력 dict에서 session_id를 추출한다."""
    return str(hook_input.get("session_id", ""))


def get_session_or_exit(session_id: str) -> Optional[SessionState]:
    """세션을 로드한다. 없으면 None 반환 (호출자가 exit_fail_open 처리)."""
    if not session_id:
        return None
    return load_session(session_id)


def is_opted_out(session_id: str) -> bool:
    """세션의 opted_out 상태를 확인한다. 파일 없으면 False (fail-open)."""
    if not session_id:
        return False
    state = load_session(session_id)
    return state.opted_out if state is not None else False


def output_context(hook_event_name: str, additional_context: str) -> None:
    """Claude Code에 additionalContext를 조용히 주입한다 (사용자에게 미표시)."""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            "additionalContext": additional_context,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))


def output_system_message(
    message: str,
    hook_event_name: str = "",
    additional_context: str = "",
) -> None:
    """사용자에게 보이는 systemMessage를 출력한다. additionalContext도 함께 전달 가능."""
    payload: dict[str, Any] = {"systemMessage": message}
    if hook_event_name and additional_context:
        payload["hookSpecificOutput"] = {
            "hookEventName": hook_event_name,
            "additionalContext": additional_context,
        }
    print(json.dumps(payload, ensure_ascii=False))


def exit_fail_open() -> None:
    """훅 실패 종료 — exit code 0으로 Claude Code를 차단하지 않는다."""
    sys.exit(0)
