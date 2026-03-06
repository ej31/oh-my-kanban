# AGENTS.md — oh-my-kanban Integration Guide for AI Agents

## Overview

oh-my-kanban (omk) is a Python CLI designed with AI agents as the primary user. All commands support non-interactive setup via environment variables and JSON output for machine-readable integration into agent pipelines.

**Repository:** https://github.com/ej31/oh-my-kanban

## Non-Interactive Setup

Set these environment variables once to enable automated workflows:

```bash
export PLANE_BASE_URL=https://api.plane.so         # API server URL (default: plane.so cloud)
export PLANE_API_KEY=<your-api-key>                # API token (required)
export PLANE_WORKSPACE_SLUG=<workspace-slug>       # Workspace identifier (required)
export PLANE_PROJECT_ID=<project-uuid>             # Default project (optional, auto-detected from CLAUDE.md)
export PLANE_PROFILE=default                       # Profile name (optional)
```

## Machine-Readable Output

Always use `-o json` for agent pipelines to get structured output:

```bash
omk -o json work-item list
omk -o json project list
omk -o json cycle create --name "Sprint 1" --start-date 2026-03-06
```

All commands support:
- `-o/--output [table|json|plain]` — Output format (default: table)
- `--profile PROFILE` — Configuration profile (default: default)
- `-w/--workspace SLUG` — Workspace override
- `-p/--project PROJECT_ID` — Project override

## Complete Command Reference

### config

Configuration management. Interactive mode is NOT suitable for agents; use environment variables instead.

```bash
omk config init                    # Interactive setup (agents: use env vars instead)
omk config show                    # Display current configuration
omk config show --profile DEV      # Show DEV profile
omk config set KEY VALUE           # Set a config value (keys: base_url, api_key, workspace_slug, project_id, output)
omk config set base_url https://plane.example.com

omk config profile list            # List all profiles
omk config profile use PROFILE     # Switch default profile
```

### user

User management.

```bash
omk user me                        # Get current user info (returns: id, display_name, email)
```

### workspace

Workspace-level management.

```bash
omk workspace members              # List workspace members
omk workspace features             # List workspace features (epics, modules, cycles, views, pages, intakes, teams, customers, wiki, pi)
omk workspace update-features --wiki true --initiatives true  # Enable features
```

### project

Project management.

```bash
omk project list                              # List all projects
omk project list --all                        # Fetch all pages (paginated by default, 50 per page)
omk project list --per-page 100               # Custom page size

omk project get PROJECT_ID                    # Get project details
omk project create --name "MyProject" --identifier PROJ --description "Desc" --timezone Asia/Seoul
omk project update PROJECT_ID --name "NewName" --description "NewDesc"
omk project delete PROJECT_ID                 # Delete (requires confirmation)

omk project members PROJECT_ID                # List project members
omk project features PROJECT_ID               # List project features (epics, modules, cycles, views, pages, intakes, work_item_types)
omk project update-features PROJECT_ID --epics --no-pages --cycles  # Enable/disable features
omk project worklog-summary PROJECT_ID        # Get project worklog summary
```

**Note on plane.so:** Avoid special characters (hyphens, etc.) in project names on plane.so cloud; the server may reject them.

### state

Work item status management.

```bash
omk state list                     # List all states
omk state get STATE_ID             # Get state details
omk state create --name "In Review" --color "#FF5733" --group started  # Create state
omk state update STATE_ID --name "Reviewing" --color "#FF5733"
omk state delete STATE_ID          # Delete (requires confirmation)
```

State groups: `backlog`, `unstarted`, `started`, `completed`, `cancelled`

### label

Label management.

```bash
omk label list                     # List all labels
omk label get LABEL_ID             # Get label details
omk label create --name "bug" --color "#FF0000" --parent PARENT_ID  # Create label
omk label update LABEL_ID --name "critical-bug" --color "#FF0000"
omk label delete LABEL_ID          # Delete (requires confirmation)
```

### work-item

Work item (issue) management.

```bash
omk work-item list                 # List work items (per_page: 50)
omk work-item list --all           # Fetch all work items
omk work-item list --per-page 100 --order-by name --priority high

omk work-item get WORK_ITEM_ID     # Get work item details
omk work-item get PROJECT-123      # Also supports PROJECT-SEQUENCE format

omk work-item create --name "Fix login bug" \
  --description "Login fails on mobile" \
  --priority high \
  --state STATE_ID \
  --assignee USER_ID1 --assignee USER_ID2 \
  --label LABEL_ID1 --label LABEL_ID2 \
  --start-date 2026-03-06 --target-date 2026-03-13 \
  --point 5

omk work-item update WORK_ITEM_ID --name "NewName" --priority urgent --state STATE_ID

omk work-item delete WORK_ITEM_ID  # Delete (requires confirmation)

omk work-item search --query "login"  # Search across workspace
```

Priority: `urgent`, `high`, `medium`, `low`, `none`

#### work-item comment

