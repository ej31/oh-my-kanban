"""Compatibility alias for Linear label commands."""

import sys

from oh_my_kanban.providers.linear.commands import label as _label_module

sys.modules[__name__] = _label_module
