"""세션 스냅샷 관리: 저장/조회/복원."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from oh_my_kanban.config import CONFIG_DIR
from oh_my_kanban.session.state import SessionState

# 스냅샷 저장 디렉토리
SNAPSHOTS_DIR = CONFIG_DIR / "snapshots"

# 스냅샷 파일 형식 버전
_SNAPSHOT_VERSION = 1

# snapshot_id 안전 문자 패턴 (경로 트래버설 방지)
_SAFE_SNAPSHOT_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")

# snapshot_id 최대 길이
_SNAPSHOT_ID_MAX_LEN = 200

# 스냅샷 메타 요약 표시 최대 길이
_SUMMARY_DISPLAY_MAX = 200


def _sanitize_summary(text: str) -> str:
    """요약 문자열에서 제어 문자를 제거하고 최대 길이로 잘라 반환한다.

    터미널 출력 시 제어 문자로 인한 오동작을 방지한다.
    """
    # 제어 문자 제거 (탭/줄바꿈/CR 제외)
    cleaned = "".join(
        c for c in text if c in ("\t", "\n", "\r") or (ord(c) >= 0x20 and ord(c) != 0x7F)
    )
    # 개행/탭 → 공백 (단일 줄 요약)
    cleaned = cleaned.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    if len(cleaned) > _SUMMARY_DISPLAY_MAX:
        cleaned = cleaned[:_SUMMARY_DISPLAY_MAX] + "..."
    return cleaned


@dataclass
class SnapshotMeta:
    """스냅샷 메타데이터."""

    snapshot_id: str
    session_id: str
    created_at: str
    scope_summary: str
    snapshot_version: int


def _snapshots_dir() -> Path:
    """스냅샷 디렉토리를 반환하고 없으면 생성한다. 0o700 권한."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(SNAPSHOTS_DIR, stat.S_IRWXU)
    except OSError:
        pass  # Windows 등 chmod 미지원 환경에서는 무시
    return SNAPSHOTS_DIR


def _make_snapshot_filename(session_id: str) -> str:
    """스냅샷 파일명을 생성한다. 형식: {session_id[:8]}_{iso_timestamp}.json"""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%S")
    safe_prefix = re.sub(r"[^a-zA-Z0-9]", "_", session_id[:8])
    return f"{safe_prefix}_{ts}.json"


def _validate_snapshot_id(snapshot_id: str) -> None:
    """snapshot_id의 안전성을 검증한다. 경로 트래버설 방지."""
    if not snapshot_id:
        raise ValueError("snapshot_id가 비어있습니다.")
    if len(snapshot_id) > _SNAPSHOT_ID_MAX_LEN:
        raise ValueError(f"snapshot_id가 너무 깁니다 (최대 {_SNAPSHOT_ID_MAX_LEN}자).")
    if not _SAFE_SNAPSHOT_ID_RE.match(snapshot_id):
        raise ValueError(f"snapshot_id에 허용되지 않는 문자가 포함되어 있습니다: {snapshot_id!r}")


def save_snapshot(state: SessionState) -> Path:
    """세션 상태를 스냅샷으로 저장한다. 저장된 파일 경로를 반환한다."""
    snap_dir = _snapshots_dir()
    filename = _make_snapshot_filename(state.session_id)
    snap_path = snap_dir / filename

    # 스냅샷 내용: SessionState + 메타데이터
    data = state.to_dict()
    data["snapshot_version"] = _SNAPSHOT_VERSION
    data["snapshot_created_at"] = datetime.now(timezone.utc).isoformat()

    tmp = snap_path.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 소유자만 읽기/쓰기 (0o600)
        try:
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        tmp.rename(snap_path)
    except OSError as e:
        # tmp 정리
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise OSError(f"스냅샷 저장 실패: {e}") from e

    return snap_path


def list_snapshots() -> list[SnapshotMeta]:
    """저장된 스냅샷 목록을 반환한다. 생성 시간 역순 정렬."""
    snap_dir = _snapshots_dir()
    snapshots: list[SnapshotMeta] = []

    try:
        for p in sorted(snap_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                raw_summary = data.get("scope", {}).get("summary", "")
                meta = SnapshotMeta(
                    snapshot_id=p.stem,
                    session_id=data.get("session_id", ""),
                    created_at=data.get("snapshot_created_at", ""),
                    scope_summary=_sanitize_summary(raw_summary),
                    snapshot_version=data.get("snapshot_version", 0),
                )
                snapshots.append(meta)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                print(f"[omk] 스냅샷 파일 로드 실패 ({p.name}): {e}", file=sys.stderr)
                continue
    except OSError as e:
        print(f"[omk] 스냅샷 디렉토리 접근 실패: {e}", file=sys.stderr)

    return snapshots


def load_snapshot(snapshot_id: str) -> SessionState | None:
    """스냅샷을 로드하여 SessionState로 복원한다. 없으면 None 반환."""
    _validate_snapshot_id(snapshot_id)

    snap_dir = _snapshots_dir()
    snap_path = (snap_dir / f"{snapshot_id}.json").resolve()

    # 경로 트래버설 최종 방어
    if not snap_path.is_relative_to(snap_dir.resolve()):
        raise ValueError(f"snapshot_id가 허용 경로를 벗어남: {snapshot_id!r}")

    if not snap_path.exists():
        return None

    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
        # 스냅샷 메타데이터 필드 제거 후 SessionState 복원
        data.pop("snapshot_version", None)
        data.pop("snapshot_created_at", None)
        return SessionState.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError) as e:
        print(f"[omk] 스냅샷 복원 실패 ({snapshot_id}): {e}", file=sys.stderr)
        return None
