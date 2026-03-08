"""Plane Work Item 컨텍스트 빌더.

compact 복원 시 Claude가 Plane API를 일일이 호출하는 토큰 낭비를 방지한다.
Work Item 제목·설명·최근 댓글을 일괄 조회해 단일 텍스트 덩어리로 반환한다.

사용 시나리오:
    /compact 발생 → SessionStart(compact) 훅 → 이 모듈 호출
    → Plane WI 내용 조회 → 단일 additionalContext 주입
    → Claude가 컨텍스트를 복원하는 데 추가 API 호출 불필요
"""

from __future__ import annotations

import re
import sys
from typing import Any

from oh_my_kanban.hooks.common import validate_plane_url_params
from oh_my_kanban.hooks.http_client import build_plane_headers, plane_http_client, warn_auth_failure

# ── 출력 크기 상수 ────────────────────────────────────────────────────────────
# 전체 WI 컨텍스트 최대 글자 수 (너무 길면 토큰 낭비)
_CONTEXT_MAX_CHARS = 3000
# 한 WI당 설명 최대 글자 수
_DESCRIPTION_MAX_CHARS = 600
# 한 WI당 가져올 최근 댓글 수
_COMMENTS_LIMIT = 5
# 한 댓글 최대 글자 수
_COMMENT_MAX_CHARS = 300

# HTML 태그 제거 정규식
_HTML_TAG_RE = re.compile(r'<[^>]+>')
# 연속 공백/개행 정규화 정규식
_WHITESPACE_RE = re.compile(r'\s+')


