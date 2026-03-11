"""Compatibility alias for the Linear me command."""

import sys

from oh_my_kanban.providers.linear.commands import me as _me_module

sys.modules[__name__] = _me_module
