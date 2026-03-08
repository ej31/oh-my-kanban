"""훅 공통 유틸리티: fail-open 래퍼, stdin 파싱, 상태 주입."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from oh_my_kanban.session.manager import load_session
from oh_my_kanban.session.state import SessionState

# Plane API 호출 타임아웃 (초 단위)
PLANE_API_TIMEOUT = 10.0

# HUD에 표시할 작업 이름 최대 길이
HUD_TASK_NAME_MAX = 15


@dataclass(frozen=True)
class HookDiagnostic:
    """훅 실행 중 발생한 오류 진단 정보."""

    # config_missing | auth_failure | network_error | rate_limit | server_error | wi_deleted
    category: str
    message: str
    wi_url: str = ""
    recovery_hint: str = ""


@dataclass(frozen=True)
class SuccessNudge:
    """WI 연결 성공 시 사용자에게 보여줄 정보."""

    wi_identifier: str  # "OMK-5"
    wi_name: str
    wi_url: str = ""


def notify_and_exit(diagnostic: HookDiagnostic, hook_name: str = "") -> None:
    """오류 진단을 stderr에 출력하고 fail-open으로 종료한다."""
    prefix = f"[omk]/{hook_name}" if hook_name else "[omk]"
    print(f"{prefix} {diagnostic.category}: {diagnostic.message}", file=sys.stderr)
    if diagnostic.recovery_hint:
        print(f"  → {diagnostic.recovery_hint}", file=sys.stderr)
    if diagnostic.wi_url:
        print(f"  → WI: {diagnostic.wi_url}", file=sys.stderr)
    sys.exit(0)


def notify_success(nudge: SuccessNudge) -> None:
    """WI 연결 성공 메시지를 systemMessage로 출력한다."""
    truncated_name = nudge.wi_name[:HUD_TASK_NAME_MAX]
    message = f"omk: {nudge.wi_identifier} [{truncated_name}] 연결됨"
    if nudge.wi_url:
        message += f" — {nudge.wi_url}"
    output_system_message(message)


def classify_api_error(
    exc: Exception | None, status_code: int | None
) -> HookDiagnostic:
    """HTTP 상태 코드 또는 예외로부터 HookDiagnostic을 생성한다."""
    # 404 / 410: WI가 외부에서 삭제된 경우
    if status_code in (404, 410):
        return HookDiagnostic(
            category="wi_deleted",
            message="Work Item이 외부에서 삭제됨",
            recovery_hint="omk focus로 다른 WI를 선택하세요",
        )
    # 401 / 403: 인증 실패
    if status_code in (401, 403):
        return HookDiagnostic(
            category="auth_failure",
            message="Plane API 인증 실패",
            recovery_hint="omk setup으로 API 키를 재설정하세요",
        )
    # 429: 요청 한도 초과
    if status_code == 429:
        return HookDiagnostic(
            category="rate_limit",
            message="Plane API 요청 한도 초과",
            recovery_hint="잠시 후 자동으로 재시도됩니다",
        )
    # 5xx: 서버 오류
    if status_code is not None and status_code >= 500:
        return HookDiagnostic(
            category="server_error",
            message=f"Plane 서버 오류 (HTTP {status_code})",
            recovery_hint="Plane 서비스 상태를 확인하세요",
        )
    # 타임아웃 예외
    if exc is not None and (
        "Timeout" in type(exc).__name__ or "timeout" in str(exc).lower()
    ):
        return HookDiagnostic(
            category="network_error",
            message="Plane API 타임아웃",
            recovery_hint="네트워크 연결을 확인하세요",
        )
    # 네트워크/연결 예외
    if exc is not None and (
        "Network" in type(exc).__name__ or "Connect" in type(exc).__name__
    ):
        return HookDiagnostic(
            category="network_error",
            message="Plane API 연결 실패",
            recovery_hint="네트워크 연결을 확인하세요",
        )
    # 그 외 기본 오류 — 예외 타입만 노출 (exc 메시지에 URL/헤더 등 민감 정보가 포함될 수 있음)
    error_type = type(exc).__name__ if exc else "알 수 없음"
    if exc:
        print(f"[omk] API 오류 타입 (debug): {type(exc).__name__}", file=sys.stderr)
    return HookDiagnostic(
        category="server_error",
        message=f"Plane API 오류: {error_type}",
        recovery_hint="잠시 후 다시 시도하세요",
    )


def build_wi_url(
    base_url: str, workspace_slug: str, project_id: str, sequence_id: int
) -> str:
    """Plane WI의 웹 URL을 생성한다."""
    return f"{base_url.rstrip('/')}/{workspace_slug}/projects/{project_id}/issues/{sequence_id}/"


def build_wi_identifier(sequence_id: int) -> str:
    """WI 식별자를 생성한다. 예: OMK-5"""
    return f"OMK-{sequence_id}"


# 민감 정보 치환 패턴
_HEX_PATTERN = re.compile(r"[0-9a-fA-F]{32,}")
_SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|secret|token|api_key|apikey)\s*[=:]\s*\S+",
)
# AWS Access Key 패턴 (AKIA... 20자)
_AWS_KEY_PATTERN = re.compile(r'AKIA[0-9A-Z]{16}')
# GitHub PAT/OAuth/앱 토큰 패턴
_GH_TOKEN_PATTERN = re.compile(r'gh[pous]_[A-Za-z0-9_]{36,}')
# Bearer 토큰 / JWT 패턴
_BEARER_PATTERN = re.compile(r'Bearer\s+[A-Za-z0-9_.\-/+=]{20,}')
# 연결 문자열 패턴 (mongodb+srv://user:pass@host 등)
_CONN_STRING_PATTERN = re.compile(r'[a-zA-Z][a-zA-Z0-9+\-.]*://[^:@\s]+:[^@\s]+@[^\s]+')


def sanitize_comment(text: str) -> str:
    """댓글 텍스트에서 민감 정보를 [REDACTED]로 치환한다."""
    # 민감 키워드 뒤에 오는 값 제거 — 먼저 처리해 이중 치환 방지
    result = _SECRET_PATTERN.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    # 연결 문자열 (user:pass@host 형태)
    result = _CONN_STRING_PATTERN.sub("[REDACTED_URL]", result)
    # AWS Access Key
    result = _AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", result)
    # GitHub 토큰
    result = _GH_TOKEN_PATTERN.sub("[REDACTED_GH_TOKEN]", result)
    # Bearer 토큰
    result = _BEARER_PATTERN.sub("Bearer [REDACTED]", result)
    # 32자 이상의 연속 16진수 문자열 제거
    result = _HEX_PATTERN.sub("[REDACTED]", result)
    return result


def update_hud(wi_identifier: str, wi_name: str, wi_status: str) -> None:
    """터미널 타이틀과 tmux 윈도우 이름을 현재 WI 정보로 업데이트한다."""
    safe_name = (
        wi_name.replace("\x1b", "")
        .replace("\x07", "")
        .replace("\n", " ")
        .replace("\r", " ")
    )
    safe_identifier = (
        wi_identifier.replace("\x1b", "")
        .replace("\x07", "")
        .replace("\n", " ")
        .replace("\r", " ")
    )
    safe_status = (
        wi_status.replace("\x1b", "")
        .replace("\x07", "")
        .replace("\n", " ")
        .replace("\r", " ")
    )
    truncated = safe_name[:HUD_TASK_NAME_MAX]
    # ANSI 이스케이프로 터미널 타이틀 업데이트
    sys.stderr.write(f"\033]0;omk:{safe_identifier} {truncated} [{safe_status}]\007")
    sys.stderr.flush()
    # TMUX 환경이면 윈도우 이름도 변경
    if os.environ.get("TMUX"):
        try:
            subprocess.run(
                ["tmux", "rename-window", f"omk:{safe_identifier}"],
                check=False,
                capture_output=True,
            )
        except OSError:
            pass  # tmux 실행 실패 시 무시


def reset_hud() -> None:
    """터미널 타이틀과 tmux 윈도우 이름을 초기화한다."""
    sys.stderr.write("\033]0;\007")
    sys.stderr.flush()
    if os.environ.get("TMUX"):
        try:
            subprocess.run(
                ["tmux", "rename-window", ""],
                check=False,
                capture_output=True,
            )
        except OSError:
            pass  # tmux 실행 실패 시 무시


def create_plane_http_client(_cfg: Any) -> Any | None:  # noqa: ANN401
    """Plane API용 httpx 클라이언트를 생성한다. httpx 미설치 시 None 반환."""
    try:
        import httpx  # noqa: PLC0415

        return httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False)
    except ImportError:
        return None


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


def get_session_or_exit(session_id: str) -> SessionState | None:
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


def handle_orphan_wi(
    state: SessionState,
    wi_id: str,
    hook_event_name: str = "SessionStart",
) -> None:
    """외부에서 삭제된 WI를 stale_work_item_ids에 기록하고 상태를 정리하며 사용자에게 알린다.

    Args:
        state: 현재 세션 상태. stale_work_item_ids에 wi_id가 추가되고
               work_item_ids에서 제거된다.
        wi_id: 삭제된 Work Item UUID.
        hook_event_name: 훅 이벤트 이름 (알림 채널용).
    """
    # 이미 stale 목록에 있으면 중복 알림 방지
    if wi_id in state.plane_context.stale_work_item_ids:
        return

    # 새 리스트 생성 — 기존 리스트 직접 변경 없음
    state.plane_context.stale_work_item_ids = [
        *state.plane_context.stale_work_item_ids, wi_id
    ]

    # work_item_ids에서 삭제된 WI 제거
    state.plane_context.work_item_ids = [
        w for w in state.plane_context.work_item_ids if w != wi_id
    ]

    remaining = list(state.plane_context.work_item_ids)

    # focused_work_item_id가 삭제된 WI이면 남은 WI로 이동
    if state.plane_context.focused_work_item_id == wi_id:
        state.plane_context.focused_work_item_id = remaining[0] if remaining else None

    # main_task_id가 삭제된 WI이면 초기화
    if state.plane_context.main_task_id == wi_id:
        state.plane_context.main_task_id = None

    if not remaining:
        # 모든 WI가 삭제된 경우
        message = (
            "연결된 모든 Work Item이 삭제됐습니다. "
            "omk focus 또는 omk create-task로 새 Work Item을 연결하세요."
        )
        additional_ctx = (
            "omk: 연결된 Plane Work Item이 모두 외부에서 삭제됨. "
            "새 WI를 연결하거나 omk-off로 추적을 중단하세요."
        )
    else:
        # 일부만 삭제된 경우
        message = (
            f"Work Item({wi_id[:8]}...)이 외부에서 삭제됐습니다. "
            f"나머지 {len(remaining)}개 WI로 계속 진행합니다."
        )
        additional_ctx = (
            f"omk: WI {wi_id[:8]}... 삭제 감지. 나머지 WI: {', '.join(remaining[:3])}."
        )

    output_system_message(message, hook_event_name, additional_ctx)
    print(
        f"[omk] Orphan WI 감지: {wi_id[:8]}..."
        f" | stale 목록: {len(state.plane_context.stale_work_item_ids)}개",
        file=sys.stderr,
    )
