---
name: omk-off
description: Disables oh-my-kanban automatic tracking for the current session.
---

# omk-off Skill Execution Guide

When the user executes /omk-off, perform the following:

## Opt-out Current Session

Execute the following command (automatically selects the most recently active session):
```bash
omk hooks opt-out
```

To specify a particular session:
```bash
omk hooks opt-out --session-id <SESSION_ID>
```

## After Completion

Once opted out, drift detection, file tracking, and WI integration will no longer operate for that session.

To reactivate, start a new Claude Code session (hooks are retained and will automatically reactivate in a new session).

To remove the hooks themselves: `omk hooks uninstall`
