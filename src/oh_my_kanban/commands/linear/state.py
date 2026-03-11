"""Compatibility alias for Linear state commands."""

import sys

from oh_my_kanban.providers.linear.commands import state as _state_module

sys.modules[__name__] = _state_module
