---
name: omk-hooks-doctor
description: Diagnoses and fixes oh-my-kanban hook installation issues. Use when session tracking is not working or hook-related errors occur.
---

# omk-hooks-doctor - Diagnose Hook Installation

Use this skill when session tracking is not starting, hook wiring looks broken, or you need to verify the current Claude Code hook installation.

## 1. Check Current Hook Status

Run:

```bash
omk hooks status
```

Summarize:
- whether hooks are installed globally, per-project, or local-only
- which hook events are registered
- whether any active sessions are visible

## 2. Reinstall Hooks If Needed

If hooks are missing or stale, reinstall them with the appropriate scope:

```bash
omk hooks install
```

For a clean reinstall:

```bash
omk hooks uninstall
omk hooks install
```

Project-specific installs use `.claude/settings.json`, local-only installs use `.claude/settings.local.json`, and global installs use `~/.claude/settings.json`.

## 3. Run Product Diagnostics

If the hook wiring is present but tracking still fails, run:

```bash
omk doctor
```

Use the `omk-doctor` or `omk-setup` skills when you need guided recovery for configuration or API issues.

## Common Troubleshooting

| Symptom | Solution |
| --- | --- |
| `omk hooks status` shows no omk hooks | Run `omk hooks install` again in the intended scope |
| Hooks are installed but no session is tracked | Restart Claude Code after installation, then check `omk hooks status` again |
| `omk` command is not found | Install or upgrade with `pip install oh-my-kanban` |
| Hook wiring exists but Plane/Linear access fails | Run `omk doctor` and follow the reported recovery steps |
| A project should not be tracked | Use `omk project opt-out` or the current-session opt-out workflow instead of removing files manually |

## Notes

- Do not rely on `~/.claude/hooks/` shell scripts; this project installs hook configuration through Claude settings JSON files.
- Prefer `omk hooks status`, `omk hooks install`, `omk hooks uninstall`, and `omk doctor` over ad hoc file edits.
