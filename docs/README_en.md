[한국어](README_kr.md) | [ENGLISH](README_en.md)

# oh-my-kanban

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
export PLANE_BASE_URL="https://api.plane.so"  # or self-hosted URL

# All operations are now fully automated
omk work-item list -o json
omk cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk work-item create --name "Fix login bug" --state-id "..." --project "..."
```

### Step 3: Interactive Mode (Human User)

```bash
# Use default profile
omk config show
omk work-item list

# Use specific profile
omk --profile production work-item list -o table
```

## Configuration

### Configuration File Location

```
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
omk --profile production work-item list
```

### Environment Variable Priority

Command-line options > Environment variables > Configuration file > Defaults

```bash
# Override with environment variables
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk work-item list
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
omk [OPTIONS] COMMAND [ARGS]
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--workspace, -w SLUG` | `PLANE_WORKSPACE_SLUG` | Workspace slug |
| `--project, -p ID` | `PLANE_PROJECT_ID` | Project UUID |
| `--output, -o FORMAT` | - | Output format: `table` \| `json` \| `plain` (default: `table`) |
| `--profile PROFILE` | `PLANE_PROFILE` | Configuration profile (default: `default`) |
| `--version` | - | Display version |

### Command Groups

#### config — Configuration Management

```bash
omk config init                              # Interactive setup
omk config show [--profile PROFILE]          # Display current configuration
omk config set KEY VALUE [--profile PROFILE] # Modify configuration value
omk config profile list                      # List available profiles
omk config profile use NAME                  # Change default profile
```

#### work-item — Work Item Management

```bash
# List work items
omk work-item list [--all] [--per-page N] [--cursor CURSOR] [--priority PRIORITY]

# Get work item details
omk work-item get ITEM_ID_OR_IDENTIFIER

# Create work item
omk work-item create --name NAME [--state-id STATE] [--priority PRIORITY] [--description DESC] [--assignees USER1,USER2]

# Update work item
omk work-item update ITEM_ID [--name NAME] [--state-id STATE] [--priority PRIORITY]

# Delete work item
omk work-item delete ITEM_ID [--force]

# Search work items
omk work-item search QUERY

# Manage work item relations
omk work-item relation create ITEM_ID --type TYPE --target TARGET_ITEM_ID
omk work-item relation list ITEM_ID
omk work-item relation delete ITEM_ID --target TARGET_ITEM_ID
```

#### cycle — Iteration Management

```bash
omk cycle list [--all]
omk cycle create --name NAME --owned-by USER_ID [--start-date DATE] [--end-date DATE]
omk cycle get CYCLE_ID
omk cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk cycle delete CYCLE_ID
omk cycle list-work-items CYCLE_ID
omk cycle add-work-items CYCLE_ID ITEM1 ITEM2 ...
omk cycle remove-work-item CYCLE_ID ITEM_ID
```

#### module — Module Management

```bash
omk module list [--all]
omk module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk module get MODULE_ID
omk module update MODULE_ID [--name NAME] [--status STATUS]
omk module delete MODULE_ID
omk module list-work-items MODULE_ID
omk module add-work-items MODULE_ID ITEM1 ITEM2 ...
```

#### Other Commands

```bash
omk user list                              # List workspace users
omk project list [--all]                   # List projects
omk state list                             # List work item states
omk label list [--all]                     # List labels
omk label create --name NAME [--color HEX] # Create label

omk milestone list                         # List milestones
omk epic list                              # List epics
omk page list                              # List pages
omk intake list                            # List intake items

omk workspace list                         # Display workspace information
omk teamspace list                         # List teamspaces
omk initiative list                        # List initiatives

omk work-item-type list                    # List work item types
omk work-item-property list --type TYPE_ID # List custom properties
```

## Output Formats

### Table (Default)

```bash
omk work-item list
```

Output:

```
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  Fix login bug  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  Add dark mode  medium    To Do      bob, charlie
```

### JSON (For Agent Automation)

```bash
omk work-item list -o json
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
omk work-item list -o plain
```

Output:

```
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

**Note**: Currently developed against Plane Community Edition (self-hosted, free tier). Enterprise-only features are not yet implemented.

## Examples

### Agent Pipeline: Create Cycle → Create Work Items → Assign

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. Create a new cycle
CYCLE_ID=$(omk cycle create \
  --name "Sprint 1" \
  --owned-by "$USER_ID" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "Created cycle: $CYCLE_ID"

# 2. Create a work item
ITEM_ID=$(omk work-item create \
  --name "Fix critical bug" \
  --priority high \
  --state-id "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "Created work item: $ITEM_ID"

# 3. Add work item to cycle
omk cycle add-work-items "$CYCLE_ID" "$ITEM_ID"

# 4. Assign to user
omk work-item update "$ITEM_ID" --assignees "$ASSIGNEE_USER_ID"

echo "Done!"
```

### Multi-Workspace Management

```bash
# Query work items in production environment
omk --profile production work-item list

# Create work item in development environment
omk --profile development work-item create --name "New feature" --priority medium

# Filter by environment
omk --profile staging work-item search "bug" -o json | jq '.data[] | select(.priority=="urgent")'
```

### Generate Project Status Report

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

# Export data as JSON
omk work-item list --all -o json > report.json

# Aggregate by state
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# Top 5 work items by priority
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

## Roadmap

- [x] **Plane** (plane.so, self-hosted)
  - Note: Developed against **Community Edition (self-hosted, free tier)**. Enterprise-only features are not implemented.
- [ ] **GitHub**
- [ ] **Linear**
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
