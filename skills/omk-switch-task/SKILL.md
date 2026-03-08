---
name: omk-switch-task
description: Switches the current session to a different Work Item. The existing WI will be set to "On Hold" status.
---

# omk switch-task - Switch to Another WI

Switches the current session to a different Work Item. The existing WI will be set to "On Hold" status.

## Execution Conditions

When the user requests "/oh-my-kanban:switch-task", "/omk:sw", "switch to another task", or "switch WI".

## Procedure

### 1. Confirm Current WI

Check `state.plane_context.focused_work_item_id`.

- If `focused_work_item_id` is missing, display an error message.
  Example: "No active WI found"
- If the new WI is the same as the current WI, do not switch.
  Example: "Already working on this WI"

### 2. Select New WI

If the user has not specified a new WI, show a list of active WIs and prompt for selection:

```python
mcp__plane__list_work_items(project_id="<project_id>")
```

If it's a new topic, confirm whether to create a new WI.

### 3. Change Existing WI to "On Hold"

Dynamically query "On Hold" status in the following order:

1. Status named "On Hold" (exact match)
2. Status named "Paused" (exact match)
3. Status named "Backlog" (exact match)
4. The first one in `group="backlog"`
5. If none, ask the user to select manually

```python
mcp__plane__update_work_item(
  work_item_id="<old_wi_id>",
  state_id="<on_hold_state_id>"
)
```

Add a comment to the existing WI:

```python
mcp__plane__create_work_item_comment(
  work_item_id="<old_wi_id>",
  comment_html=(
    "<h2>omk Work Paused</h2>"
    "<p><strong>Session ID</strong>: <code><session_id[:8]>...</code><br>"
    "<strong>Switch Time</strong>: <timestamp><br>"
    "<strong>Reason for Switch</strong>: Switched to another Task by user request</p>"
  )
)
```

### 4. Link Session to New WI

Add a session link comment to the new WI:

```python
mcp__plane__create_work_item_comment(
  work_item_id="<new_wi_id>",
  comment_html=(
    "<h2>omk Session Switched</h2>"
    "<p><strong>Session ID</strong>: <code><session_id[:8]>...</code><br>"
    "<strong>Switch Time</strong>: <timestamp><br>"
    "<strong>Previous Task</strong>: <old_wi_identifier></p>"
  )
)
```

### 5. Update Session Status

Update `plane_context.focused_work_item_id` in the session file with the new WI UUID.

### 6. Set Relationship (Optional)

Add a `relates_to` relationship only if the user explicitly requested it, or if the two WIs are consecutive tasks within the same functional context.
Omit if it's a complete replacement task or if the link would cause confusion.

Set a `relates_to` relationship between the two WIs:

```python
mcp__plane__create_work_item_relation(
  work_item_id="<old_wi_id>",
  related_work_item_id="<new_wi_id>",
  relation_type="relates_to"
)
```

### 7. Confirmation Notification

```text
[omk] Task switched.
  Previous: <old_identifier> - <old_wi_name> (On Hold)
  Current: <new_identifier> - <new_wi_name> (In Progress)
```

## Caveats

- Get user confirmation before switching
- If "On Hold" status is not found, use an alternative status and inform the user
- Display a clear error message if status change fails
