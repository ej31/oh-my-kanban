"""Single source of truth for registered providers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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


_COMMANDS: dict[str, click.Command] = {
    "plane": plane,
    "linear": linear,
}


def _metadata_path() -> Path:
    """Return shared provider metadata path."""

    return Path(__file__).resolve().parents[3] / "shared" / "provider-metadata.json"


def _load_provider_specs() -> tuple[ProviderSpec, ...]:
    """Load provider metadata and attach runtime commands."""

    payload = json.loads(_metadata_path().read_text(encoding="utf-8"))
    specs: list[ProviderSpec] = []
    for provider in payload["providers"]:
        specs.append(
            ProviderSpec(
                name=provider["name"],
                aliases=tuple(provider.get("aliases", [])),
                command=_COMMANDS[provider["name"]],
                config_keys=tuple(provider.get("config_keys", [])),
                supports_self_hosted=bool(provider.get("supports_self_hosted", False)),
            )
        )
    return tuple(specs)


PROVIDER_SPECS = _load_provider_specs()


def iter_provider_specs() -> tuple[ProviderSpec, ...]:
    """Return registered provider definitions."""

    return PROVIDER_SPECS
