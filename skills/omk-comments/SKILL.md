---
name: omk-comments
description: Shows recent comments on the Work Item linked to the current session.
---

# omk comments - View Recent Comments on Current WI

Shows recent comments on the Work Item linked to the current session.

## Trigger Conditions

When the user requests "/oh-my-kanban:comments", "/omk:cm", or phrases like
"show comments", "check WI comments", "any team comments?" etc.

## Procedure

### 1. Check Current WI

Check `state.plane_context.focused_work_item_id`. If not set:

```text
[omk] No Task is linked to the current session.
  Please link a Task first using /oh-my-kanban:focus.
```

### 2. Retrieve Comments

```python
mcp__plane__list_work_item_comments(
  work_item_id="<focused_wi_id>"
)
```

### 3. Display Results

Show the 10 most recent comments in reverse chronological order:

```text
[omk] WI: <identifier> - <wi_name>
  Recent comments (<count>):

  Comment: <author> (<timestamp>):
  <comment_text>

  Comment: <author> (<timestamp>):
  <comment_text>

  ...
```

If there are no comments:

```text
[omk] No comments on <identifier>.
  URL: <plane_url>
```

### 4. Handle New Comments

If there are new comments (added since the last poll), highlight them.

Update the session's `known_comment_ids` with the latest comment ID list.

## Notes

- Display a clear error message if comment retrieval fails
- Comments posted by omk itself (starting with ## omk) should be visually distinguished with a different color/format
- If multiple WIs are linked, show comments for the focused WI
