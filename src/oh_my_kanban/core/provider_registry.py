"""Single source of truth for registered providers."""

from __future__ import annotations

from dataclasses import dataclass

import click

from oh_my_kanban.providers.linear.group import linear
from oh_my_kanban.providers.plane.group import plane


@dataclass(frozen=True)
class ProviderSpec:
    """Metadata for a provider mounted under the unified omk CLI."""

    name: str
    aliases: tuple[str, ...]
    command: click.Command
    config_keys: tuple[str, ...]
    supports_self_hosted: bool = False


PROVIDER_SPECS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        name="plane",
        aliases=("pl",),
        command=plane,
        config_keys=("plane.base_url", "plane.api_key", "plane.workspace_slug", "plane.project_id"),
        supports_self_hosted=True,
    ),
    ProviderSpec(
        name="linear",
        aliases=("ln",),
        command=linear,
        config_keys=("linear.api_key", "linear.team_id"),
    ),
)


def iter_provider_specs() -> tuple[ProviderSpec, ...]:
    """Return registered provider definitions."""

    return PROVIDER_SPECS

