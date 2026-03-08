---
name: omk-setup
description: Configures Plane integration for oh-my-kanban.
---

# omk-setup - Plane Setup Workflow

Configures Plane integration for oh-my-kanban.

## Current command path

Use the existing config and hook commands:

```bash
omk config init
omk hooks install
```

You can then verify the result with:

```bash
omk doctor
omk hooks status
```

## Setup items

1. **Plane API URL** - Default: `https://api.plane.so`
   Use a custom base URL for self-hosted deployments.
2. **API key** - Issued from Plane Profile -> API Tokens
3. **Workspace slug** - The workspace segment in the Plane URL
4. **Project ID** - UUID of the current project
   If `PLANE_PROJECT_ID` is not set, the project can also be detected from `.omk/project.toml` or `CLAUDE.md`, depending on repository setup.

## Check current settings

To check PlaneContext information in the current session:

- `state.plane_context.project_id` - Connected project
- `state.plane_context.work_item_ids` - List of currently tracked WIs
- `state.plane_context.focused_work_item_id` - Focused WI

After completing the setup, restart Claude Code if needed and check the connection status with `omk hooks status` or the `/omk-status` skill.
