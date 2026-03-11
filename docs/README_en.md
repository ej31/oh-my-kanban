# oh-my-kanban

[한국어](README_kr.md) | [ENGLISH](README_en.md)

> Automation-friendly CLI for Plane and Linear.

[![PyPI version](https://badge.fury.io/py/oh-my-kanban.svg)](https://pypi.org/project/oh-my-kanban/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-ej31%2Foh--my--kanban-black)](https://github.com/ej31/oh-my-kanban)

## Overview

oh-my-kanban is a Python CLI for working with Plane and Linear from scripts, agent workflows, and everyday terminal usage.

- One command surface for both providers: `omk plane ...` and `omk linear ...`
- Automation-friendly output modes: `table`, `json`, `plain`
- Plane profiles plus environment variable overrides for both providers
- Self-hosted Plane support
- Current repository scope is intentionally limited to Plane and Linear

## Supported Providers

- **Plane**
  - Work items, cycles, modules, milestones, epics, pages, intake
  - Projects, states, labels, teamspaces, customers, workspace and user helpers
  - Additional groups: `agent-run`, `sticky`, `work-item-type`, `work-item-property`
- **Linear**
  - Viewer lookup, teams, issues, issue comments
  - States, labels, projects, cycles

## Architecture

- Runtime stays unified under `omk`
- Provider-specific implementation lives under `src/oh_my_kanban/providers/<name>/`
- Provider-local modules are the only canonical implementation paths
- New provider-specific code should be added under `providers/<name>/`

## Agent Workflow

When an AI agent needs to operate the CLI safely, the recommended discovery order is:

1. `omk config --help`
2. `omk config show --profile PROFILE`
3. `omk plane --help` or `omk linear --help`
4. the target subcommand `--help`

Important hidden-context rules are:

- Plane workspace/project context lives on `omk plane`, not on the root CLI
- Plane values can come from group options, environment variables, or config
- Linear credentials come from environment variables or config
- Team-scoped Linear commands can fall back from `--team` to `LINEAR_TEAM_ID` to config

## Installation

### PyPI

```bash
pip install oh-my-kanban
```

### From Source

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

### Interactive Setup Wizard

```bash
npx @oh-my-kanban/setup

# local development
cd installer
npm install
npm run start
```

## Quick Start

### 1. Configure Plane

`config init` is provider-aware interactive setup. It can configure Plane, Linear, or both in one profile.

```bash
omk config init
omk config set plane.project_id YOUR_PROJECT_UUID
```

If you prefer non-interactive setup:

```bash
export PLANE_BASE_URL="https://api.plane.so"
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"
```

### 2. Configure Linear

You can persist Linear settings in the config file:

```bash
omk config set linear.api_key lin_api_xxxxxxxxxx
omk config set linear.team_id your-linear-team-id
```

Or provide them via environment variables:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxx"
export LINEAR_TEAM_ID="your-linear-team-id"
```

### 3. Try the CLI

```bash
omk config show
omk plane work-item list
omk linear me
omk linear issue list --team YOUR_LINEAR_TEAM_ID
```

## Configuration

### Config File

```text
~/.config/oh-my-kanban/config.toml
```

### Example

```toml
[default]
output = "table"

[default.plane]
base_url = "https://api.plane.so"
api_key = "pl_xxxxx"
workspace_slug = "my-workspace"
project_id = "plane-project-uuid"

[default.linear]
api_key = "lin_api_xxxxx"
team_id = "team-id"

[production]
output = "json"

[production.plane]
base_url = "https://plane.example.com"
api_key = "pl_yyyyy"
workspace_slug = "prod-workspace"
project_id = "prod-project-uuid"

[production.linear]
api_key = "lin_api_prod"
team_id = "prod-team-id"
```

### Precedence

Command-line options > environment variables > config file > defaults

### Environment Variables

| Variable | Purpose |
|---|---|
| `PLANE_BASE_URL` | Plane API base URL |
| `PLANE_API_KEY` | Plane API key |
| `PLANE_WORKSPACE_SLUG` | Plane workspace slug |
| `PLANE_PROJECT_ID` | Default Plane project UUID |
| `LINEAR_API_KEY` | Linear API key |
| `LINEAR_TEAM_ID` | Default Linear team ID |
| `PLANE_PROFILE` | Active config profile |

### Config Commands

```bash
omk config init
omk config show [--profile PROFILE]
omk config set plane.base_url VALUE
omk config set plane.api_key VALUE
omk config set plane.workspace_slug VALUE
omk config set plane.project_id VALUE
omk config set output VALUE
omk config set linear.api_key VALUE
omk config set linear.team_id VALUE
omk config migrate [--profile PROFILE]
omk config migrate --all-profiles
omk config profile list
omk config profile use NAME
```

## Command Overview

### Global Form

```bash
omk [OPTIONS] COMMAND [ARGS]...
```

| Option | Environment Variable | Description |
|---|---|---|
| `--output`, `-o` | - | Output format: `table`, `json`, `plain` |
| `--profile` | `PLANE_PROFILE` | Config profile |
| `--version` | - | Show version |

### Top-Level Commands

- `omk config` - provider-independent configuration
- `omk plane` / `omk pl` - Plane commands
- `omk linear` / `omk ln` - Linear commands

Plane-specific context options live on the provider group:

```bash
omk plane --workspace MY_WORKSPACE --project PROJECT_UUID work-item list
```

### Plane Commands

Use `omk plane --help` for the full list. Common entry points:

```bash
omk plane user me
omk plane project list [--all]
omk plane state list
omk plane label list [--all]

omk plane work-item list [--all] [--per-page N] [--priority PRIORITY]
omk plane work-item get ITEM_ID_OR_IDENTIFIER
omk plane work-item create --name NAME [--state STATE_ID] [--priority PRIORITY]
omk plane work-item update ITEM_ID [--name NAME] [--state STATE_ID]

omk plane cycle list [--all]
omk plane cycle create --name NAME [--start-date DATE] [--end-date DATE]
omk plane cycle add-items CYCLE_ID --items ITEM1 --items ITEM2

omk plane module list [--all]
omk plane milestone list
omk plane epic list
omk plane page list
omk plane intake list
omk plane workspace members
omk plane teamspace list
omk plane customer list
omk plane sticky list
omk plane agent-run list
```

### Linear Commands

Use `omk linear --help` for the full list. Common entry points:

```bash
omk linear me
omk linear team list
omk linear team get TEAM_ID

omk linear issue list [--team TEAM_ID] [--first N]
omk linear issue get ISSUE_ID_OR_KEY
omk linear issue create --title TITLE --team TEAM_ID [--priority 0-4] [--state STATE_ID]
omk linear issue update ISSUE_ID [--title TITLE] [--priority 0-4] [--state STATE_ID]
omk linear issue delete ISSUE_ID

omk linear issue comment list ISSUE_ID
omk linear issue comment create ISSUE_ID --body "Comment text"

omk linear state list [--team TEAM_ID]
omk linear label list [--team TEAM_ID]
omk linear project list [--first N]
omk linear cycle list [--team TEAM_ID]
```

## Output Formats

`--output` is a global option, so place it before the provider command.

```bash
omk -o table plane work-item list
omk -o json plane work-item list
omk -o plain linear issue list --team TEAM_ID
```

## Examples

### Plane Workflow

```bash
export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

CYCLE_ID=$(omk -o json plane cycle create \
  --name "Sprint 1" \
  --start-date "2024-03-06" \
  --end-date "2024-03-20" | jq -r '.data.id')

STATE_ID="state_uuid"

ITEM_ID=$(omk -o json plane work-item create \
  --name "Fix critical bug" \
  --priority high \
  --state "$STATE_ID" | jq -r '.data.id')

omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"
omk plane work-item update "$ITEM_ID" --assignee "user_uuid"
```

### Linear Workflow

```bash
export LINEAR_API_KEY="lin_api_xxxxxx"
export LINEAR_TEAM_ID="team_uuid"

omk linear team list
omk -o json linear issue list --team "$LINEAR_TEAM_ID"

omk linear issue create \
  --title "Fix login bug" \
  --team "$LINEAR_TEAM_ID" \
  --priority 2

omk linear issue comment create ISSUE_ID --body "Started investigation."
```

## Provider Notes

### Plane

- Developed against Plane Community Edition and plane.so cloud
- Self-hosted deployments are supported through `PLANE_BASE_URL`
- Some Plane enterprise-only surfaces may be limited depending on your server

### Linear

- Uses Linear's GraphQL API via `httpx`
- `LINEAR_API_KEY` is required
- `LINEAR_TEAM_ID` is optional but useful as a default team

## Development

```bash
uv run pytest
uv run python -m oh_my_kanban --help
```

## Support

- **Issues**: [GitHub Issues](https://github.com/ej31/oh-my-kanban/issues)
- **Plane API Docs**: [docs.plane.so/api-reference](https://docs.plane.so/api-reference)
- **Linear API Docs**: [developers.linear.app](https://developers.linear.app/)

## License

MIT License - See [../LICENSE](../LICENSE) for details.
