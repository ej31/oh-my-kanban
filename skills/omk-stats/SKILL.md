---
name: omk-stats
description: Analyzes and summarizes session statistics and Work Item status for the current project.
---

# omk stats - Session/WI Statistics Dashboard

Analyzes and summarizes session statistics and Work Item status for the current project.

## Execution steps

1. **Aggregate session files**

   - Read `~/.config/oh-my-kanban/sessions/*.json`
   - Aggregation items:
     - Total number of sessions
     - Total number of prompts (sum of `stats.total_prompts`)
     - Total number of modified files (deduplicated `stats.files_touched`)
     - Total drift warnings (sum of `stats.drift_warnings`)
     - Average prompts per session
   - Hotspot files (files modified in 5 or more sessions):

     ```text
     [hotspot] src/auth.py - modified in 7 sessions (refactoring review recommended)
     ```

2. **Retrieve WI status (when Plane API is available)**

   - Retrieve the full WI list with `mcp__plane__list_work_items`
   - Calculate status distribution (In Progress / Backlog / Done, etc.)
   - Calculate completion rate: `completed WIs / total WIs * 100`
   - List of 10 most recent WIs (by updated time)

3. **Output format**

```text
[omk stats] Session Statistics
  Total sessions: 24
  Total prompts: 1,247
  Modified files (unique): 89
  Drift warnings: 12
  Average prompts per session: 51.9

[omk stats] Hotspot Files (5+ sessions)
  src/oh_my_kanban/hooks/session_start.py - 12 sessions
  src/oh_my_kanban/session/state.py - 9 sessions
  src/oh_my_kanban/hooks/common.py - 7 sessions

[omk stats] WI Status
  Total: 35 | Done: 32 | In Progress: 2 | Backlog: 1
  Completion rate: 91.4%
```

## When no API key is set

Output session statistics only, skipping WI status:

```text
[omk stats] Plane API key is not configured; WI status cannot be retrieved.
  Configure it with /omk-setup.
```

## Notes

- If no session files exist, output "No session data yet"
- Skip files that fail to read (fail-open)
- Statistics are based on local session files and may differ from actual Plane state
