---
name: omk-open
description: Displays the web URL of the Plane Work Item linked to the current session.
---

# omk open - Display the current Task web link

Displays the web URL of the Plane Work Item linked to the current session.

## Trigger conditions

When the user requests "/oh-my-kanban:open", "/omk:o", or
phrases like "show Task link", "open in Plane", etc.

## Procedure

### 1. Check the current WI

Check the linked WI from the current session's PlaneContext:

- `state.plane_context.focused_work_item_id` - focused WI (priority)
- `state.plane_context.work_item_ids` - list of linked WIs

If no WI exists:

```text
No Task is linked. Link a Task with /oh-my-kanban:focus or
create a new Task with /oh-my-kanban:create-task.
```

### 2. Retrieve WI details

```python
mcp__plane__retrieve_work_item(work_item_id="<focused_work_item_id>")
```

Extract `sequence_id` and the WI name from the response.

### 3. Construct the URL

Plane URL pattern:

```text
{base_url}/{workspace_slug}/projects/{project_id}/issues/{sequence_id}/
```

Read values from the configuration:

- `base_url`: `base_url` in `~/.config/oh-my-kanban/config.toml`
- `workspace_slug`: `workspace_slug` in the configuration
- `project_id`: `state.plane_context.project_id`

### 4. Output the URL

```text
[omk] Current Task
  WI: <identifier> - <wi_name>
  Status: <state_name>
  URL: <plane_url>

  Click or paste into your browser.
```

### 5. Handling multiple WIs

If multiple WIs are linked, display all of them:

```text
[omk] Linked Tasks
  1. <identifier1> - <name1>: <url1>
  2. <identifier2> - <name2>: <url2>
```

## Reading the current PlaneContext

- `state.plane_context.focused_work_item_id` - focused WI UUID
- `state.plane_context.work_item_ids` - full list of linked WIs
- `state.plane_context.project_id` - project ID needed for URL construction

## Notes

- Output the URL as a clickable hyperlink format
- Even if WI retrieval fails, attempt to construct the URL from information stored in the session file
- If `base_url` is not configured, use the plane.so default value
