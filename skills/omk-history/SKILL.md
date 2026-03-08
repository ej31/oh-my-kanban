---
name: omk-history
description: Displays the omk session comment history for the current Work Item in chronological order.
---

# omk history - View Session Contribution History for Current WI

Displays the omk session comment history for the current Work Item in chronological order.

## Execution Steps

1. **Check current WI in session status**
   - Use `focused_work_item_id` or `work_item_ids[0]`

2. **Retrieve WI comments**

   ```python
   mcp__plane__list_work_item_comments(
       project_id=<current project_id>,
       work_item_id=<focused_work_item_id>
   )
   ```

3. **Filter omk session-related comments**
   - Pattern: omk session start/end markers, commit log markers, or handoff markers

4. **Output results** (in the following format):

```text
[omk] Work Item Contribution History: {wi_identifier} - {wi_name}

  [2026-03-07 09:15 UTC] Session Start (sess-abc123...)
    Goal: Implement OAuth2 Provider

  [2026-03-07 09:42 UTC] Commit: a1b2c3d

  [2026-03-07 10:30 UTC] Session End (sess-abc123...)
    23 requests, 4 files modified, duration 1 hour 15 minutes

  [2026-03-08 14:00 UTC] Handoff Memo
    "refresh_token incomplete, from token_store.py line 36"

Total Sessions: N | Total Requests: N | Total Commits: N
```

## Precautions

- If no WI is connected, display "No Work Item connected to the current session."
- If there are many comments, display only the most recent 20.
- If no omk comments exist, display "No session history recorded."
