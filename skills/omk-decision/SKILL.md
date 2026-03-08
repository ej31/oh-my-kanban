---
name: omk-decision
description: Records an important decision made during the current work as a Work Item comment.
---

# omk decision - Record Decision to WI

Records an important decision made during the current work as a Work Item comment.

## Trigger Conditions

When the user requests "/oh-my-kanban:decision", "/omk:dec" or phrases like
"record this decision", "log this decision to the WI", "save the decision" etc.

## Procedure

### 1. Check Current WI

Check `state.plane_context.focused_work_item_id`. If not set:

```text
[omk] No Task is linked to the current session.
  Please link a Task first using /oh-my-kanban:focus.
```

### 2. Collect Decision Details

If the user has not provided the decision details, infer them from the current conversation context and ask for confirmation:

- What was decided?
- Why was this decision made?
- What alternatives were considered?

### 3. Add Decision Comment

```python
# User input must be processed through sanitize_comment() or equivalent escaping before insertion
omk_add_comment(
  work_item_id="<focused_wi_id>",
  comment=(
    "## Decision Record\n\n"
    "**Decision**: <sanitized_decision_summary>\n\n"
    "**Rationale**: <sanitized_rationale>\n\n"
    "**Alternatives considered**: <sanitized_alternatives>\n\n"
    "---\n"
    "*Recorded by omk at <sanitized_timestamp>*"
  )
)
```

### 4. Confirmation Notification

```text
[omk] Decision has been recorded.
  WI: <identifier> - <wi_name>
  Decision: <decision_summary>
  URL: <plane_url>
```

## Notes

- If the decision content is unclear, ask the user for specific details
- Be careful not to include sensitive information in security/authentication-related decisions
- Display a clear error message if recording fails
