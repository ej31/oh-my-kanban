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
- **Broad Plane coverage** — Work items, cycles, modules, milestones, intake, pages, initiatives, teamspaces, stickies, and more (Community Edition free tier priority)
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
- `omk linear` (or `omk ln`) — Linear project management
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
omk plane work-item search --query QUERY

# Manage relationships
omk plane work-item relation create ITEM_ID --related-work-item ITEM_ID2 --relation-type blocking
omk plane work-item relation list ITEM_ID
omk plane work-item relation delete ITEM_ID --related-work-item ITEM_ID2
```

##### cycle — Cycles/Sprints

```bash
omk plane cycle list [--all]
omk plane cycle create --name NAME [--start-date DATE] [--end-date DATE]
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
omk plane epic list                              # List epics (list/get only)
omk plane page get PAGE_ID                       # Get page (get/create only)
omk plane intake list                            # List intake requests

omk plane workspace members                      # List workspace members
omk plane workspace features                     # List workspace features
omk plane teamspace list                         # List teamspaces
omk plane initiative list                        # List initiatives
omk plane sticky list                            # List stickies
omk plane customer list                          # List customers (Enterprise)

omk plane work-item-type list                    # List work item types
omk plane work-item-property list --type TYPE_ID # List custom properties
```

#### omk linear (or omk ln) — Linear Project Management

Set `LINEAR_API_KEY` before use. Optionally set `LINEAR_TEAM_ID` as a default team.

```bash
omk linear me                                          # Current user info
omk linear team list                                   # List teams
omk linear team get TEAM_ID

omk linear issue list [--team TEAM_ID] [--first N]
omk linear issue get ISSUE_ID_OR_KEY                   # UUID or KEY-123 format
omk linear issue create --title TITLE --team TEAM_ID [--priority 0-4] [--state STATE_ID]
omk linear issue update ISSUE_ID [--title TITLE] [--priority 0-4] [--state STATE_ID] [--assignee USER_ID] [--description DESC]
omk linear issue delete ISSUE_ID

omk linear issue comment list ISSUE_ID
omk linear issue comment create ISSUE_ID --body "Comment text"

omk linear state list [--team TEAM_ID]                 # Workflow states
omk linear label list [--team TEAM_ID]                 # Labels
omk linear label get LABEL_ID

omk linear project list [--first N]                    # Projects
omk linear project get PROJECT_ID

omk linear cycle list [--team TEAM_ID]                 # Cycles
omk linear cycle get CYCLE_ID
```

Priority: `0`=none, `1`=urgent, `2`=high, `3`=medium, `4`=low

#### omk github (or omk gh) — GitHub Project Management

GitHub integration uses the [`gh` CLI](https://cli.github.com/) under the hood.
Run `npx oh-my-kanban` to get guided through installing and authenticating `gh`.

```bash
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Linux (Debian/Ubuntu)
sudo apt install gh

