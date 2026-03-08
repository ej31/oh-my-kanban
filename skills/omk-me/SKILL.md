---
name: omk-me
description: Shows the current session's status, linked WIs, progress, and more.
---

# omk me - View current session information

Shows the current session's status, linked WIs, progress, and more.

## Trigger conditions

When the user requests "/oh-my-kanban:me", "/omk:me", or
phrases like "show current session status", "tell me my work status", "check omk status", etc.

## Procedure

### 1. Read the session file

Read the current session's status from the session file.

### 2. Display session information

```text
[omk] Current Session Info
  Session ID: <session_id[:8]>...
  Started at: <created_at (converted to local time)>
  Session duration: <duration>

  Linked Task: <identifier> - <wi_name>
     URL: <plane_url>
     Status: <wi_status>

  Progress stats:
     Requests: <total_prompts>
     Files modified: <files_touched_count>
     Scope drift warnings: <drift_warnings>
     Scope auto-expansions: <scope_expansions>

  Session goal:
     <scope_summary>

  Key files modified:
     <files_touched[:5]>

  Last comment poll: <last_comment_check or 'none'>
```

If no WI is linked:

```text
  Linked Task: None
     Link a Task with /oh-my-kanban:focus or create a new one with /oh-my-kanban:create-task.
```

### 3. Current user information (optional)

Query the currently authenticated user via the Plane API:

```python
mcp__plane__get_me()
```

## Notes

- If reading the session file fails, output "Unable to load session information"
- Convert timestamps to the user's local timezone where possible
- If the local timezone cannot be determined, display timestamps in UTC and label them clearly
- Construct the WI URL from `base_url`, `workspace_slug`, and `project_id` in the config
