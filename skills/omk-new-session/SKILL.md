---
name: omk-new-session
description: Ends the current session and explicitly switches to a new work scope. Use this when previous work is complete and you are starting work with a completely different goal.
---

# omk-new-session - Start a New Work Session

Please end the current session and start a new work session.

**Step 1: End the current session**

Stop automatic tracking for the existing session:

```bash
omk hooks opt-out
```

`omk hooks opt-out` marks the session as opted out and preserves existing linked Work Items, but it does **not** post the normal SessionEnd summary comment.

**Step 2: Confirm readiness for the new session**

```bash
omk hooks status
```

Confirm there is no active session, then begin your new work.

**Step 3: Create a new Plane Work Item (optional)**

Create a Work Item in Plane that matches the new work scope. When the next Claude Code session starts, oh-my-kanban will automatically detect the new session and attempt to link it to a matching Work Item (if one exists).

After execution:
- The previous session stops being tracked
- The new session is automatically created when the next Claude Code conversation starts
- The new session will be linked to the new Plane Work Item (if created)

If you want the full SessionEnd summary comment, end the Claude Code conversation normally before starting a new one.

**Note**: Make sure all important work has been committed before ending the current session.