# Authenticate after installation
gh auth login
```

Once `gh` is installed and authenticated, run `npx oh-my-kanban` again to complete setup.

> GitHub command support (`omk github issue list`, etc.) is coming soon.

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

> 개발 기준: **Plane Community Edition (무료 자가호스팅)**
> 무료 플랜에서 제공하는 기능을 우선 구현합니다. 유료/Enterprise 전용 기능은 구현 범위에 포함되지 않습니다.

### Plane

| 기능 | 구현 | plane.so | Self-hosted CE | 비고 |
|------|:----:|:--------:|:--------------:|------|
| Work Items (CRUD) | ✅ | ✅ | ✅ | 댓글·링크·관계·활동·첨부파일·작업로그 포함 |
| Cycles (CRUD) | ✅ | ✅ | ✅ | 아이템 추가·제거 포함 |
| Modules (CRUD) | ✅ | ✅ | ✅ | 아이템 추가 포함 |
| Milestones (CRUD) | ✅ | ✅ | ✅ | 아이템 추가·제거 포함 |
| Intake (CRUD) | ✅ | ✅ | ✅ | 상태 승인·거부 포함 |
| Initiatives (CRUD) | ✅ | ✅ | ✅ | 에픽·레이블·프로젝트 연결 포함 |
| Teamspaces (CRUD) | ✅ | ✅ | ✅ | 멤버·프로젝트 관리 포함 |
| Stickies (CRUD) | ✅ | ✅ | ✅ | - |
| Work Item Types (CRUD) | ✅ | ✅ | ✅ | - |
| Custom Properties (CRUD) | ✅ | ✅ | ✅ | 옵션·값 관리 포함 |
| Users / Members | ✅ | ✅ | ✅ | me, workspace members |
| Pages | ⚠️ | ✅ | ✅ | get·create만 구현 |
| Epics | ⚠️ | ✅ | ✅ | list·get만 구현 |
| States | ⚠️ | ✅ | ✅ | list만 구현 |
| Labels | ⚠️ | ✅ | ✅ | list·create만 구현 |
| Projects | ⚠️ | ✅ | ✅ | list만 구현 |
| Workspace Features | ⚠️ | ✅ | ✅ | list만 구현 (read-only) |
| Customers (CRUD) | ✅ | ✅ | ❌ | Enterprise 전용 (CE 미지원) |

#### 부분 구현 사유

| 기능 | 미구현 범위 | 사유 |
|------|------------|------|
| Pages | list·update·delete | Plane Python SDK가 해당 엔드포인트를 미지원 |
| Epics | create·update·delete | Epic은 Work Item Type의 특수 케이스. Plane API의 Epic CRUD가 CE에서 제한적으로 제공되어 조회만 지원 |
| States | create·update·delete | 프로젝트 설정 리소스로, 자동화 파이프라인에서 직접 생성·삭제 수요가 낮아 list 우선 구현 |
| Labels | get·update·delete | 자동화 파이프라인에서 레이블 수정·삭제 수요가 낮아 후순위 |
| Projects | create·update·delete | 관리자 작업으로 CLI 자동화 범위 밖으로 판단 |

### Linear

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Issues (CRUD) | ✅ | 댓글 포함 |
| Teams | ✅ | list·get |
| States | ✅ | list |
| Labels | ✅ | list·get |
| Projects | ✅ | list·get |
| Cycles | ✅ | list·get |
| Users | ✅ | me |

### GitHub

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Issues | ❌ | 향후 구현 예정 |
| Projects | ❌ | 향후 구현 예정 |

> GitHub 통합은 `gh` CLI 기반으로 구현 예정입니다. `npx oh-my-kanban`을 실행하면 `gh` 설치 및 인증을 안내합니다.

### Notion / Jira

| 기능 | 구현 | 비고 |
|------|:----:|------|
| Notion | ❌ | 미착수 |
| Jira | ❌ | 미착수 |

## Examples

### Example 1: Agent Pipeline — Create Cycle → Create Work Item → Assign

```bash
#!/bin/bash

export PLANE_API_KEY="pl_xxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="proj_uuid"

# 1. Create cycle (ownership is derived automatically from the authenticated user)
CYCLE_ID=$(omk plane cycle create \
  --name "Sprint 1" \
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
omk plane cycle add-items "$CYCLE_ID" --items "$ITEM_ID"

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
- [ ] **GitHub** (via [`gh` CLI](https://cli.github.com/))
  - Provider subgroup: `omk github` (or `omk gh`)
  - Run `npx oh-my-kanban` to get guided through `gh` installation and authentication
  - Examples: `omk github issue list --owner ej31 --repo my-repo`, `omk github project list --owner ej31`
- [x] **Linear**
  - Provider subgroup: `omk linear` (or `omk ln`)
  - Examples: `omk linear issue list`, `omk linear issue create --title "Bug" --team TEAM_ID`, `omk ln team list`
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
