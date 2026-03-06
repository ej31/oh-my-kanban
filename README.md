# oh-my-kanban

| [한국어](docs/README_kr.md) | [ENGLISH](docs/README_en.md) |
|---|---|

> Multi-platform project management CLI — built for AI agents first, humans second.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

## Why oh-my-kanban?

oh-my-kanban is a lightweight CLI designed for **AI agent automation workflows**.

- **Zero-interaction mode** — Full automation via environment variables
- **Machine-readable output** — JSON format for agent pipeline integration
- **Full Plane CRUD** — Complete support for work items, cycles, modules, intake, pages, users, states, labels, and more
- **Multi-workspace support** — Profile-based management of multiple environments
- **Self-hosted friendly** — Built and tested on Plane Community Edition (free, self-hosted)

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

Provide the following information:

- **Server type**: plane.so cloud or self-hosted
- **API key**: [Generate API token](https://app.plane.so/profile/api-tokens/)
- **Workspace slug**: Extract from URL or enter directly

### Step 2: Agent Mode (Environment Variable Automation)

For unattended automation with AI agents:

```bash
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"  # required for project-scoped commands
export PLANE_BASE_URL="https://api.plane.so"  # or self-hosted URL

# Full automation via environment variables
omk plane work-item list -o json
omk plane cycle create --name "Sprint 1" --start-date "2024-03-06" --end-date "2024-03-20"
omk plane work-item create --name "Fix login bug" --state-id "..."
```

### Step 3: Interactive Mode (Human Usage)

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
# Override via environment variable
PLANE_API_KEY="pl_xxxxxx" omk config show
PLANE_WORKSPACE_SLUG="override-ws" omk plane work-item list
```

### Configuration Management Commands

```bash
# Initialize configuration (interactive)
omk config init

# Display current configuration (API key masked)
omk config show

# Set specific value
omk config set workspace_slug my-new-workspace
omk config set output json

# List profiles
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
|--------|----------------------|-------------|
| `--workspace, -w SLUG` | `PLANE_WORKSPACE_SLUG` | Workspace slug |
| `--project, -p ID` | `PLANE_PROJECT_ID` | Project UUID |
| `--output, -o FORMAT` | - | Output format: `table` \| `json` \| `plain` (default: `table`) |
| `--profile PROFILE` | `PLANE_PROFILE` | Configuration profile (default: `default`) |
| `--version` | - | Show version |

### Provider Subgroups

omk separates commands by provider:
- `omk plane` (or `omk pl`) — Plane project management
- `omk github` (or `omk gh`) — GitHub project management (coming soon)
- `omk config` — Configuration management (provider-independent)

### Command Reference

#### omk config — Configuration Management (provider-independent)

```bash
omk config init                              # Initialize configuration (interactive)
omk config show [--profile PROFILE]          # Display current configuration
omk config set KEY VALUE [--profile PROFILE] # Change setting value
omk config profile list                      # List profiles
omk config profile use NAME                  # Change default profile
```

#### omk plane (or omk pl) — Plane Project Management

##### work-item — Work Items

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
omk plane work-item search QUERY

# Manage relationships
omk plane work-item relation create ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk plane work-item relation list ITEM_ID
omk plane work-item relation delete ITEM_ID --related-work-item ITEM_ID2
```

##### cycle — Cycles/Sprints

```bash
omk plane cycle list [--all]
omk plane cycle create --name NAME --owned-by USER_ID [--start-date DATE] [--end-date DATE]
omk plane cycle get CYCLE_ID
omk plane cycle update CYCLE_ID [--name NAME] [--start-date DATE] [--end-date DATE]
omk plane cycle delete CYCLE_ID
omk plane cycle items CYCLE_ID
omk plane cycle add-items CYCLE_ID --items ITEM1 --items ITEM2
omk plane cycle remove-item CYCLE_ID ITEM_ID
```

##### module — Modules

```bash
omk plane module list [--all]
omk plane module create --name NAME [--status STATUS] [--start-date DATE] [--target-date DATE]
omk plane module get MODULE_ID
omk plane module update MODULE_ID [--name NAME] [--status STATUS]
omk plane module delete MODULE_ID
omk plane module items MODULE_ID
omk plane module add-items MODULE_ID --items ITEM1 --items ITEM2
```

##### Other Commands

```bash
omk plane user me                               # Get current user info
omk plane project list [--all]                   # List projects
omk plane state list                             # List states
omk plane label list [--all]                     # List labels
omk plane label create --name NAME [--color HEX] # Create label

omk plane milestone list                         # List milestones
omk plane epic list                              # List epics
omk plane page list                              # List pages
omk plane intake list                            # List intake requests

omk plane workspace members                      # List workspace members
omk plane workspace features                     # List workspace features
omk plane teamspace list                         # List teamspaces
omk plane initiative list                        # List initiatives

omk plane work-item-type list                    # List work item types
omk plane work-item-property list --type TYPE_ID # List custom properties
```

#### omk github (or omk gh) — GitHub Project Management (coming soon)

```bash
omk github issue list --owner OWNER --repo REPO
omk github project list --owner OWNER
```

**Coming soon.**

## Output Formats / 출력 형식

### Table (Default)

```bash
omk plane work-item list
```

```text
ID                                    NAME           PRIORITY  STATE      ASSIGNEES
12345678-90ab-cdef-1234-567890abcdef  Fix login bug  high      In Progress  alice
87654321-abcd-ef12-3456-7890abcdef12  Add dark mode  medium    To Do      bob, charlie
```

### JSON (Agent Automation)

```bash
omk plane work-item list -o json
```

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

### Plain (Script Parsing)

```bash
omk plane work-item list -o plain
```

```text
12345678-90ab-cdef-1234-567890abcdef|Fix login bug|high|In Progress|alice
87654321-abcd-ef12-3456-7890abcdef12|Add dark mode|medium|To Do|bob,charlie
```

## Server Compatibility

| Feature | plane.so | Self-hosted CE | Note |
|---------|----------|----------------|------|
| Work Items | ✅ | ✅ | - |
| Cycles | ✅ | ✅ | - |
| Modules | ✅ | ✅ | - |
| Milestones | ✅ | ✅ | - |
| Pages | ✅ | ✅ | - |
| Intake | ✅ | ✅ | - |
| Custom Properties | ✅ | ⚠️ | Limited on CE |
| Epics | ✅ | ⚠️ | Limited on CE |
| Initiatives | ✅ | ✅ | - |

**Note**: Development is based on Plane Community Edition (self-hosted, free tier).
Enterprise-only features are not implemented.

## Examples

### Example 1: Agent Pipeline — Create Cycle → Create Work Item → Assign

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. Create cycle
CYCLE_ID=$(omk plane cycle create \
  --name "Sprint 1" \
  --owned-by "$USER_ID" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" \
  -o json | jq -r '.data.id')

echo "Created cycle: $CYCLE_ID"

# 2. Create work item
ITEM_ID=$(omk plane work-item create \
  --name "Fix critical bug" \
  --priority high \
  --state-id "$STATE_ID" \
  -o json | jq -r '.data.id')

echo "Created work item: $ITEM_ID"

# 3. Add work item to cycle
omk plane cycle add-work-items "$CYCLE_ID" "$ITEM_ID"

# 4. Assign to user
omk plane work-item update "$ITEM_ID" --assignees "$ASSIGNEE_USER_ID"

echo "Done!"
```

### Example 2: Multi-Workspace Management

```bash
# Fetch work items from production
omk --profile production plane work-item list

# Create work item in development
omk --profile development plane work-item create --name "New feature" --priority medium

# Filter by environment
omk --profile staging plane work-item search "bug" -o json | jq '.data[] | select(.priority=="urgent")'
```

### Example 3: Generate Project Status Report

```bash
#!/bin/bash

export PLANE_WORKSPACE_SLUG="my-workspace"

# Generate report in JSON format
omk plane work-item list --all -o json > report.json

# Group by status and count
jq '[.data[] | .state] | group_by(.) | map({state: .[0], count: length})' report.json

# Get top 5 work items by priority
jq '.data | sort_by(.priority) | reverse | .[0:5]' report.json
```

## Roadmap

- [x] **Plane** (plane.so, self-hosted)
  - Note: Developed against **Community Edition (self-hosted, free tier)**. Enterprise-only features are not implemented.
  - Provider subgroup: `omk plane` (or `omk pl`)
  - Examples: `omk plane work-item list`, `omk plane cycle create --name "Sprint 1"`, `omk pl work-item search "bug"`
- [ ] **GitHub**
  - Provider subgroup: `omk github` (or `omk gh`)
  - Examples: `omk github issue list --owner ej31 --repo my-repo`, `omk github project list --owner ej31`
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
