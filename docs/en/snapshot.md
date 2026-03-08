# Snapshot

Save and restore session state at specific points in time.

## Overview

Snapshots save the current session state (scope, statistics, Work Item connections, timeline) as JSON files. Take snapshots before and after important work to restore previous states when needed.

## CLI Commands

### Save Snapshot

```bash
# Save the most recent active session
omk hooks snapshot save

# Specify a session
omk hooks snapshot save --session-id abc12345
```

### List Snapshots

```bash
omk hooks snapshot list
```

Example output:

```text
=== Snapshot List ===
  abc12345_20260101T100000  Session: abc12345...  OAuth refactoring
  def67890_20260101T090000  Session: def67890...  API endpoint addition
```

### Restore Snapshot

```bash
# Restore (warns if active sessions exist)
omk hooks snapshot restore abc12345_20260101T100000

# Force restore
omk hooks snapshot restore abc12345_20260101T100000 --force
```

## Snapshot File Structure

Snapshots are stored in `~/.config/oh-my-kanban/snapshots/`.

Filename format: `{session_id_prefix}_{timestamp}.json`

```json
{
  "session_id": "abc12345-...",
  "status": "active",
  "scope": {
    "summary": "OAuth refactoring",
    "topics": ["auth", "oauth"]
  },
  "stats": { ... },
  "timeline": [ ... ],
  "snapshot_version": 1,
  "snapshot_created_at": "2026-01-01T10:00:00+00:00"
}
```

## Notes

- Snapshot files are owner read/write only (0o600 permissions).
- API keys and sensitive information are not included in snapshots.
- Restoring while active sessions exist may cause conflicts. Use `--force` to override.
- Snapshots persist until manually deleted.
