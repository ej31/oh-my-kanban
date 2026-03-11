"""Compatibility alias for Linear project commands."""

import sys

from oh_my_kanban.providers.linear.commands import project as _project_module

sys.modules[__name__] = _project_module
