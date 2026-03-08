---
name: omk-sprint
description: Retrieves active Sprint (Cycle) information and a list of incomplete Tasks for the current project.
---

# omk sprint - View Current Sprint (Cycle) Status

Retrieves active Sprint (Cycle) information and a list of incomplete Tasks for the current project.

## Execution Steps

1. **Retrieve Active Cycle**

```python
mcp__plane__list_cycles(project_id=<current_project_id>)
```

Find a Cycle with status "current" or an `end_date` in the future.

2. **Retrieve Work Items within Cycle**

```python
mcp__plane__list_cycle_work_items(
  project_id=<current_project_id>,
  cycle_id=<active_cycle_id>
)
```

3. **Categorize by Status**
   - Incomplete (group: started, unstarted, backlog)
   - Completed (group: completed, cancelled)

4. **Output Results** (in the following format):

```text
[omk] Sprint: {cycle_name}
  Period: {start_date} ~ {end_date} (D-{days_left})
  Progress: {done_count}/{total_count} ({percent}%)

  Incomplete Tasks ({incomplete_count} items):
    OMK-XXX: Task Name (In Progress)
    OMK-YYY: Task Name (Todo)
    ...
```

## Context Access

```python
# Retrieve project_id from session state
import json, pathlib
session_files = list(pathlib.Path.home().glob(".config/oh-my-kanban/sessions/*.json"))
# Use plane_context.project_id from the most recent file
```

Or reference the `OMK_PROJECT_ID` environment variable in the MCP settings.

## Notes

- If no Cycle exists, display "No active Sprint."
- If API call fails, output an error message and terminate.
- Highlight warning if deadline is within 3 days.
