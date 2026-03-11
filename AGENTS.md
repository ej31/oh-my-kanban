# AGENTS.md — oh-my-kanban Integration Guide for AI Agents

## Overview

oh-my-kanban (omk) is a Python CLI designed with AI agents as the primary user. All commands support non-interactive setup via environment variables and JSON output for machine-readable integration into agent pipelines.

**Repository:** https://github.com/ej31/oh-my-kanban

## Non-Interactive Setup

Set these environment variables once to enable automated workflows:

```bash
# Plane
export PLANE_BASE_URL=https://api.plane.so         # API server URL (default: plane.so cloud)
export PLANE_API_KEY=<your-api-key>                # API token (required)
export PLANE_WORKSPACE_SLUG=<workspace-slug>       # Workspace identifier (required)
export PLANE_PROJECT_ID=<project-uuid>             # Default project (optional, auto-detected from CLAUDE.md)
export PLANE_PROFILE=default                       # Profile name (optional)

# Linear
export LINEAR_API_KEY=<your-linear-api-key>        # Linear API token (required for linear commands)
export LINEAR_TEAM_ID=<team-uuid>                  # Default team (optional, passed via --team if omitted)
```

## Machine-Readable Output

Always use `-o json` for agent pipelines to get structured output:

```bash
omk -o json plane work-item list
omk -o json plane project list
omk -o json plane cycle create --name "Sprint 1" --start-date 2026-03-06
omk -o json linear issue list
```

All commands support:
- `-o/--output [table|json|plain]` — Output format (default: table)
- `--profile PROFILE` — Configuration profile (default: default)
- `-w/--workspace SLUG` — Workspace override
- `-p/--project PROJECT_ID` — Project override

**Global flags position:** `-o`, `--profile`, `-w`, `-p` must come BEFORE the provider subcommand.

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

---

## omk plane (or omk pl)

### user

```bash
omk plane user me                  # Get current user info (returns: id, display_name, email)
```

### workspace

```bash
omk plane workspace members              # List workspace members
omk plane workspace features             # List workspace features (epics, modules, cycles, views, pages, intakes, teams, customers, wiki, pi)
omk plane workspace update-features --wiki true --initiatives true  # Enable features
```

### project

```bash
omk plane project list                              # List all projects
omk plane project list --all                        # Fetch all pages (paginated by default, 50 per page)
omk plane project list --per-page 100               # Custom page size

omk plane project get PROJECT_ID                    # Get project details
omk plane project create --name "MyProject" --identifier PROJ --description "Desc" --timezone Asia/Seoul
omk plane project update PROJECT_ID --name "NewName" --description "NewDesc"
omk plane project delete PROJECT_ID                 # Delete (requires confirmation)

omk plane project members PROJECT_ID                # List project members
omk plane project features PROJECT_ID               # List project features
omk plane project update-features PROJECT_ID --epics --no-pages --cycles  # Enable/disable features
omk plane project worklog-summary PROJECT_ID        # Get project worklog summary
```

**Note on plane.so:** Avoid special characters (hyphens, etc.) in project names on plane.so cloud; the server may reject them.

### state

```bash
omk plane state list                     # List all states
omk plane state get STATE_ID             # Get state details
omk plane state create --name "In Review" --color "#FF5733" --group started
omk plane state update STATE_ID --name "Reviewing" --color "#FF5733"
omk plane state delete STATE_ID          # Delete (requires confirmation)
```

State groups: `backlog`, `unstarted`, `started`, `completed`, `cancelled`

### label

```bash
omk plane label list                     # List all labels
omk plane label get LABEL_ID             # Get label details
omk plane label create --name "bug" --color "#FF0000" --parent PARENT_ID
omk plane label update LABEL_ID --name "critical-bug" --color "#FF0000"
omk plane label delete LABEL_ID          # Delete (requires confirmation)
```

### work-item

