# Task Switching

Switch to a different task by suspending current work and starting fresh.

## Overview

Use `omk hooks switch-task` to move current session Work Items to a suspended state and prepare for a new task. Switch history is recorded in the timeline.

## CLI Commands

### Switch Task

```bash
# Basic switch (move current WIs to stale)
omk hooks switch-task

# With new task title and reason
omk hooks switch-task --new "Emergency bug fix" --reason "Production incident"

# Specify session
omk hooks switch-task --session-id abc12345 --new "New feature"
```

## How It Works

1. **Suspend current Work Items**: The session's `work_item_ids` move to `stale_work_item_ids`.
2. **Timeline recording**: A `task_switch` event is added.
3. **Session saved**: The updated state is saved to the local file.

## After Switching

- Suspended Work Items are not deleted. They remain visible in Plane.
- If `--new` is specified, a new WI will be created automatically during the next session hook execution.
- You can also use the `/oh-my-kanban:focus` skill to focus on a different existing WI.

## Timeline Example

```text
2026-01-01T10:00:00 [scope_init] Session started
2026-01-01T10:30:00 [task_switch] Task switch | New task: Emergency bug fix | Reason: Production incident
2026-01-01T11:00:00 [prompt] Session ended normally
```

## Notes

- Cannot switch without an active session.
- Session scope and statistics are preserved during switching.
- Frequent task switching may reduce session tracking accuracy.
