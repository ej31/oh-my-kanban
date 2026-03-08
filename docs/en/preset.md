# Presets

Presets bundle commonly used settings so you can apply them all at once.

## Overview

When different projects need different settings, use presets instead of changing individual values each time. Three built-in presets are provided, and you can create custom presets.

## Built-in Presets

| Preset | task_mode | upload_level | Description |
|--------|-----------|--------------|-------------|
| `minimal` | flat | none | Minimal setup. Local recording only, no comment uploads. |
| `standard` | main-sub | metadata | Standard setup. Metadata comment uploads. |
| `verbose` | main-sub | full | Detailed recording. Full comments with timeline. |

## CLI Commands

### List Presets

```bash
omk config preset list
```

### Apply Preset

```bash
# Apply a built-in preset
omk config preset apply minimal

# Apply to a specific profile
omk config preset apply verbose --profile work
```

### Create Custom Preset

```bash
# Save current settings as a preset
omk config preset create my-setup

# With description
omk config preset create my-setup -d "Team project settings"
```

### Export Preset

```bash
# Output as TOML
omk config preset export my-setup
```

Example output:

```toml
[preset]
name = "my-setup"
description = "Team project settings"
task_mode = "main-sub"
upload_level = "full"
drift_sensitivity = 0.7
drift_cooldown = 2
```

## User Preset Files

Custom presets are stored as TOML files in `~/.config/oh-my-kanban/presets/`.

## Notes

- Built-in presets cannot be modified.
- Preset names may only contain letters, numbers, hyphens, and underscores.
- Applying a preset overwrites existing settings. Check current settings before applying.
