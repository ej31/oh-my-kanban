"""Plane API HTTP 클라이언트 공통 유틸리티: 인증 헤더 팩토리 + 응답 경고 + 통합 래퍼."""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from typing import Any

import httpx

from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT

# 재시도 대상 상태 코드
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES = 2
_BACKOFF_BASE = 1.0  # 지수 백오프 기본 대기 시간 (초)


def build_plane_headers(api_key: str, content_type: str = "application/json") -> dict[str, str]:
    """Plane API 인증 헤더를 생성한다.

    Args:
        api_key: Plane API 키.
        content_type: Content-Type 헤더 값. 빈 문자열이면 생략.

    Returns:
        인증 및 Content-Type 헤더 딕셔너리.
    """
    headers: dict[str, str] = {"X-API-Key": api_key}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def warn_auth_failure(status_code: int, context: str = "") -> None:
    """401/403 응답 시 stderr에 인증 실패 경고를 출력한다.

    Args:
        status_code: HTTP 응답 상태 코드.
        context: 호출 맥락 (예: "댓글 추가", "WI 조회"). 없으면 생략.
    """
    if status_code == 401:
        msg = "[omk] Plane API 인증 실패 (401). API 키가 만료되었거나 잘못되었습니다."
    elif status_code == 403:
        msg = "[omk] Plane API 권한 부족 (403). 워크스페이스/프로젝트 접근 권한을 확인하세요."
    else:
        return
    if context:
        msg += f" ({context})"
    print(msg, file=sys.stderr)


@contextmanager
def plane_http_client(
    api_key: str,
    timeout: httpx.Timeout | None = None,
):
    """Plane API 호출용 통합 httpx.Client 컨텍스트 매니저.

    기능:
    - 인증 헤더 자동 설정
    - 타임아웃 기본값 적용
    - follow_redirects=False (보안)

    Args:
        api_key: Plane API 키.
        timeout: httpx.Timeout. None이면 PLANE_API_TIMEOUT 사용.
    """
    headers = build_plane_headers(api_key)
    with httpx.Client(
        timeout=timeout or PLANE_API_TIMEOUT,
        follow_redirects=False,
    ) as client:
        # 기본 헤더 설정
        client.headers.update(headers)
        yield client


def plane_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_retries: int = _MAX_RETRIES,
    context: str = "",
    **kwargs: Any,
) -> httpx.Response:
    """재시도 + 에러 분류가 포함된 Plane API 요청 래퍼.

    Args:
        client: httpx.Client 인스턴스.
        method: HTTP 메서드 (GET, POST, DELETE 등).
        url: 요청 URL.
        max_retries: 최대 재시도 횟수 (기본 2).
        context: 에러 로그에 포함할 맥락 문자열.
        **kwargs: httpx.Client.request()에 전달할 추가 인자.

    Returns:
        httpx.Response 객체.

    Raises:
        httpx.TimeoutException: 재시도 후에도 타임아웃 시.
        httpx.NetworkError: 재시도 후에도 네트워크 에러 시.
    """
    resp: httpx.Response | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.request(method, url, **kwargs)
            # 재시도 대상 상태 코드
            if resp.status_code in _RETRYABLE_STATUS and attempt < max_retries:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = min(float(retry_after), 10.0)
                    except ValueError:
                        wait = _BACKOFF_BASE * (2 ** attempt)
                else:
                    wait = _BACKOFF_BASE * (2 ** attempt)
                time.sleep(wait)
                continue
            # 401/403 경고
            warn_auth_failure(resp.status_code, context=context)
            return resp
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt < max_retries:
                time.sleep(_BACKOFF_BASE * (2 ** attempt))
                continue
            raise
    # 모든 재시도 후에도 재시도 대상 상태 코드면 마지막 응답 반환
    assert resp is not None
    return resp
