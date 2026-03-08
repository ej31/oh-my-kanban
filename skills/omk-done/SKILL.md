---
name: omk-done
description: Changes the current session's Work Item status to "Done".
---

# omk done - Mark Current WI as Done

Changes the current session's Work Item status to "Done".

## Trigger Conditions

When the user requests "/oh-my-kanban:done", "/omk:d" or phrases like "task is done", "close the WI", "mark as complete" etc.

## Procedure

### 1. Check Current WI

Check the session's focused_work_item_id. If not set:

```text
[omk] No Task is linked to the current session.
  Please link a Task first using /oh-my-kanban:focus.
```

### 2. Retrieve Done Status

Dynamically retrieve the "Done" status ID for the project:

```text
mcp__plane__list_states(project_id="<project_id>")
```

Find the done status in the following order:

1. First status where `group="completed"`
2. Status with a completed-state name such as "Done" or "Completed"

### 3. User Confirmation

Confirm with the user before changing the status.

```text
[omk] Mark <identifier> as done?
  Status will only be changed upon yes/confirm response.
```

Proceed to the next step only if the user explicitly confirms.

### 4. Mark as Done

```text
mcp__plane__update_work_item(
  work_item_id="<focused_wi_id>",
  state_id="<completed_state_id>"
)
```

### 5. Add Completion Comment

```text
mcp__plane__create_work_item_comment(
  work_item_id="<focused_wi_id>",
  comment_html="## omk Session Complete\n\n**Session ID**: `<session_id[:8]>...`\n"
  "**Completed at**: <timestamp>\n**Summary**: <scope_summary>"
)
```

### 6. Confirmation Notification

```text
[omk] Task has been marked as done.
  WI: <identifier> - <wi_name>
  Status: <previous_state> -> Done
  URL: <plane_url>
```

## Notes

- Get user confirmation before marking as done
  e.g., "Mark OMK-5 as done?"
- If there are sub-tasks with incomplete items, display a warning
- If the done status cannot be found, guide the user to handle it manually
- Display a clear error message if status change fails
