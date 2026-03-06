# oh-my-kanban

[한국어](README_kr.md) | [ENGLISH](README_en.md)

> Multi-platform project management CLI — built for AI agents first, humans second.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

## Why oh-my-kanban?

A project management CLI designed with AI agents as the primary user.

- **Zero-interaction mode** — Complete automation through environment variables alone
- **Machine-readable output** — JSON format for seamless agent pipeline integration
- **Full Plane CRUD** — Complete support for work items, cycles, modules, intake, pages, users, states, labels, and more
- **Linear support** — Issues, teams, cycles, projects, states, and labels via GraphQL
- **Multi-workspace support** — Profile-based management of multiple workspaces
- **Self-hosted friendly** — Developed against Plane Community Edition (free tier)

## Installation

### PyPI

```bash
pip install oh-my-kanban
```

### From Source

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e .
```

## Quick Start

### Step 1: Initialize Configuration (Interactive)

```bash
omk config init
```

You will be prompted to enter:

- **Server type**: plane.so cloud or self-hosted
- **API key**: [Generate API token](https://app.plane.so/profile/api-tokens/)
- **Workspace slug**: From URL or manual entry

### Step 2: Agent Mode (Environment Variable Automation)

For fully automated execution without human intervention:

```bash
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"  # required for project-scoped commands
export PLANE_BASE_URL="https://api.plane.so"  # or self-hosted URL

# All operations are now fully automated
omk plane work-item list -o json
omk plane cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk plane work-item create --name "Fix login bug" --state-id "..."
```

For Linear:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxx"
export LINEAR_TEAM_ID="your-team-id"  # optional default team

omk linear issue list -o json
omk linear issue create --title "Fix bug" --team TEAM_ID
```

### Step 3: Interactive Mode (Human User)

```bash
# Use default profile
omk config show
omk plane work-item list

# Use specific profile
omk --profile production plane work-item list -o table
```

## Configuration

### Configuration File Location

```text
~/.config/oh-my-kanban/config.toml
```

### Profile-Based Multi-Workspace Management

```toml
[default]
base_url = "https://api.plane.so"
api_key = "pl_xxxxx"
workspace_slug = "my-workspace"
output = "table"

[production]
base_url = "https://plane.example.com"
api_key = "pl_yyyyy"
workspace_slug = "prod-workspace"
output = "json"
```

Usage:

```bash
omk --profile production plane work-item list
```

### Environment Variable Priority

Command-line options > Environment variables > Configuration file > Defaults

```bash
# Override with environment variables
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk plane work-item list
```

### Configuration Management Commands

```bash
# Initialize configuration (interactive)
omk config init

# Display current configuration (API key is masked)
omk config show

# Modify specific values
omk config set workspace_slug my-new-workspace
omk config set output json

# List available profiles
omk config profile list

# Change default profile
omk config profile use production
```

## Command Reference

### Global Options

```bash
omk [OPTIONS] PROVIDER [PROVIDER_OPTIONS] COMMAND [ARGS]
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--workspace, -w SLUG` | `PLANE_WORKSPACE_SLUG` | Workspace slug |
| `--project, -p ID` | `PLANE_PROJECT_ID` | Project UUID |
| `--output, -o FORMAT` | - | Output format: `table` \| `json` \| `plain` (default: `table`) |
| `--profile PROFILE` | `PLANE_PROFILE` | Configuration profile (default: `default`) |
| `--version` | - | Display version |

### Provider Subgroups

omk separates commands by provider:
- `omk plane` (or `omk pl`) — Plane project management
- `omk linear` (or `omk ln`) — Linear project management
- `omk github` (or `omk gh`) — GitHub project management (coming soon)
- `omk config` — Configuration management (provider-independent)

### omk config — Configuration Management

```bash
omk config init                              # Interactive setup
omk config show [--profile PROFILE]          # Display current configuration
omk config set KEY VALUE [--profile PROFILE] # Modify configuration value
omk config profile list                      # List available profiles
omk config profile use NAME                  # Change default profile
```

### omk plane (or omk pl) — Plane Project Management

#### work-item — Work Item Management