```bash
omk work-item comment list WORK_ITEM_ID       # List comments
omk work-item comment get WORK_ITEM_ID COMMENT_ID
omk work-item comment create WORK_ITEM_ID --body "Great work!"
omk work-item comment update WORK_ITEM_ID COMMENT_ID --body "Updated comment"
omk work-item comment delete WORK_ITEM_ID COMMENT_ID
```

#### work-item link

```bash
omk work-item link list WORK_ITEM_ID          # List links
omk work-item link get WORK_ITEM_ID LINK_ID
omk work-item link create WORK_ITEM_ID --url "https://example.com/doc"
omk work-item link update WORK_ITEM_ID LINK_ID --url "https://example.com/newdoc"
omk work-item link delete WORK_ITEM_ID LINK_ID
```

Note: SDK does not support custom link titles; only URLs are stored.

#### work-item activity

Read-only activity log.

```bash
omk work-item activity list WORK_ITEM_ID      # List activities
omk work-item activity get WORK_ITEM_ID ACTIVITY_ID
```

#### work-item attachment

```bash
omk work-item attachment list WORK_ITEM_ID    # List attachments
omk work-item attachment get WORK_ITEM_ID ATTACHMENT_ID
omk work-item attachment create WORK_ITEM_ID --name "screenshot.png" --size 102400 --mime-type image/png
omk work-item attachment delete WORK_ITEM_ID ATTACHMENT_ID
```

#### work-item relation

Relations between work items (plane.so only; not supported on self-hosted CE).

```bash
omk work-item relation list WORK_ITEM_ID      # List relations
omk work-item relation create WORK_ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk work-item relation delete WORK_ITEM_ID --related-work-item ITEM_ID2
```

Relation types: `blocking`, `blocked_by`, `duplicate`, `relates_to`, `start_before`, `start_after`, `finish_before`, `finish_after`

#### work-item worklog

Time tracking (plane.so only; not supported on self-hosted CE).

```bash
omk work-item worklog list WORK_ITEM_ID       # List logs (columns: id, duration, description, logged_by, created_at)
omk work-item worklog create WORK_ITEM_ID --duration 120 --description "Frontend refactor"
omk work-item worklog update WORK_ITEM_ID WORKLOG_ID --duration 90 --description "Updated"
omk work-item worklog delete WORK_ITEM_ID WORKLOG_ID
```

### cycle

Sprint/cycle management.

```bash
omk cycle list                     # List cycles
omk cycle archived                 # List archived cycles
omk cycle get CYCLE_ID             # Get cycle details

omk cycle create --name "Sprint 1" \
  --start-date 2026-03-06 \
  --end-date 2026-03-20 \
  --description "First sprint"

omk cycle update CYCLE_ID --name "Sprint 1 (Extended)" --end-date 2026-03-27
omk cycle delete CYCLE_ID          # Delete (requires confirmation)
omk cycle archive CYCLE_ID         # Archive cycle
omk cycle unarchive CYCLE_ID       # Unarchive cycle

omk cycle items CYCLE_ID           # List work items in cycle
omk cycle add-items CYCLE_ID --items ITEM_ID1 --items ITEM_ID2  # Add multiple items
omk cycle remove-item CYCLE_ID ITEM_ID
omk cycle transfer CYCLE_ID --target TARGET_CYCLE_ID  # Move all items to another cycle
```

### module

Feature module management.

```bash
omk module list                    # List modules
omk module archived                # List archived modules
omk module get MODULE_ID           # Get module details

omk module create --name "Auth Module" \
  --description "Authentication system" \
  --status planned \
  --start-date 2026-03-06 \
  --target-date 2026-04-30

omk module update MODULE_ID --name "Auth & Security" --status in-progress
omk module delete MODULE_ID        # Delete (requires confirmation)
omk module archive MODULE_ID       # Archive module
omk module unarchive MODULE_ID     # Unarchive module

omk module items MODULE_ID         # List work items in module
omk module add-items MODULE_ID --items ITEM_ID1 --items ITEM_ID2
omk module remove-item MODULE_ID ITEM_ID
```

Module status: `backlog`, `planned`, `in-progress`, `paused`, `completed`, `cancelled`

### milestone

Release milestone management.

```bash
omk milestone list                 # List milestones
omk milestone get MILESTONE_ID     # Get milestone details

omk milestone create --title "v1.0" --target-date 2026-06-30
omk milestone update MILESTONE_ID --title "v1.1" --target-date 2026-07-31
omk milestone delete MILESTONE_ID  # Delete (requires confirmation)

omk milestone items MILESTONE_ID   # List work items in milestone
omk milestone add-items MILESTONE_ID --items ITEM_ID1 --items ITEM_ID2
omk milestone remove-items MILESTONE_ID --items ITEM_ID1 --items ITEM_ID2
```

### intake

Intake work items (external requests).

```bash
omk intake list                    # List intake items
omk intake get ISSUE_UUID          # Get intake details
omk intake create --name "Feature request" --description "HTML description" --priority high --source email
omk intake update ISSUE_UUID --status 1 --source web  # Status: -2=rejected, -1=snoozed, 0=pending, 1=accepted, 2=duplicate
omk intake delete ISSUE_UUID       # Delete
```

