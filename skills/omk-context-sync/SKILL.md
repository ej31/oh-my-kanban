---
name: omk-context-sync
description: Retrieves the latest status of the Plane Work Item linked to the current session and updates the context.
---

# omk context-sync - Sync Latest Plane WI Status

Retrieves the latest status of the Plane Work Item linked to the current session and updates the context.

## Trigger Conditions

When the user requests "/oh-my-kanban:context-sync" or phrases like "sync WI status", "fetch latest comments" etc.

## Procedure

### 1. Read Current PlaneContext

Check the linked WIs from the current session's PlaneContext:

- `state.plane_context.focused_work_item_id` - focused WI (priority)
- `state.plane_context.work_item_ids` - full linked WI list
- `state.plane_context.project_id` - project ID

If no WI is linked, ask the user to link one using `/oh-my-kanban:focus`.

### 2. Retrieve Latest WI Status

```python
mcp__plane__retrieve_work_item(work_item_id="<focused_work_item_id>")
```

Extract from results:

- WI name, status, priority
- Assignee, due date
- Label list

### 3. Retrieve Recent Comments

```python
mcp__plane__list_work_item_comments(work_item_id="<focused_work_item_id>")
```

Fetch the 10 most recent comments and filter for new comments since `last_comment_check`.

### 4. Retrieve Sub-task List

```python
mcp__plane__list_work_items(project_id="<project_id>", parent="<focused_work_item_id>")
```

### 5. Output Sync Results Summary

```text
[omk] WI sync complete
  Task: <identifier>: <wi_name>
  Status: <state_name> | Priority: <priority>

  Recent comments (<n>):
    [<date>] <author>: <comment_preview>
    ...

  Sub-tasks (<n>):
    - <sub_task_1_name> (Done)
    - <sub_task_2_name> (In Progress)
    ...
```

### 6. Update PlaneContext

Update `last_comment_check` to the current time.
Add newly checked comment IDs to `known_comment_ids`.

## Reading Current PlaneContext

- `state.plane_context.focused_work_item_id` - WI to sync
- `state.plane_context.last_comment_check` - last sync time
- `state.plane_context.known_comment_ids` - list of already-checked comment IDs

## Notes

- If API fails, display a clear error and guide the user to run `/oh-my-kanban:doctor`
- Sync does not modify the Plane WI itself. However, the session's
  `last_comment_check` and `known_comment_ids` may be updated
- If there are no new comments, explicitly state "No new comments"
