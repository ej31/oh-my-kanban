# Installation

## For Humans

Paste this into your LLM agent session:

```text
Install and configure oh-my-kanban by following the instructions here:
https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

If you want to do it yourself, run the interactive installer:

```bash
npx @oh-my-kanban/setup
```

Local development path:

```bash
cd installer
npm install
npm run start
```

After installation, verify with:

```bash
omk --help
omk config show
```

## For LLM Agents

Important:

- Use this file as the installation runbook
- Do not infer setup from unrelated docs
- Do not skip required questions
- Do not assume Plane or Linear should be configured unless the user wants them

Fetch this file directly if needed:

```bash
curl -fsSL https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

If you are helping a user install oh-my-kanban, follow these steps exactly.

### Step 0: Ask the user for installation inputs

Before running the installer, ask the user these questions and record the answers.

1. What profile name should be created?
   - Default recommendation: `default`

2. What should the default output format be?
   - `table`
   - `json`
   - `plain`

3. Which providers should be configured now?
   - `plane`
   - `linear`
   - both

4. If `plane` is selected:
   - Are you using Plane cloud or self-hosted Plane?
   - If self-hosted: what is the Plane base URL?
   - What is the Plane API key?
   - What is the Plane workspace slug or workspace URL?
   - What is the default Plane project UUID, if any?

5. If `linear` is selected:
   - What is the Linear API key?
   - What is the default Linear team ID, if any?

6. Should package installation be skipped?
   - If yes, use config-only mode
   - If no, allow the installer to install the Python package

You should not proceed until these answers are known.

### Step 1: Check installer mode

Use the normal installer unless the user explicitly wants config-only behavior.

Normal install:

```bash
npx @oh-my-kanban/setup
```

Config-only:

```bash
npx @oh-my-kanban/setup --config-only
```

Legacy alias:

```bash
npx @oh-my-kanban/setup --skip-install
```

### Step 2: Understand what the installer will ask

The installer prompts in this order:

1. profile name
2. default output format
3. provider selection (`plane`, `linear`, or both)
4. provider-specific questions
5. Python environment check
6. package installation unless config-only mode is enabled
7. config file write

### Step 3: Plane-specific prompt contract

If Plane is selected, the installer will ask:

1. Are you using self-hosted Plane?
2. If yes, Plane base URL
3. Plane API key
4. Plane workspace slug or workspace URL
5. Optional default project UUID

Validation behavior:

- Plane API key is validated against `/api/v1/users/me/`
- Plane workspace is validated against `/api/v1/workspaces/{slug}/projects/`
- Invalid values cause the prompt to repeat

### Step 4: Linear-specific prompt contract

If Linear is selected, the installer will ask:

1. Linear API key
2. Optional default team ID

Validation behavior:

- Linear API key is validated with `{ viewer { id } }`
- If a team ID is provided, the installer validates it with:
  - `query Team($id: String!) { team(id: $id) { id } }`
- Invalid values cause the prompt to repeat

### Step 5: Runtime installation behavior

Unless config-only mode is active, the installer attempts Python package installation.

Installation lookup order:

1. `pip3`
2. `pip`
3. `python -m pip`
4. `uv pip`

If a PEP 668 externally managed environment blocks direct install:

5. `pipx` fallback

If the system lacks Python 3.10+, installation should stop and the user must fix Python first.

### Step 6: Config file that should be produced

Canonical config target:

```text
~/.config/oh-my-kanban/config.toml
```

Canonical format:

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
```

The installer should preserve other profiles and rewrite only the selected profile sections.

### Step 7: Post-install verification

Run these commands after setup:

```bash
omk --help
omk config --help
omk config show --profile PROFILE_NAME
```

If Plane was configured:

```bash
omk plane --help
omk plane --workspace WORKSPACE_SLUG --project PROJECT_UUID work-item list
```

If Linear was configured:

```bash
omk linear --help
omk linear me
omk linear state list --team TEAM_ID
```

### Step 8: Explain fallback rules to the user

You should explicitly tell the user:

- root CLI only has root options like `--output` and `--profile`
- Plane workspace/project context lives on `omk plane`
- Plane values can come from:
  - group options
  - environment variables
  - profile config
- Linear credentials can come from:
  - environment variables
  - profile config
- team-scoped Linear commands can resolve team from:
  - `--team`
  - `LINEAR_TEAM_ID`
  - config `linear.team_id`

### Step 9: Troubleshooting

If package install must be skipped:

```bash
npx @oh-my-kanban/setup --config-only
```

If the user already has the runtime package and only wants config:

- use config-only mode
- still collect and validate provider values
- still verify with `omk config show --profile ...`

If verification fails:

1. inspect `omk config show --profile PROFILE_NAME`
2. re-check API key
3. re-check workspace slug or team ID
4. re-run the installer if needed
