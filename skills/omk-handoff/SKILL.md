---
name: omk-handoff
description: Records a handoff memo for the next session or a team member as a Work Item comment.
---

# omk handoff - Record a Handoff Memo to a WI

Records a handoff memo for the next session or a team member as a Work Item comment.

## Trigger Conditions

When the user requests "/oh-my-kanban:handoff", "/omk:ho", or
phrases like "leave a handoff memo", "record a memo for the next session", etc.
Or when omk requests handoff recording via additionalContext at session end.

## Procedure

### 1. Check the Current WI

Check `state.plane_context.focused_work_item_id`. If missing:

```text
[omk] No Task is linked to the current session.
  There is no Work Item to leave a handoff memo on.
```

### 2. Collect Handoff Content

Collect handoff content based on the current session's work status:

- **Current status**: What has been completed?
- **Incomplete items**: What is remaining?
- **Next steps**: Where should the next session start?
- **Notes**: Are there any things to be aware of?

If the user does not provide content, automatically infer from the current conversation context.

### 3. Add the Handoff Comment

```python
mcp__plane__create_work_item_comment(
  work_item_id="<focused_wi_id>",
  comment_html="## Handoff\n\n**Current status**: <current_status>\n\n"
  "**Incomplete items**: <incomplete_items>\n\n**Next steps**: "
  "<next_steps>\n\n**Notes**: <notes>\n\n---\n"
  "*Recorded by omk at <timestamp> "
  "(Session ID: <session_id[:8]>...)*"
)
```

### 4. Present Draft to User for Confirmation

Present the draft handoff memo to the user for confirmation before posting.

### 5. Confirm Notification

```text
[omk] Handoff memo has been recorded.
  WI: <identifier> - <wi_name>
  This memo will be automatically displayed in the next session.
  URL: <plane_url>
```

## Notes

- Handoff memos must contain specific and actionable information.
- It is helpful to include specific location information such as file paths, function names, and line numbers.
- If recording fails, display a clear error message.
- HTML-escape all user-sourced dynamic fields before posting comments
