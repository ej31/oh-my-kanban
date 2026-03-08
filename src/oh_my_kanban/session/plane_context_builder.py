"""Plane Work Item 컨텍스트 빌더.

compact 복원 시 Claude가 Plane API를 일일이 호출하는 토큰 낭비를 방지한다.
Work Item 제목·설명·최근 댓글·Sub-task를 ThreadPoolExecutor로 병렬 조회하여
단일 텍스트 덩어리로 반환한다.

사용 시나리오:
    /compact 발생 → SessionStart(compact) 훅 → 이 모듈 호출
    → Plane WI 내용 병렬 조회 → 단일 additionalContext 주입
    → Claude가 컨텍스트를 복원하는 데 추가 API 호출 불필요
"""

from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT

# ── 출력 크기 상수 ────────────────────────────────────────────────────────────
# 전체 WI 컨텍스트 최대 글자 수 (너무 길면 토큰 낭비)
_CONTEXT_MAX_CHARS = 4000
# 한 WI당 설명 최대 글자 수
_DESCRIPTION_MAX_CHARS = 800
# 한 WI당 가져올 최근 댓글 수 (Phase 1b: 5 → 10으로 강화)
_COMMENTS_LIMIT = 10
# 한 댓글 최대 글자 수
_COMMENT_MAX_CHARS = 300
# Sub-task 표시 최대 수
_SUBTASKS_DISPLAY_MAX = 5
# 병렬 WI 조회 최대 워커 수
_MAX_WORKERS = 4

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
        if resp.status_code in (404, 410):
            # 외부에서 삭제된 WI — 호출자가 handle_orphan_wi를 호출할 수 있도록 특별 표시
            return {"__deleted__": True, "__wi_id__": wi_id, "__status__": resp.status_code}
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


def _fetch_sub_tasks(
    client: Any,
    base_url: str,
    workspace_slug: str,
    project_id: str,
    wi_id: str,
    headers: dict[str, str],
) -> list[dict[str, Any]]:
    """Work Item의 하위 태스크(Sub-task) 목록을 조회한다. 실패 시 빈 리스트 반환."""
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/issues/"
    )
    try:
        resp = client.get(url, headers=headers, params={"parent": wi_id})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                return data.get("results", [])
            if isinstance(data, list):
                return data
        else:
            print(
                f"[omk] Plane Sub-task 조회 실패 (wi_id={wi_id!r}): HTTP {resp.status_code}",
                file=sys.stderr,
            )
        return []
    except Exception as e:
        print(
            f"[omk] Plane Sub-task 조회 예외 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return []


def _build_wi_context(
    wi_data: dict[str, Any],
    comments: list[dict[str, Any]],
    _wi_id: str,
    sub_tasks: list[dict[str, Any]] | None = None,
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

    # Sub-task 목록 (최대 _SUBTASKS_DISPLAY_MAX개)
    if sub_tasks:
        lines.append(f"Sub-tasks ({len(sub_tasks)}개):")
        for st in sub_tasks[:_SUBTASKS_DISPLAY_MAX]:
            st_name = st.get("name", "").strip()
            st_state = st.get("state__name") or ""
            if not st_state:
                st_state_raw = st.get("state")
                if isinstance(st_state_raw, dict):
                    st_state = st_state_raw.get("name", "")
                elif isinstance(st_state_raw, str):
                    st_state = st_state_raw
            normalized_state = st_state.strip().lower()
            completed = "✓" if normalized_state in {"complete", "completed", "done"} else "○"
            lines.append(f"  {completed} {st_name}")
        if len(sub_tasks) > _SUBTASKS_DISPLAY_MAX:
            lines.append(f"  ...외 {len(sub_tasks) - _SUBTASKS_DISPLAY_MAX}개")

    return "\n".join(lines)


def build_plane_context(
    work_item_ids: list[str],
    project_id: str,
    base_url: str,
    api_key: str,
    workspace_slug: str,
) -> str:
    """Work Item 목록을 조회해 단일 컨텍스트 문자열로 반환한다.

    compact 복원 시 session_start.py에서 호출한다.
    Plane API 미설정이거나 조회 실패 시 빈 문자열 반환 (fail-open).

    Args:
        work_item_ids: 조회할 Work Item UUID 목록.
        project_id: Plane 프로젝트 UUID.
        base_url: Plane API 기본 URL.
        api_key: Plane API 키.
        workspace_slug: Plane 워크스페이스 슬러그.

    Returns:
        Work Item 내용을 포함한 컨텍스트 문자열. 실패 시 빈 문자열.
    """
    # 필수 설정 검증
    if not all([work_item_ids, project_id, base_url, api_key, workspace_slug]):
        return ""

    try:
        import httpx
    except ImportError:
        return ""

    base_url = base_url.rstrip("/")
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    parts: list[str] = []

    def _fetch_single_wi(wi_id: str) -> tuple[str, dict | None, list, list]:
        """단일 WI의 상세정보, 댓글, Sub-task를 조회한다. 순서 보장을 위해 wi_id를 함께 반환."""
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            wi_data = _fetch_work_item(client, base_url, workspace_slug, project_id, wi_id, headers)
            if wi_data is None or wi_data.get("__deleted__"):
                return wi_id, wi_data, [], []
            comments = _fetch_comments(client, base_url, workspace_slug, project_id, wi_id, headers)
            sub_tasks = _fetch_sub_tasks(
                client, base_url, workspace_slug, project_id, wi_id, headers
            )
            return wi_id, wi_data, comments, sub_tasks

    try:
        target_ids = work_item_ids[:3]  # 최대 3개 WI만 조회 (토큰 절약)
        deleted_wi_ids: list[str] = []

        # ThreadPoolExecutor로 병렬 조회 (순서 보장: work_item_ids 원래 순서 유지)
        results: dict[str, tuple] = {}
        with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(target_ids))) as executor:
            future_to_id = {executor.submit(_fetch_single_wi, wi_id): wi_id for wi_id in target_ids}
            for future in as_completed(future_to_id):
                wi_id = future_to_id[future]
                try:
                    results[wi_id] = future.result()
                except Exception as e:
                    print(
                        f"[omk] Plane WI 병렬 조회 예외 (wi_id={wi_id!r}): {type(e).__name__}: {e}",
                        file=sys.stderr,
                    )
                    results[wi_id] = (wi_id, None, [], [])

        # 원래 순서대로 컨텍스트 구성
        for wi_id in target_ids:
            if wi_id not in results:
                continue
            _, wi_data, comments, sub_tasks = results[wi_id]
            if wi_data is None:
                continue
            if wi_data.get("__deleted__"):
                deleted_wi_ids.append(wi_id)
                print(
                    f"[omk] Plane WI 삭제 감지 (wi_id={wi_id!r}): HTTP {wi_data.get('__status__')}",
                    file=sys.stderr,
                )
                continue
            wi_context = _build_wi_context(wi_data, comments, wi_id, sub_tasks)
            if wi_context:
                parts.append(wi_context)

    except Exception as e:
        print(
            f"[omk] Plane 컨텍스트 빌드 예외: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return ""

    # 삭제된 WI가 있으면 컨텍스트에 경고 추가
    if deleted_wi_ids:
        deleted_ids_str = ', '.join(d[:8] + '...' for d in deleted_wi_ids)
        deleted_note = f"[omk 경고] 다음 WI가 외부에서 삭제됐습니다: {deleted_ids_str}"
        parts.append(deleted_note)

    if not parts:
        return ""

    full_context = "\n\n".join(parts)

    return _truncate(full_context, _CONTEXT_MAX_CHARS)
