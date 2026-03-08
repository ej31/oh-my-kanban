---
name: omk-snapshot
description: Saves or reviews a manual snapshot of the current session state.
---

# omk snapshot - Manual Session Snapshot Workflow

Use this skill when you want to save, inspect, or manually restore the current session state.

## Current Implementation Status

A dedicated `omk snapshot` CLI command is not implemented in the current release.
Handle snapshot requests by working directly with the local session JSON files.

## Save a Snapshot

1. Read the current session JSON file from `~/.config/oh-my-kanban/sessions/<session_id>.json`
2. Copy it to a timestamped file under `~/.config/oh-my-kanban/snapshots/`
3. If the user supplied a note, store it alongside the saved snapshot metadata
4. Report the saved path and a short summary

```text
[omk] Snapshot saved.
  File: ~/.config/oh-my-kanban/snapshots/{session_id}_20260308T143000.json
  Goal: {current scope.summary}
  Modified files: {len(files_touched)}
```

## List Snapshots

1. List files in `~/.config/oh-my-kanban/snapshots/`
2. Filter snapshots that belong to the current session when appropriate
3. Sort newest first
4. Show the snapshot ID, timestamp, and note if one exists

```text
[omk] Saved snapshots:
  1. omk-snap-2026-03-08T14:30:00 - "Before OAuth refactor cleanup"
  2. omk-snap-2026-03-08T12:00:00 - (no note)
```

## Restore a Snapshot

Restoring a snapshot overwrites the current session state. Always confirm with the user first.

1. Resolve the requested snapshot file
2. Confirm with the user that the current session state will be overwritten
3. If confirmed, restore the snapshot into the current session file while preserving the current `session_id`
4. Report the restored goal and key stats

```text
[omk] Snapshot restored.
  Goal: {restored scope.summary}
  Modified files: {len(files_touched)}
```

## Notes

- Create the snapshots directory automatically if it does not exist.
- Snapshot files should keep the same JSON shape as the original session files.
- Restoration is destructive and must require explicit user confirmation.
