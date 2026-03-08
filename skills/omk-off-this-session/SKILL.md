---
name: omk-off-this-session
description: Stops oh-my-kanban automatic tracking for the current Claude Code session. Already-created Plane Work Items are preserved.
---

# omk-off-this-session - Disable Tracking for This Session

Please stop oh-my-kanban automatic tracking for the current Claude Code session.

Run the following command:

```bash
omk hooks opt-out
```

This command automatically finds the most recent active session and stops tracking.

After execution:
- A comment "Automatic tracking for this session has been stopped at the user's request" will be added to the already-created Plane Work Item
- Work that occurs after this point in the session will no longer be recorded
- Plane sync will be skipped when the session ends (SessionEnd)

To specify a particular session:
```bash
omk hooks status          # Check the session ID
omk hooks opt-out --session-id <SESSION_ID>
```
