---
name: omk-status
description: Displays Plane Work Item information linked to the current Claude Code session.
---

# omk status - Display Current Session WI Status

Displays Plane Work Item information linked to the current Claude Code session.

## Displayed information

1. **Linked WI list** - `state.plane_context.work_item_ids`
2. **Focused WI** - `state.plane_context.focused_work_item_id`
3. **Externally deleted WIs** - `state.plane_context.stale_work_item_ids`
4. **Session statistics** - request count, modified file count

## How to retrieve current status

Use the MCP tool for a summarized view:

```python
omk_get_session_status()
```

`omk_get_session_status()` currently returns `project_id`, `work_item_ids`, `module_id`, and session statistics. For `focused_work_item_id`, `stale_work_item_ids`, or comment polling timestamps, inspect the session file directly.

Or read directly from the session file:

```bash
cat ~/.config/oh-my-kanban/sessions/<session_id>.json | python3 -m json.tool
```

## Reading PlaneContext

Verify the following from the session state:

- `plane_context.project_id` - Project UUID
- `plane_context.work_item_ids` - List of tracked WI UUIDs
- `plane_context.focused_work_item_id` - Currently focused WI
- `plane_context.stale_work_item_ids` - Linked WIs that could not be loaded anymore
- `plane_context.last_comment_check` - Last comment polling time

If no WI is linked: connect one with `/oh-my-kanban:focus <WI-ID>` or `/oh-my-kanban:create-task`.