def _strip_html(html: str) -> str:
    """HTML 태그를 제거하고 공백을 정규화해 평문을 반환한다."""
    if not html:
        return ""
    text = _HTML_TAG_RE.sub(" ", html)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _truncate(text: str, max_chars: int) -> str:
    """텍스트를 max_chars 길이로 자른다. 자른 경우 '...'을 붙인다."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def _fetch_work_item(
    client: Any,
    base_url: str,
    workspace_slug: str,
    project_id: str,
    wi_id: str,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """단일 Work Item의 상세 정보를 조회한다. 실패 시 None 반환."""
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/issues/{wi_id}/"
    )
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        warn_auth_failure(resp.status_code, context=f"WI 조회 wi_id={wi_id}")
        print(
            f"[omk] Plane WI 조회 실패 (wi_id={wi_id!r}): HTTP {resp.status_code}",
            file=sys.stderr,
        )
        return None
    except Exception as e:
        print(
            f"[omk] Plane WI 조회 예외 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return None


def _fetch_comments(
    client: Any,
    base_url: str,
    workspace_slug: str,
    project_id: str,
    wi_id: str,
    headers: dict[str, str],
) -> list[dict[str, Any]]:
    """Work Item의 댓글 목록을 조회한다. 실패 시 빈 리스트 반환."""
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/issues/{wi_id}/comments/"
    )
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Plane API는 {"results": [...]} 형태로 반환
            if isinstance(data, dict):
                return data.get("results", [])
            if isinstance(data, list):
                return data
        else:
            print(
                f"[omk] Plane 댓글 조회 실패 (wi_id={wi_id!r}): HTTP {resp.status_code}",
                file=sys.stderr,
            )
        return []
    except Exception as e:
        print(
            f"[omk] Plane 댓글 조회 예외 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return []


def _build_wi_context(
    wi_data: dict[str, Any],
    comments: list[dict[str, Any]],
    wi_id: str,
) -> str:
    """Work Item 데이터와 댓글을 사람이 읽기 좋은 텍스트로 변환한다."""
    lines: list[str] = []

    # 제목
    name = wi_data.get("name", "").strip()
    state_name = wi_data.get("state__name") or ""
    if not state_name:
        state_raw = wi_data.get("state")
        if isinstance(state_raw, dict):
            state_name = state_raw.get("name", "")
        elif isinstance(state_raw, str):
            state_name = state_raw
    state_name = state_name or "알 수 없음"
    priority = wi_data.get("priority", "none")

    lines.append(f"### WI: {name}")
    lines.append(f"상태: {state_name} | 우선순위: {priority}")

    # 설명
    description_html = wi_data.get("description_html") or wi_data.get("description", "")
    description = _strip_html(description_html)
    if description:
        lines.append(f"설명: {_truncate(description, _DESCRIPTION_MAX_CHARS)}")

    # 최근 댓글 (최신순 정렬 후 상위 N개)
    if comments:
        # created_at 기준 내림차순 정렬
        sorted_comments = sorted(
            comments,
            key=lambda c: c.get("created_at", ""),
            reverse=True,
        )
        recent = sorted_comments[:_COMMENTS_LIMIT]
        lines.append(f"최근 댓글 ({len(recent)}개):")
        for c in reversed(recent):  # 시간순으로 다시 표시
            actor = c.get("actor_detail", {})
            if isinstance(actor, dict):
                author = actor.get("display_name") or actor.get("email", "")
            else:
                author = str(actor)
            comment_html = c.get("comment_html") or c.get("comment", "")
            comment_text = _strip_html(comment_html)
            if comment_text:
                created = c.get("created_at", "")[:10]  # YYYY-MM-DD 부분만
                lines.append(
                    f"  [{created}] {author}: "
                    f"{_truncate(comment_text, _COMMENT_MAX_CHARS)}"
                )

    return "\n".join(lines)


def build_plane_context(
    work_item_ids: list[str],
    project_id: str,
    base_url: str,
    api_key: str,
    workspace_slug: str,
) -> tuple[str, list[str]]:
    """Work Item 목록을 조회해 단일 컨텍스트 문자열로 반환한다.

    compact 복원 시 session_start.py에서 호출한다.
    Plane API 미설정이거나 조회 실패 시 fail-open으로 처리한다.

    Args:
        work_item_ids: 조회할 Work Item UUID 목록.
        project_id: Plane 프로젝트 UUID.
        base_url: Plane API 기본 URL.
        api_key: Plane API 키.
        workspace_slug: Plane 워크스페이스 슬러그.

    Returns:
        (컨텍스트 문자열, 실패한 WI ID 목록) 튜플.
        조회 실패 또는 미설정 시 ("", []) 또는 ("", 실패한 ID 목록) 반환.
    """
    # 필수 설정 검증
    if not all([work_item_ids, project_id, base_url, api_key, workspace_slug]):
        return "", []

    # URL 경로 파라미터 형식 검증 (경로 트래버설 / 인젝션 방지)
    if not validate_plane_url_params(workspace_slug, project_id):
        print("[omk] 유효하지 않은 workspace_slug 또는 project_id — 컨텍스트 빌드 건너뜀", file=sys.stderr)
        return "", []

    try:
        import httpx
    except ImportError:
        return "", []

    base_url = base_url.rstrip("/")
    headers = build_plane_headers(api_key)

    parts: list[str] = []
    failed_ids: list[str] = []

    try:
        with plane_http_client(api_key) as client:
            for wi_id in work_item_ids[:3]:  # 최대 3개 WI만 조회 (토큰 절약)
                if not validate_plane_url_params(workspace_slug, project_id, wi_id):
                    print(f"[omk] 유효하지 않은 work_item_id 건너뜀: {wi_id!r}", file=sys.stderr)
                    failed_ids.append(wi_id)
                    continue
                wi_data = _fetch_work_item(
                    client, base_url, workspace_slug, project_id, wi_id, headers
                )
                if wi_data is None:
                    failed_ids.append(wi_id)
                    continue

                comments = _fetch_comments(
                    client, base_url, workspace_slug, project_id, wi_id, headers
                )
                wi_context = _build_wi_context(wi_data, comments, wi_id)
                if wi_context:
                    parts.append(wi_context)
    except Exception as e:
        print(
            f"[omk] Plane 컨텍스트 빌드 예외: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return "", list(work_item_ids[:3])

    if not parts:
        return "", failed_ids

    full_context = "\n\n".join(parts)
    return _truncate(full_context, _CONTEXT_MAX_CHARS), failed_ids