```bash
omk plane work-item list                 # List work items (per_page: 50)
omk plane work-item list --all           # Fetch all work items
omk plane work-item list --per-page 100 --order-by name --priority high

omk plane work-item get WORK_ITEM_ID     # Get work item details
omk plane work-item get PROJECT-123      # Also supports PROJECT-SEQUENCE format

omk plane work-item create --name "Fix login bug" \
  --description "Login fails on mobile" \
  --priority high \
  --state STATE_ID \
  --assignee USER_ID1 --assignee USER_ID2 \
  --label LABEL_ID1 --label LABEL_ID2 \
  --start-date 2026-03-06 --target-date 2026-03-13 \
  --point 5

omk plane work-item update WORK_ITEM_ID --name "NewName" --priority urgent --state STATE_ID

omk plane work-item delete WORK_ITEM_ID  # Delete (requires confirmation)

omk plane work-item search --query "login"  # Search across workspace
```

Priority: `urgent`, `high`, `medium`, `low`, `none`

#### work-item comment

```bash
omk plane work-item comment list WORK_ITEM_ID
omk plane work-item comment get WORK_ITEM_ID COMMENT_ID
omk plane work-item comment create WORK_ITEM_ID --body "Great work!"
omk plane work-item comment update WORK_ITEM_ID COMMENT_ID --body "Updated comment"
omk plane work-item comment delete WORK_ITEM_ID COMMENT_ID
```

#### work-item link

```bash
omk plane work-item link list WORK_ITEM_ID
omk plane work-item link get WORK_ITEM_ID LINK_ID
omk plane work-item link create WORK_ITEM_ID --url "https://example.com/doc"
omk plane work-item link update WORK_ITEM_ID LINK_ID --url "https://example.com/newdoc"
omk plane work-item link delete WORK_ITEM_ID LINK_ID
```

Note: SDK does not support custom link titles; only URLs are stored.

#### work-item activity

Read-only activity log.

```bash
omk plane work-item activity list WORK_ITEM_ID
omk plane work-item activity get WORK_ITEM_ID ACTIVITY_ID
```

#### work-item attachment

```bash
omk plane work-item attachment list WORK_ITEM_ID
omk plane work-item attachment get WORK_ITEM_ID ATTACHMENT_ID
omk plane work-item attachment create WORK_ITEM_ID --name "screenshot.png" --size 102400 --mime-type image/png
omk plane work-item attachment delete WORK_ITEM_ID ATTACHMENT_ID
```

#### work-item relation

Relations between work items (plane.so only; not supported on self-hosted CE).

```bash
omk plane work-item relation list WORK_ITEM_ID
omk plane work-item relation create WORK_ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk plane work-item relation delete WORK_ITEM_ID --related-work-item ITEM_ID2
```

Relation types: `blocking`, `blocked_by`, `duplicate`, `relates_to`, `start_before`, `start_after`, `finish_before`, `finish_after`

#### work-item worklog

Time tracking (plane.so only; not supported on self-hosted CE).

```bash
omk plane work-item worklog list WORK_ITEM_ID
omk plane work-item worklog create WORK_ITEM_ID --duration 120 --description "Frontend refactor"
omk plane work-item worklog update WORK_ITEM_ID WORKLOG_ID --duration 90 --description "Updated"
omk plane work-item worklog delete WORK_ITEM_ID WORKLOG_ID
```

### cycle

```bash
omk plane cycle list                     # List cycles
omk plane cycle archived                 # List archived cycles
omk plane cycle get CYCLE_ID             # Get cycle details

omk plane cycle create --name "Sprint 1" \
  --start-date 2026-03-06 \
  --end-date 2026-03-20 \
  --description "First sprint"

omk plane cycle update CYCLE_ID --name "Sprint 1 (Extended)" --end-date 2026-03-27
omk plane cycle delete CYCLE_ID          # Delete (requires confirmation)
omk plane cycle archive CYCLE_ID         # Archive cycle
omk plane cycle unarchive CYCLE_ID       # Unarchive cycle

omk plane cycle items CYCLE_ID                               # List work items in cycle
omk plane cycle add-items CYCLE_ID --items ITEM_ID1 --items ITEM_ID2
omk plane cycle remove-item CYCLE_ID ITEM_ID
omk plane cycle transfer CYCLE_ID --target TARGET_CYCLE_ID   # Move all items to another cycle
```

### module

