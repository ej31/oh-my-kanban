---
name: omk-context-injection
description: Explicitly injects information from the Plane Work Item linked to the current session into Claude's context.
---

# omk context-injection - Manual Plane WI Context Injection

Explicitly injects information from the Plane Work Item linked to the current session into Claude's context.
Used for restoring context after compact or when previous work context is needed in a new session.

## Trigger Conditions

When the user requests "/oh-my-kanban:context-injection" or phrases like "load WI content", "restore previous work context", "inject Plane content" etc.

## Procedure

### 1. Read Current PlaneContext

Check the linked WIs from the current session's PlaneContext:
- `state.plane_context.work_item_ids` - list of linked WI UUIDs
- `state.plane_context.focused_work_item_id` - focused WI
- `state.plane_context.project_id` - project ID

### 2. Collect WI Information

For each linked WI:

```text
mcp__plane__retrieve_work_item(work_item_id="<wi_id>")
mcp__plane__list_work_item_comments(work_item_id="<wi_id>")
mcp__plane__list_work_items(project_id="<project_id>", parent="<wi_id>")
```

### 3. Structure the Context

Structure the collected information in the following format:

```text
[omk: Plane Work Item Context]

### <identifier>: <wi_name>
Status: <state_name> | Priority: <priority>
Description: <description_preview (max 500 chars)>

Recent comments (latest 10):
  [<date>] <author>: <comment_text>
  ...

Sub-tasks:
  - [Done] <sub_task_name>
  - [In Progress] <sub_task_name>
  ...
```

### 4. Auto-Injection Scenario (Session Resume)

After `/compact` occurs, the `SessionStart(compact)` hook automatically calls `build_plane_context()` to inject WI information as `additionalContext`.

Manual injection is needed when:
- WI information is missing even after compact
- You want to explicitly restore the context of a previous WI in a new session

### 5. Confirm Injection Results

```text
[omk] WI context has been injected.
  Task: <identifier>: <wi_name>
  Included: title, status, description, <n> comments, <n> sub-tasks
  You can now continue working with the WI context.
```

## Two Injection Modes

### Auto-Injection (SessionStart compact)

When `/compact` occurs, the `_handle_compact()` function in `session_start.py`:
1. Reads `work_item_ids` from the session file
2. Calls `build_plane_context()` (parallel retrieval via ThreadPoolExecutor)
3. Injects the result into Claude as `additionalContext`

### Manual Injection (This Skill)

1. User explicitly requests it
2. Collects WI information via MCP tools
3. Inserts structured text directly into the current conversation

## Reading Current PlaneContext

- `state.plane_context.work_item_ids` - list of WIs to inject context for
- `state.plane_context.focused_work_item_id` - priority target WI
- `state.scope.summary` - current session goal (for context supplementation)

## Notes

- If API fails, fall back to existing information stored in the session file
- Mask sensitive information (API keys, etc.) in comments as `[REDACTED]`
- Truncate context to 3000 characters if too long to prevent Claude context pollution
