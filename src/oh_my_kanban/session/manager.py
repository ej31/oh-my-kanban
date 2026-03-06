"""세션 CRUD — 로컬 JSON 전용. 네트워크 호출 없음."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from oh_my_kanban.config import CONFIG_DIR
from oh_my_kanban.session.state import SessionState

# 세션 파일 저장 디렉토리
SESSIONS_DIR = CONFIG_DIR / "sessions"

# session_id에 허용되는 문자 (경로 트래버설 방지용 안전 변환만 수행)
_UNSAFE_CHARS = str.maketrans({"/": "_", "\\": "_", ".": "_"})

# session_id 최대 허용 길이 — 파일명 초과로 인한 OSError 방지
_SESSION_ID_MAX_LEN = 200


def _sessions_dir() -> Path:
    """세션 디렉토리를 반환하고 없으면 생성한다."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def _session_path(session_id: str) -> Path:
    """session_id를 안전한 파일명으로 변환해 경로를 반환한다.

    보안 방어:
    1. 위험 문자(/, \\, .) → _ 변환
    2. null 바이트 제거 (OS 레벨 경로 해석 우회 방지)
    3. 길이 제한 (_SESSION_ID_MAX_LEN)
    4. resolve() 후 SESSIONS_DIR 하위 경로인지 검증 (경로 트래버설 최종 방어)
    """
    safe_id = session_id.translate(_UNSAFE_CHARS)
    # null 바이트 제거 — C 라이브러리가 null에서 문자열을 자르는 것을 방지
    safe_id = safe_id.replace("\x00", "")
    # 파일명이 비정상적으로 길어지지 않도록 제한
    safe_id = safe_id[:_SESSION_ID_MAX_LEN]
    if not safe_id:
        safe_id = "_empty_"
    sessions_root = _sessions_dir().resolve()
    target = (sessions_root / f"{safe_id}.json").resolve()
    # 경로 트래버설 최종 방어: 결과 경로가 세션 디렉토리 하위인지 확인
    if not target.is_relative_to(sessions_root):
        raise ValueError(f"세션 ID가 허용 경로를 벗어남: {session_id!r}")
    return target


def load_session(session_id: str) -> Optional[SessionState]:
    """세션 파일을 로드한다. 없거나 파싱 실패 시 None 반환."""
    if not session_id:
        return None
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_session(state: SessionState) -> None:
    """세션 상태를 원자적으로 저장한다 (tmp → rename).

    저장 실패 시 stderr에 경고를 기록하고 무시 — 훅이 Claude Code를 차단하면 안 된다.
    """
    path = _session_path(state.session_id)
    state.touch()
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(state.to_json(), encoding="utf-8")
        tmp.rename(path)
    except OSError as e:
        # 원자적 쓰기 실패 → 직접 쓰기 시도
        try:
            path.write_text(state.to_json(), encoding="utf-8")
        except OSError as e2:
            print(
                f"[omk] 세션 저장 실패 (session_id={state.session_id!r}): {e2}",
                file=sys.stderr,
            )
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def create_session(session_id: str) -> SessionState:
    """새 세션을 생성하고 파일에 저장한다."""
    state = SessionState(session_id=session_id)
    save_session(state)
    return state


def list_sessions() -> list[SessionState]:
    """저장된 모든 세션을 로드해 반환한다."""
    sessions: list[SessionState] = []
    try:
        for p in _sessions_dir().glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                sessions.append(SessionState.from_dict(data))
            except (json.JSONDecodeError, KeyError, OSError) as e:
                print(f"[omk] 세션 파일 로드 실패 ({p.name}): {e}", file=sys.stderr)
                continue
    except OSError as e:
        print(f"[omk] 세션 디렉토리 접근 실패: {e}", file=sys.stderr)
    return sessions


def delete_session_file(session_id: str) -> bool:
    """세션 파일을 삭제한다. 성공 여부를 반환한다."""
    try:
        _session_path(session_id).unlink(missing_ok=True)
        return True
    except OSError:
        return False