```bash
omk plane module list                    # List modules
omk plane module archived                # List archived modules
omk plane module get MODULE_ID           # Get module details

omk plane module create --name "Auth Module" \
  --description "Authentication system" \
  --status planned \
  --start-date 2026-03-06 \
  --target-date 2026-04-30

omk plane module update MODULE_ID --name "Auth & Security" --status in-progress
omk plane module delete MODULE_ID        # Delete (requires confirmation)
omk plane module archive MODULE_ID       # Archive module
omk plane module unarchive MODULE_ID     # Unarchive module

omk plane module items MODULE_ID                              # List work items in module
omk plane module add-items MODULE_ID --items ITEM_ID1 --items ITEM_ID2
omk plane module remove-item MODULE_ID ITEM_ID
```

Module status: `backlog`, `planned`, `in-progress`, `paused`, `completed`, `cancelled`

### milestone

```bash
omk plane milestone list                 # List milestones
omk plane milestone get MILESTONE_ID     # Get milestone details

omk plane milestone create --title "v1.0" --target-date 2026-06-30
omk plane milestone update MILESTONE_ID --title "v1.1" --target-date 2026-07-31
omk plane milestone delete MILESTONE_ID  # Delete (requires confirmation)

omk plane milestone items MILESTONE_ID   # List work items in milestone
omk plane milestone add-items MILESTONE_ID --items ITEM_ID1 --items ITEM_ID2
omk plane milestone remove-items MILESTONE_ID --items ITEM_ID1 --items ITEM_ID2
```

### intake

```bash
omk plane intake list                    # List intake items
omk plane intake get ISSUE_UUID          # Get intake details
omk plane intake create --name "Feature request" --description "HTML description" --priority high --source email
omk plane intake update ISSUE_UUID --status 1 --source web  # Status: -2=rejected, -1=snoozed, 0=pending, 1=accepted, 2=duplicate
omk plane intake delete ISSUE_UUID       # Delete
```

**CRITICAL:** Use the `issue` field UUID from `list` response, NOT the `id` field.

### page

Page/wiki management. Project pages require project context; workspace pages do not.

```bash
omk plane page get PAGE_ID               # Get project page
omk plane page get PAGE_ID --workspace   # Get workspace page

omk plane page create --name "API Docs" --description-html "<h1>Docs</h1>" --workspace
omk plane page create --name "Setup Guide" --description-html "<p>Guide</p>"  # Project page (requires -p PROJECT_ID)
```

---

## omk linear (or omk ln)

Requires `LINEAR_API_KEY`. Team-scoped commands fall back to `LINEAR_TEAM_ID` when `--team` is not provided.

### me

```bash
omk linear me                            # Current user info (id, name, email)
```

### team

```bash
omk linear team list                     # List all teams (id, name, key)
omk linear team get TEAM_ID             # Get team details (id, name, key, description)
```

### issue

```bash
omk linear issue list [--team TEAM_ID] [--first N]   # List issues (default first: 50)
omk linear issue get REF                              # Get issue by UUID or KEY-123 format

omk linear issue create \
  --title "Fix authentication bug" \
  --team TEAM_ID \
  --description "Markdown description" \
  --priority 2 \
  --state STATE_ID \
  --assignee USER_ID

omk linear issue update ISSUE_ID \
  --title "New title" \
  --priority 1 \
  --state STATE_ID \
  --assignee USER_ID

omk linear issue delete ISSUE_ID
```

Priority: `0`=none, `1`=urgent, `2`=high, `3`=medium, `4`=low

#### issue comment

```bash
omk linear issue comment list ISSUE_ID              # List comments (id, body, createdAt)
omk linear issue comment create ISSUE_ID --body "Comment text"
```

### state

```bash
omk linear state list [--team TEAM_ID]  # Team workflow states (id, name, type, position)
```

### label

```bash
omk linear label list [--team TEAM_ID]  # Team labels (id, name, color)
omk linear label get LABEL_ID           # Label details (id, name, color, parent)
```

### project

```bash
omk linear project list [--first N]     # All projects (id, name, state)
omk linear project get PROJECT_ID       # Project details (id, name, description, state, startDate, targetDate)
```

### cycle

