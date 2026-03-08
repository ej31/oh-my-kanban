---
name: omk-create-task
description: Creates a new Plane Work Item and links it to the current session.
---

# omk create-task - Create New Task + Link to Session

Creates a new Plane Work Item and links it to the current session.

## Trigger Conditions

When the user requests "/oh-my-kanban:create-task", "/omk:ct" or phrases like "create a new task", "make a Task" etc.

## Procedure

### 1. Collect Task Information

Confirm the Task name and description with the user. If it can be inferred from conversation context, infer it and ask for confirmation:

```text
New Task name: <user input or inferred>
Description (optional): <user input>
```

### 2. Check task_mode in Config (Planned — not yet wired into creation flow)

> **Note**: `task_mode` support is currently standalone (`src/oh_my_kanban/session/task_format.py`) and not yet integrated into the WI creation flow. The steps below describe the planned behavior.

Check the `task_mode` value in `~/.config/oh-my-kanban/config.toml`:
- `main-sub`: Create as MainTask structure (standalone WI, omk:type:main label)
- `module-task-sub`: Create as Task linked to a Module (requires Module selection)

### 3. Create WI

Create the WI. Currently, a simple standalone WI is created regardless of task_mode. The mode-specific structures below are planned for future integration:

**Mode A (main-sub):**
```text
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<task_name>",
  description="<description>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:session label ID>", "<omk:type:main label ID>"]
)
```

**Mode B (module-task-sub):**
First retrieve the Module list:
```text
mcp__plane__list_modules(project_id="<project_id>")
```
After selecting a Module, create the WI:
```text
mcp__plane__create_work_item(
  project_id="<project_id>",
  name="<task_name>",
  description="<description>",
  state_id="<in_progress_state_id>",
  label_ids=["<omk:session label ID>"]
)
mcp__plane__add_work_items_to_module(module_id="<module_id>", work_item_ids=["<new_wi_id>"])
```

### 4. Add Session Start Comment

Add a session start comment to the created WI:
```text
mcp__plane__create_work_item_comment(
  work_item_id="<new_wi_id>",
  comment_html="## omk Session Start\n\n**Session ID**: `<session_id[:8]>...`\n**Start time**: <timestamp>\n**Goal**: <task_name>"
)
```

### 5. Update PlaneContext

Reflect the created WI UUID in the session's plane_context:
- Add new WI UUID to `work_item_ids`
- Set `focused_work_item_id` to the new WI UUID

### 6. Confirmation Notification

```text
[omk] Task has been registered.
  WI: <identifier> - <task_name>
  URL: <plane_url>
  If you have important notes or context, please leave them as comments at the link above.
  They will be automatically referenced in this session.
```

## Reading Current PlaneContext

- `state.plane_context.project_id` - project ID to create in
- `state.plane_context.work_item_ids` - existing linked WI list
- If `project_id` is not set, guide the user through `/omk-setup` or the `omk config init` + `omk hooks install` workflow first

## Notes

- Always confirm the name with the user before creating a WI
- Do not hardcode State IDs; dynamically retrieve them via `mcp__plane__list_states`
- Do not hardcode Label IDs; dynamically retrieve them via `mcp__plane__list_labels`
- Display a clear error message if creation fails
