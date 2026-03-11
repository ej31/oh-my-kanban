"""Compatibility alias for Linear team commands."""

import sys

from oh_my_kanban.providers.linear.commands import team as _team_module

sys.modules[__name__] = _team_module
