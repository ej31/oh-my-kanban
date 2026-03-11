"""Provider-neutral root context."""

from __future__ import annotations

from dataclasses import dataclass

from oh_my_kanban.config import Config


@dataclass
class AppContext:
    """Root CLI context shared by provider groups."""

    profile: str
    output: str
    config: Config