```bash
# List work items
omk plane work-item list [--all] [--per-page N] [--cursor CURSOR] [--priority PRIORITY]

# Get work item details
omk plane work-item get ITEM_ID_OR_IDENTIFIER

# Create work item
omk plane work-item create --name NAME [--state STATE_ID] [--priority PRIORITY] [--description DESC] [--assignee USER_ID]

# Update work item
omk plane work-item update ITEM_ID [--name NAME] [--state STATE_ID] [--priority PRIORITY]

# Delete work item
omk plane work-item delete ITEM_ID [--force]

# Search work items
omk plane work-item search --query QUERY

# Manage work item relations
omk plane work-item relation list ITEM_ID
omk plane work-item relation create ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk plane work-item relation delete ITEM_ID --related-work-item ITEM_ID2

# Comments
omk plane work-item comment list ITEM_ID
omk plane work-item comment create ITEM_ID --body "Great work!"
omk plane work-item comment update ITEM_ID COMMENT_ID --body "Updated"
omk plane work-item comment delete ITEM_ID COMMENT_ID

# Links
omk plane work-item link list ITEM_ID
omk plane work-item link create ITEM_ID --url "https://example.com/doc"
omk plane work-item link delete ITEM_ID LINK_ID

# Activity (read-only)
omk plane work-item activity list ITEM_ID

# Worklog (plane.so only)
omk plane work-item worklog list ITEM_ID
omk plane work-item worklog create ITEM_ID --duration 120 --description "Frontend refactor"
omk plane work-item worklog update ITEM_ID WORKLOG_ID --duration 90
omk plane work-item worklog delete ITEM_ID WORKLOG_ID
```

#### cycle — Iteration Management

```bash
omk plane cycle list [--all]
omk plane cycle create --name NAME [--start-date DATE] [--end-date DATE]
omk plane cycle get CYCLE_ID
omk plane cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk plane cycle delete CYCLE_ID
omk plane cycle archive CYCLE_ID
omk plane cycle unarchive CYCLE_ID
omk plane cycle archived                  # List archived cycles
omk plane cycle items CYCLE_ID            # List work items in cycle
omk plane cycle add-items CYCLE_ID --items ITEM1 --items ITEM2
omk plane cycle remove-item CYCLE_ID ITEM_ID
omk plane cycle transfer CYCLE_ID --target TARGET_CYCLE_ID
```

#### module — Module Management

```bash
omk plane module list [--all]
omk plane module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk plane module get MODULE_ID
omk plane module update MODULE_ID [--name NAME] [--status STATUS]
omk plane module delete MODULE_ID
omk plane module archive MODULE_ID
omk plane module unarchive MODULE_ID
omk plane module items MODULE_ID          # List work items in module
omk plane module add-items MODULE_ID --items ITEM1 --items ITEM2
omk plane module remove-item MODULE_ID ITEM_ID
```

#### Other Plane Commands

```bash
omk plane user me                                  # Current user info
omk plane project list [--all]                     # List projects
omk plane state list                               # List states
omk plane label list [--all]                       # List labels
omk plane label create --name NAME [--color HEX]   # Create label

omk plane milestone list                           # List milestones
omk plane epic list                                # List epics
omk plane page list                                # List pages
omk plane intake list                              # List intake requests

omk plane workspace members                        # List workspace members
omk plane workspace features                       # List workspace features
omk plane teamspace list                           # List teamspaces
omk plane initiative list                          # List initiatives

omk plane work-item-type list                      # List work item types
omk plane work-item-property list --type TYPE_ID   # List custom properties
```

### omk linear (or omk ln) — Linear Project Management

Set `LINEAR_API_KEY` and optionally `LINEAR_TEAM_ID` before using Linear commands.

#### me — Current User

```bash
omk linear me                             # Get current user info (id, name, email)
```

#### team — Team Management

```bash
omk linear team list                      # List all teams
omk linear team get TEAM_ID              # Get team details
```

#### issue — Issue Management

```bash
omk linear issue list [--team TEAM_ID] [--first N]
omk linear issue get ISSUE_ID_OR_KEY     # UUID or KEY-123 format
omk linear issue create --title TITLE --team TEAM_ID [--description DESC] [--priority 0-4] [--state STATE_ID] [--assignee USER_ID]
omk linear issue update ISSUE_ID [--title TITLE] [--priority 0-4] [--state STATE_ID] [--assignee USER_ID] [--description DESC]
omk linear issue delete ISSUE_ID

# Comments
omk linear issue comment list ISSUE_ID
omk linear issue comment create ISSUE_ID --body "Comment text"
```

Priority: `0`=none, `1`=urgent, `2`=high, `3`=medium, `4`=low

#### state — Workflow States

```bash
omk linear state list [--team TEAM_ID]   # List team workflow states
```

#### label — Labels

```bash
omk linear label list [--team TEAM_ID]   # List team labels
omk linear label get LABEL_ID            # Get label details
```

#### project — Projects

```bash
omk linear project list [--first N]      # List all projects
omk linear project get PROJECT_ID        # Get project details
```

#### cycle — Cycles

```bash
omk linear cycle list [--team TEAM_ID]   # List team cycles
omk linear cycle get CYCLE_ID            # Get cycle details
```

### omk github (or omk gh) — GitHub Project Management (coming soon)

```bash
omk github issue list --owner OWNER --repo REPO
omk github project list --owner OWNER
```

