---
name: omk-subtask
description: Creates a sub-task for the main Work Item of the current session.
---

# omk subtask - Create a sub-task for the current WI

Creates a sub-task for the main Work Item of the current session.

## Execution Conditions

When the user requests "/oh-my-kanban:subtask", "/omk:st" or "add subtask", "create subtask", etc.

## Procedure

### 1. Confirm current WI

Check the current parent WI from the session file:

- `state.plane_context.focused_work_item_id` - use this as `parent_id`

If no WI is linked:

```text
[omk] No Task linked to the current session.
  Please link a Task first using /oh-my-kanban:focus or /oh-my-kanban:create-task.
```

### 2. Collect Sub-task information

Confirm the Sub-task name with the user. Infer it from the conversation context if possible and request confirmation.

### 3. Create Sub-task

```python
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<subtask_name>",
  parent_id="<parent_wi_id>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:type:sub label ID>"]
)
```

State ID and Label ID are dynamically looked up, not hardcoded:

```python
mcp__plane__list_states(project_id="<project_id>")
mcp__plane__list_labels(project_id="<project_id>")
```

### 4. Confirmation Notification

```text
[omk] Sub-task created.
  WI: <identifier> - <subtask_name>
  Parent: <parent_identifier> - <parent_name>
  URL: <plane_url>
```

## Notes

- Confirm the Sub-task name with the user before creation
- Automatically apply the `omk:type:sub` label to Sub-tasks
- Display a clear error message if creation fails
