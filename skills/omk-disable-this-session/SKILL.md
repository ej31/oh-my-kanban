---
name: omk-disable-this-session
description: Disables omk automatic tracking for the current Claude Code session.
---

# omk disable-this-session - Disable Tracking for This Session

Disables omk automatic tracking for the current Claude Code session.
Use for simple Q&A sessions or work that doesn't require tracking.

## Trigger Conditions

When the user requests "/oh-my-kanban:disable-this-session", "/omk:off" or phrases like
"turn off tracking", "this session is just Q&A", "don't record anything" etc.

## Procedure

### 1. Check Current Session ID

Check the current session ID (from environment variables or session file).

### 2. Execute Opt-Out

```bash
omk hooks opt-out
```

This command performs the following:

- Sets `state.opted_out = True`
- Sets `state.status = "opted_out"`
- Adds a single structured comment if a WI is linked (does not delete the WI)
- Resets the HUD

### 3. WI Comment Format Reference (Illustrative Example)

The actual structured comment is recorded once within the `omk hooks opt-out` processing in Step 2.
The following is not a procedure for duplicate execution but an example showing what format the comment takes.

```text
mcp__plane__create_work_item_comment(
  work_item_id="<focused_work_item_id>",
  comment_html="<h2>omk Tracking Stopped</h2>
<ul>
  <li>Session ID: {session_id[:8]}...</li>
  <li>Timestamp: {timestamp}</li>
  <li>Reason: User request (simple Q&A session)</li>
  <li>Stats: {n} prompts, {n} files modified</li>
  <li>Status: No further contributions from this session.</li>
</ul>"
)
```

### 4. Confirmation Notification

```text
[omk] Task tracking has been disabled for this session.
  No more WI creation/updates will occur in this session.
  Already created Plane Work Items will be preserved.
  Start a new session to re-enable tracking.
```

## Reading Current PlaneContext

- `state.opted_out` - check current opt-out status
- `state.plane_context.focused_work_item_id` - WI to add comment to
- `state.stats.total_prompts` - statistics
- `state.stats.files_touched` - list of modified files

## Notes

- **Never delete WIs** - contribution records from other sessions could be lost
- After opt-out, SessionStart/End hooks operate as no-ops
- If already in opted_out state, prevent duplicate execution and notify the user
- Opt-out only affects the current session - other sessions and future sessions are not affected
