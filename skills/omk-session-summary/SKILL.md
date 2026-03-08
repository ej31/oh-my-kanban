---
name: omk-session-summary
description: Syncs the current session's progress to the linked Plane Work Item. Use this when you want to record progress before the session ends.
---

# omk session-summary — Sync Current Session Progress

Sync the current session's progress to the linked Plane Work Item.

## Planned Command

```bash
omk hooks sync
```

> Note: `omk hooks sync` is planned, but it is not implemented in the current release.

## Current Supported Workflow

### Option A: End the Claude Code conversation normally

When the conversation ends normally, the SessionEnd hook posts the session summary comment automatically.

This is the only currently implemented path for writing the full session summary comment automatically.

### Option B: Stop tracking without posting the summary

```bash
omk hooks opt-out
```

`omk hooks opt-out` stops tracking for the current session and preserves existing Work Items, but it does **not** post the full SessionEnd summary comment.

### If the session is not linked to a Work Item

Link the session first with `/omk-link-work-item` or `/omk-focus`, then end the conversation normally to let SessionEnd post the summary.

```bash
omk hooks status
```
