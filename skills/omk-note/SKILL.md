---
name: omk-note
description: Adds a memo/comment to the Plane Work Item linked to the current session.
---

# omk note - Add a memo to the current Task

Adds a memo/comment to the Plane Work Item linked to the current session.

## Trigger conditions

When the user requests "/oh-my-kanban:note", "/omk:n", or
phrases like "leave a memo", "add a comment", "record this", etc.

## Procedure

### 1. Check the current WI

Check the linked WI from the current session's PlaneContext:

- `state.plane_context.focused_work_item_id` - focused WI (priority)
- `state.plane_context.work_item_ids[0]` - first linked WI (fallback)

If no WI exists:

```text
No Task is linked. Link a Task with /oh-my-kanban:focus or
create a new Task with /oh-my-kanban:create-task.
```

### 2. Confirm memo content

Use the text provided by the user as the memo. If not provided, request it:

```text
What would you like to record?
```

### 3. Choose the comment format

Use an appropriate format based on the memo type:

**General memo:**

```html
<p>[{timestamp}] {sanitize_comment(memo_text)}</p>
```

**Decision:**

```html
<h3>Decision</h3>
<ul>
  <li>Decision: {sanitize_comment(decision)}</li>
  <li>Reason: {sanitize_comment(reason)}</li>
  <li>Alternatives considered: {sanitize_comment(alternatives)}</li>
</ul>
```

**Progress update:**

```html
<h3>Progress</h3>
<p>{sanitize_comment(status_update)}</p>
```

### 4. Add the comment

```python
mcp__plane__create_work_item_comment(
  work_item_id="<focused_work_item_id>",
  comment_html="<formatted_comment>"
)
```

### 5. Confirm completion

```text
[omk] Memo recorded.
  WI: <identifier> - <wi_name>
  Content: <memo_summary>
```

## Reading the current PlaneContext

- `state.plane_context.focused_work_item_id` - WI UUID to add the memo to
- `state.plane_context.project_id` - project ID

## Notes

- Do not include sensitive information (API keys, passwords, etc.) in memos
- If adding a comment fails, provide the user with a clear error and a Plane web link
- Structure long memos in HTML format to improve readability
