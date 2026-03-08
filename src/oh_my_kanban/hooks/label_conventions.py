"""omk Label 컨벤션 초기화.

Plane 프로젝트에 omk 표준 라벨을 생성한다.
이미 존재하는 라벨은 재생성하지 않는다 (idempotent).
API 실패는 fail-open으로 처리한다 — 라벨 없어도 기본 기능은 동작한다.

표준 라벨:
    omk:session     — omk가 관리하는 WI 마커 (#6366F1 indigo)
    omk:type:main   — MainTask 구분 (#10B981 emerald)
    omk:type:sub    — SubTask 구분 (#6EE7B7 light green)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from oh_my_kanban.hooks.common import PLANE_API_TIMEOUT, validate_plane_url_params

# ── 표준 라벨 정의 ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OmkLabel:
    """omk 표준 라벨 정의."""
    name: str
    color: str
    description: str


# omk 표준 라벨 목록
OMK_LABELS: tuple[OmkLabel, ...] = (
    OmkLabel(
        name="omk:session",
        color="#6366F1",
        description="oh-my-kanban이 관리하는 Work Item 마커",
    ),
    OmkLabel(
        name="omk:type:main",
        color="#10B981",
        description="omk MainTask 구분 라벨 (Mode A: MainTask-Subtask)",
    ),
    OmkLabel(
        name="omk:type:sub",
        color="#6EE7B7",
        description="omk SubTask 구분 라벨",
    ),
)


def _fetch_existing_labels(
    client: Any,
    base_url: str,
    workspace_slug: str,
    project_id: str,
    headers: dict[str, str],
) -> set[str]:
    """프로젝트의 기존 라벨 이름 집합을 반환한다. 실패 시 빈 집합 반환."""
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/labels/"
    )
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("results", data) if isinstance(data, dict) else data
            return {item.get("name", "") for item in items if isinstance(item, dict)}
        print(
            f"[omk] 라벨 목록 조회 실패: HTTP {resp.status_code}",
            file=sys.stderr,
        )
        return set()
    except Exception as e:
        print(
            f"[omk] 라벨 목록 조회 예외: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return set()


def _create_label(
    client: Any,
    base_url: str,
    workspace_slug: str,
    project_id: str,
    headers: dict[str, str],
    label: OmkLabel,
) -> bool:
    """단일 라벨을 생성한다. 성공 여부를 반환한다."""
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/labels/"
    )
    payload = {
        "name": label.name,
        "color": label.color,
        "description": label.description,
    }
    try:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            return True
        print(
            f"[omk] 라벨 생성 실패 (name={label.name!r}): HTTP {resp.status_code}",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(
            f"[omk] 라벨 생성 예외 (name={label.name!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return False


def ensure_omk_labels(project_id: str, cfg: Any) -> None:
    """omk 표준 라벨이 프로젝트에 존재하는지 확인하고 없으면 생성한다.

    idempotent: 이미 존재하는 라벨은 재생성하지 않는다.
    fail-open: API 실패 시 예외를 전파하지 않고 경고만 출력한다.

    Args:
        project_id: Plane 프로젝트 UUID.
        cfg: load_config()로 로드한 Config 객체. api_key, workspace_slug, base_url 사용.
    """
    if not cfg.api_key or not cfg.workspace_slug or not project_id:
        return

    # URL 경로 파라미터 형식 검증 (경로 트래버설 / 인젝션 방지)
    workspace_slug = cfg.workspace_slug
    if not validate_plane_url_params(workspace_slug, project_id):
        print("[omk] 유효하지 않은 workspace_slug 또는 project_id — 라벨 초기화 건너뜀", file=sys.stderr)
        return

    try:
        import httpx
    except ImportError:
        return

    base_url = cfg.base_url.rstrip("/")
    headers = {
        "X-API-Key": cfg.api_key,
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            existing_names = _fetch_existing_labels(
                client, base_url, workspace_slug, project_id, headers
            )

            created_count = 0
            for label in OMK_LABELS:
                if label.name in existing_names:
                    # 이미 존재 — 재생성하지 않음 (idempotent)
                    continue
                success = _create_label(
                    client, base_url, workspace_slug, project_id, headers, label
                )
                if success:
                    created_count += 1
                    print(f"[omk] 라벨 생성: {label.name} ({label.color})")

            if created_count > 0:
                print(f"[omk] omk 표준 라벨 {created_count}개 생성 완료")
            else:
                print("[omk] omk 표준 라벨 이미 설정됨")

    except Exception as e:
        # fail-open: 라벨 초기화 실패가 훅 설치를 막지 않도록
        print(
            f"[omk] 라벨 초기화 중 예외 (무시): {type(e).__name__}: {e}",
            file=sys.stderr,
        )


def get_label_id_by_name(
    label_name: str,
    project_id: str,
    cfg: Any,
) -> str | None:
    """라벨 이름으로 Plane 라벨 UUID를 조회한다. 실패 시 None 반환."""
    if not cfg.api_key or not cfg.workspace_slug or not project_id:
        return None

    # URL 경로 파라미터 형식 검증 (경로 트래버설 / 인젝션 방지)
    workspace_slug = cfg.workspace_slug
    if not validate_plane_url_params(workspace_slug, project_id):
        return None

    try:
        import httpx
    except ImportError:
        return None

    base_url = cfg.base_url.rstrip("/")
    headers = {"X-API-Key": cfg.api_key}
    url = (
        f"{base_url}/api/v1/workspaces/{workspace_slug}"
        f"/projects/{project_id}/labels/"
    )
    try:
        with httpx.Client(timeout=PLANE_API_TIMEOUT, follow_redirects=False) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("results", data) if isinstance(data, dict) else data
                for item in items:
                    if isinstance(item, dict) and item.get("name") == label_name:
                        return item.get("id")
    except Exception as e:
        print(
            f"[omk] 라벨 ID 조회 예외 (name={label_name!r}): {type(e).__name__}: {e}",
            file=sys.stderr,
        )
    return None