**CRITICAL:** Use the `issue` field UUID from `list` response, NOT the `id` field.

### page

Page/wiki management. Project pages require project context; workspace pages do not.

```bash
omk page get PAGE_ID               # Get project page
omk page get PAGE_ID --workspace   # Get workspace page

omk page create --name "API Docs" --description-html "<h1>Docs</h1>" --workspace
omk page create --name "Setup Guide" --description-html "<p>Guide</p>"  # Project page (requires -p PROJECT_ID)
```

## Common Workflows

### Create a work item and add to cycle

```bash
# 1. Create state first
STATE_ID=$(omk state create --name "In Progress" --color "#FF9800" -o json | jq -r '.id')

# 2. Create work item
ITEM=$(omk work-item create --name "Implement API" \
  --priority high --state "$STATE_ID" -o json)
ITEM_ID=$(echo "$ITEM" | jq -r '.id')

# 3. Create and add to cycle
CYCLE=$(omk cycle create --name "Sprint 1" \
  --start-date 2026-03-06 --end-date 2026-03-20 -o json)
CYCLE_ID=$(echo "$CYCLE" | jq -r '.id')

omk cycle add-items "$CYCLE_ID" --items "$ITEM_ID"
echo "Created work item $ITEM_ID in cycle $CYCLE_ID"
```

### Intake processing pipeline

```bash
# 1. List pending intakes
omk intake list -o json | jq '.results[] | select(.status==0)'

# 2. Accept or reject
INTAKE_ID=$(omk intake list -o json | jq -r '.results[0].issue')
omk intake update "$INTAKE_ID" --status 1  # Accept

# 3. Create work item from accepted intake
omk work-item create --name "From intake" --priority medium
```

### Assign work items to team members

```bash
# Get workspace members
MEMBER=$(omk workspace members -o json | jq -r '.results[0].id')

# Create work item with assignee
omk work-item create --name "Task" --assignee "$MEMBER"

# Or update existing
omk work-item update ITEM_ID --assignee "$MEMBER"
```

## Server Compatibility Matrix

| Feature              | plane.so | self-hosted CE |
|----------------------|----------|----------------|
| work-item CRUD       | ✅       | ✅             |
| cycle               | ✅       | ✅             |
| module              | ✅       | ✅             |
| state/label         | ✅       | ✅             |
| intake              | ✅       | ✅             |
| comment/link        | ✅       | ✅             |
| activity/attachment | ✅       | ✅             |
| page (project)      | ✅       | ✅             |
| page (workspace)    | ✅       | ❌ (Enterprise)|
| worklog             | ✅       | ❌ (Enterprise)|
| relation            | ✅       | ❌ (Enterprise)|
| milestone           | ✅       | ✅             |

## Error Handling

All commands exit with:
- **Exit code 0:** Success
- **Exit code 1:** Error (message printed to stderr)

Common errors:
- `"Given API token is not valid"` — Invalid or expired API key
- `"This feature is not currently supported on this server"` — Enterprise-only feature on Community Edition
- `"Workspace slug is required"` — Missing workspace (set `--workspace` or `PLANE_WORKSPACE_SLUG`)
- `"Project is required"` — Missing project (set `--project` or `PLANE_PROJECT_ID`)

## Known Quirks and Limitations

1. **Intake get/update/delete:** Use the `issue` UUID from `list`, not the `id` field
2. **plane.so project names:** Avoid special characters (hyphens, underscores may be rejected)
3. **cycle/module add-items:** Use `--items` flag (not `--item-ids`)
4. **Global flags position:** `-o`, `--profile`, `-w`, `-p` must come BEFORE subcommand
5. **Confirmation prompts:** Delete and some update operations require interactive confirmation; use `-o json` output to suppress
6. **Description formatting:** Plain text descriptions are auto-wrapped in `<p>` tags; use `--description-html` for custom HTML
7. **Links on work items:** SDK does not support custom titles; only URLs are stored
8. **Relations:** Only supported on plane.so; not available on Community Edition
9. **Worklog:** Only supported on plane.so and Enterprise Edition
10. **Page creation:** Workspace pages require `--workspace` flag; project pages require project context

## Configuration Files and CLAUDE.md Integration

The CLI auto-detects project_id from CLAUDE.md:

```xml
<plane_context>
- project_id: 12345678-90ab-cdef-1234-567890abcdef
</plane_context>
```

When no `PLANE_PROJECT_ID` is set and no `-p` flag is provided, the CLI searches parent directories for CLAUDE.md and extracts project_id automatically.

Configuration is stored in `~/.config/oh-my-kanban/config.toml`:

```toml
[default]
base_url = "https://api.plane.so"
api_key = "pl_..."
workspace_slug = "my-workspace"
project_id = ""
output = "table"

[dev]
base_url = "https://plane.example.com"
api_key = "pl_..."
workspace_slug = "dev-workspace"
```
