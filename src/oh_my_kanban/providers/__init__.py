"""Provider 팩토리: 설정과 세션 상태에서 적절한 ProviderClient를 생성한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oh_my_kanban.config import detect_project_toml

if TYPE_CHECKING:
    from oh_my_kanban.config import Config
    from oh_my_kanban.provider import ProviderClient


def get_provider_name(cfg: "Config") -> str:
    """활성 provider 이름을 결정한다.

    우선순위:
    1. .omk/project.toml의 provider 필드
    2. cfg.linear_api_key가 설정된 경우 "linear"
    3. 기본값 "plane"
    """
    _, provider = detect_project_toml()
    if provider:
        return provider
    if cfg.linear_api_key:
        return "linear"
    return "plane"


def get_provider_client(provider_name: str, cfg: "Config") -> "ProviderClient":
    """provider_name에 해당하는 ProviderClient 인스턴스를 반환한다.

    Args:
        provider_name: "plane" 또는 "linear".
        cfg: 로드된 설정 객체.

    Returns:
        ProviderClient 구현체.

    Raises:
        ValueError: 알 수 없는 provider_name인 경우.
        RuntimeError: 필수 설정(api_key 등)이 누락된 경우.
    """
    if provider_name == "linear":
        return _make_linear_client(cfg)
    if provider_name == "plane":
        return _make_plane_client(cfg)
    raise ValueError(
        f"알 수 없는 provider: {provider_name!r}. 허용값: 'plane', 'linear'"
    )


def _make_plane_client(cfg: "Config") -> "ProviderClient":
    """Plane ProviderClient를 생성한다."""
    from oh_my_kanban.providers.plane import PlaneProviderClient
    return PlaneProviderClient(cfg)


def _make_linear_client(cfg: "Config") -> "ProviderClient":
    """Linear ProviderClient를 생성한다."""
    from oh_my_kanban.providers.linear import LinearProviderClient
    return LinearProviderClient(cfg)
