"""Compatibility alias for Linear cycle commands."""

import sys

from oh_my_kanban.providers.linear.commands import cycle as _cycle_module

sys.modules[__name__] = _cycle_module
