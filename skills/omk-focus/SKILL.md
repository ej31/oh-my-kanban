---
name: omk-focus
description: Connects the current Claude Code session to a specific Plane Work Item.
---

# omk focus - Connect session to an existing WI

Connects the current Claude Code session to a specific Plane Work Item.

## Execution Conditions

When the user requests "/oh-my-kanban:focus", "/omk:f", or "Connect WI", "Connect to YCF-123", etc.

## Procedure

### 1. Confirm WI identifier

Check if the user has provided a WI identifier (e.g., OMK-5, YCF-123).
If not provided, show a list of active WIs and prompt for selection:

```python
mcp__plane__list_work_items(project_id="<project_id>")
```

### 2. Retrieve WI

Retrieve the WI using the identifier provided by the user:

```python
mcp__plane__retrieve_work_item_by_identifier(identifier="OMK-5")
```

Or if a UUID is available directly:

```python
mcp__plane__retrieve_work_item(work_item_id="<uuid>")
```

### 3. Update PlaneContext

Read the current PlaneContext from the session file and update `work_item_ids` and `focused_work_item_id`:

```python
# In ~/.config/oh-my-kanban/sessions/<session_id>.json
# Add WI UUID to plane_context.work_item_ids
# Set plane_context.focused_work_item_id to the corresponding UUID
```

Actual updates are handled by the `omk` CLI or by directly modifying the session file.

### 4. Add Session Start Comment

Add a structured comment to the connected WI:

```python
mcp__plane__create_work_item_comment(
  work_item_id="<wi_uuid>",
  comment_html=(
    "## omk Session Connected\n\n"
    "**Session ID**: `<session_id[:8]>...`\n"
    "**Connection Time**: <timestamp>\n"
    "**Goal**: Manual connection by user request"
  )
)
```

### 5. Notify User

```text
[omk] Task connected.
  WI: <identifier> - <wi_name>
  URL: <plane_url>
  Work progress in this session will be automatically recorded.
```

## Reading Current PlaneContext

Current session PlaneContext information is checked in the session file:

- `state.plane_context.work_item_ids` - List of connected WI UUIDs
- `state.plane_context.focused_work_item_id` - Currently focused WI
- `state.plane_context.project_id` - Connected project

## Precautions

- If a WI is already connected, confirm with the user before replacing it.
- If WI retrieval fails, output a clear error message to the user.
