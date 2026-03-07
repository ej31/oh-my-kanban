"""훅 공통 유틸리티: fail-open 래퍼, stdin 파싱, 상태 주입."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

import httpx

from oh_my_kanban.session.manager import load_session
from oh_my_kanban.session.state import SessionState

# Plane API 호출 타임아웃 (connect/read 분리)
PLANE_API_TIMEOUT = httpx.Timeout(10.0, connect=3.0, read=10.0)

# fcntl은 Unix 전용 — Windows에서는 no-op fallback
try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False


@contextlib.contextmanager
def session_write_lock(lock_path: Path):
    """세션 파일에 대한 배타적 잠금 — async 훅 동시 실행 시 lost-update 방지.

    Windows 등 fcntl 미지원 환경에서는 no-op으로 동작한다.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_FCNTL:
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)
    else:
        # Windows: 잠금 없이 진행 (best-effort)
        yield


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


def record_health_warning(warning: dict[str, Any]) -> None:
    """훅 실패 시 health_warnings.json에 경고를 기록한다.

    기록 실패해도 훅을 차단하지 않는다 (fail-open).
    """
    from oh_my_kanban.config import CONFIG_DIR

    warnings_file = CONFIG_DIR / "health_warnings.json"
    try:
        warnings_file.parent.mkdir(parents=True, exist_ok=True)
        existing: list[dict[str, Any]] = []
        if warnings_file.exists():
            try:
                existing = json.loads(warnings_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, OSError):
                existing = []
        # 최대 50개 유지 (오래된 것부터 제거)
        existing.append(warning)
        if len(existing) > 50:
            existing = existing[-50:]
        warnings_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        # fail-open: 기록 실패 시 훅을 차단하지 않는다
        print(f"[omk] health_warnings 기록 실패: {type(e).__name__}", file=sys.stderr)


def exit_fail_open() -> None:
    """훅 실패 종료 — exit code 0으로 Claude Code를 차단하지 않는다."""
    sys.exit(0)
