---
name: omk-session-status
description: Checks the current oh-my-kanban session tracking status. Displays the active session ID, goal, linked Plane Work Items, and progress statistics at a glance.
---

Please check the current oh-my-kanban session tracking status.

Run the following command:

```bash
omk hooks status
```

After execution, the following information is displayed:
- Current active session ID
- Session start time and elapsed time
- Linked Plane Work Item link (if any)
- Session goal and scope
- Number of actions detected so far / number of changed files
- Session state (active / opted_out / ended)

If the session is not linked to a specific Work Item, you can link it manually using `/omk-link-work-item`.