```bash
omk linear cycle list [--team TEAM_ID]  # Team cycles (id, name, startsAt, endsAt)
omk linear cycle get CYCLE_ID           # Cycle details (id, name, startsAt, endsAt, completedAt)
```

---

## Common Workflows

### Plane: Create a work item and add to cycle

```bash
# 1. Create state first
STATE_ID=$(omk plane state create --name "In Progress" --color "#FF9800" -o json | jq -r '.id')

# 2. Create work item
ITEM=$(omk plane work-item create --name "Implement API" \
  --priority high --state "$STATE_ID" -o json)
ITEM_ID=$(echo "$ITEM" | jq -r '.id')

# 3. Create and add to cycle
CYCLE=$(omk plane cycle create --name "Sprint 1" \
  --start-date 2026-03-06 --end-date 2026-03-20 -o json)
CYCLE_ID=$(echo "$CYCLE" | jq -r '.id')

omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"
echo "Created work item $ITEM_ID in cycle $CYCLE_ID"
```

### Plane: Intake processing pipeline

```bash
# 1. List pending intakes
omk plane intake list -o json | jq '.results[] | select(.status==0)'

# 2. Accept or reject
INTAKE_ID=$(omk plane intake list -o json | jq -r '.results[0].issue')
omk plane intake update "$INTAKE_ID" --status 1  # Accept

# 3. Create work item from accepted intake
omk plane work-item create --name "From intake" --priority medium
```

### Plane: Assign work items to team members

```bash
# Get workspace members
MEMBER=$(omk plane workspace members -o json | jq -r '.results[0].id')

# Create work item with assignee
omk plane work-item create --name "Task" --assignee "$MEMBER"

# Or update existing
omk plane work-item update ITEM_ID --assignee "$MEMBER"
```

### Linear: Create issue and add comment

```bash
# 1. Get team and state
TEAM_ID=$(omk linear team list -o json | jq -r '.results[0].id')
STATE_ID=$(omk linear state list --team "$TEAM_ID" -o json | jq -r '.results[] | select(.name=="Todo") | .id')

# 2. Create issue
ISSUE_ID=$(omk linear issue create \
  --title "New feature request" \
  --team "$TEAM_ID" \
  --priority 3 \
  --state "$STATE_ID" \
  -o json | jq -r '.id')

# 3. Add comment
omk linear issue comment create "$ISSUE_ID" --body "Starting work on this."
```

---

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
| Linear (all)        | ✅       | N/A            |

## Error Handling

All commands exit with:
- **Exit code 0:** Success
- **Exit code 1:** Error (message printed to stderr)

Common errors:
- `"Given API token is not valid"` — Invalid or expired API key
- `"This feature is not currently supported on this server"` — Enterprise-only feature on Community Edition
- `"Workspace slug is required"` — Missing workspace (set `--workspace` or `PLANE_WORKSPACE_SLUG`)
- `"Project is required"` — Missing project (set `--project` or `PLANE_PROJECT_ID`)
- `"LINEAR_API_KEY is not set"` — Missing Linear API key

## Known Quirks and Limitations

1. **Intake get/update/delete:** Use the `issue` UUID from `list`, not the `id` field
2. **plane.so project names:** Avoid special characters (hyphens, underscores may be rejected)
3. **cycle/module add-items:** Use `--items` flag (multiple times for multiple items)
4. **Global flags position:** `-o`, `--profile`, `-w`, `-p` must come BEFORE provider subcommand (e.g., `omk -o json plane work-item list`)
5. **Confirmation prompts:** Delete and some update operations require interactive confirmation; pipe to `/dev/null` or use `-o json` does not suppress — run in non-interactive environments with caution
6. **Description formatting:** Plain text descriptions are auto-wrapped in `<p>` tags; use `--description-html` for custom HTML
7. **Links on work items:** SDK does not support custom titles; only URLs are stored
8. **Relations:** Only supported on plane.so; not available on Community Edition
9. **Worklog:** Only supported on plane.so and Enterprise Edition
10. **Page creation:** Workspace pages require `--workspace` flag; project pages require project context
11. **Linear team:** Most `linear` subcommands require `--team TEAM_ID` or `LINEAR_TEAM_ID` env var

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
