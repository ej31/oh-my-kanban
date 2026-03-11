"""Compatibility alias for Linear issue commands."""

import sys

from oh_my_kanban.providers.linear.commands import issue as _issue_module

sys.modules[__name__] = _issue_module