**Coming soon.**

## Output Formats

### Table (Default)

```bash
omk plane work-item list
```

Output:

```text
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  Fix login bug  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  Add dark mode  medium    To Do      bob, charlie
```

### JSON (For Agent Automation)

```bash
omk plane work-item list -o json
```

Output:

```json
{
  "data": [
    {
      "id": "12345678-90ab-cdef-1234-567890abcdef",
      "name": "Fix login bug",
      "priority": "high",
      "state": "In Progress",
      "assignees": ["alice"],
      "state_id": "state_uuid_1",
      "project_id": "proj_uuid_1"
    }
  ],
  "pagination": {
    "cursor": "next_cursor_token",
    "has_more": true
  }
}
```

### Plain (For Script Parsing)

```bash
omk plane work-item list -o plain
```

Output:

```text
12345678-90ab-cdef-1234-567890abcdef|Fix login bug|high|In Progress|alice
87654321-abcd-ef12-3456-7890abcdef12|Add dark mode|medium|To Do|bob,charlie
```

## Server Compatibility

| Feature | plane.so | Self-hosted CE | Notes |
|---------|----------|----------------|-------|
| Work Items | ✅ | ✅ | - |
| Cycles | ✅ | ✅ | - |
| Modules | ✅ | ✅ | - |
| Milestones | ✅ | ✅ | - |
| Pages | ✅ | ✅ | - |
| Intake | ✅ | ✅ | - |
| Custom Properties | ✅ | ⚠️ | Limited in CE |
| Epics | ✅ | ⚠️ | Limited in CE |
| Initiatives | ✅ | ✅ | - |
| Worklog | ✅ | ❌ | Enterprise only |
| Relations | ✅ | ❌ | Enterprise only |

**Note**: Currently developed against Plane Community Edition (self-hosted, free tier). Enterprise-only features are not yet implemented.

## Examples

### Agent Pipeline: Create Cycle → Create Work Items → Assign

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. Create a new cycle
CYCLE_ID=$(omk plane cycle create \
  --name "Sprint 1" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "Created cycle: $CYCLE_ID"

# 2. Create a work item
ITEM_ID=$(omk plane work-item create \
  --name "Fix critical bug" \
  --priority high \
  --state "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "Created work item: $ITEM_ID"

# 3. Add work item to cycle
omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"

# 4. Assign to user
omk plane work-item update "$ITEM_ID" --assignee "$ASSIGNEE_USER_ID"

echo "Done!"
```

### Linear Issue Pipeline

```bash
#!/bin/bash

export LINEAR_API_KEY="lin_api_xxxxxx"

# 1. Get team ID
TEAM_ID=$(omk linear team list -o json | jq -r '.results[0].id')

# 2. Get state ID
STATE_ID=$(omk linear state list --team "$TEAM_ID" -o json | jq -r '.results[] | select(.name=="In Progress") | .id')

# 3. Create issue
ISSUE_ID=$(omk linear issue create \
  --title "Fix authentication bug" \
  --team "$TEAM_ID" \
  --priority 2 \
  --state "$STATE_ID" \
  -o json | jq -r '.id')

echo "Created issue: $ISSUE_ID"
```

### Multi-Workspace Management

```bash
# Query work items in production environment
omk --profile production plane work-item list

# Create work item in development environment
omk --profile development plane work-item create --name "New feature" --priority medium

# Filter by environment
omk --profile staging plane work-item search "bug" -o json | jq '.data[] | select(.priority=="urgent")'
```

### Generate Project Status Report

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

# Export data as JSON
omk plane work-item list --all -o json > report.json

# Aggregate by state
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# Top 5 work items by priority
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

## Roadmap

- [x] **Plane** (plane.so, self-hosted)
  - Note: Developed against **Community Edition (self-hosted, free tier)**. Enterprise-only features are not implemented.
  - Provider subgroup: `omk plane` (or `omk pl`)
- [x] **Linear**
  - Provider subgroup: `omk linear` (or `omk ln`)
  - Supported: issues, teams, cycles, projects, states, labels, comments
- [ ] **GitHub**
  - Provider subgroup: `omk github` (or `omk gh`)
- [ ] **Notion**
- [ ] **Jira**

## Contributing

### Environment Setup

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

### Code Style

- Python 3.10+
- Ruff lint rules: E, F, I, UP, B
- Line length: 100

### Testing

```bash
pytest tests/
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit changes: `git commit -am 'feat: add your feature'`
4. Push to branch: `git push origin feat/your-feature`
5. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) for details

## Support

- **Issues**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **Documentation**: [GitHub Wiki](https://github.com/ej31/oh-my-kanban/wiki)
- **API Reference**: [Plane API Docs](https://docs.plane.so/api-reference)
