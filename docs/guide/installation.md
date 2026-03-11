# Installation

This is the setup runbook.

If you are an agent, stop improvising and follow this file.

## For Humans

Paste this into your LLM agent:

```text
Install and configure oh-my-kanban by following this guide:
https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

If you insist on doing it yourself:

```bash
npx @oh-my-kanban/setup
```

Local development:

```bash
cd installer
npm install
npm run start
```

Verify after setup:

```bash
omk --help
omk config show
```

## For LLM Agents

Rules:

- Use this file as the install procedure
- Ask for required inputs first
- Do not guess provider values
- Do not skip validation
- Do not continue if required answers are missing

Raw source:

```bash
curl -fsSL https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

## Step 0: Ask First

Collect these answers before you run anything:

1. Profile name
   - default: `default`

2. Default output format
   - `table`
   - `json`
   - `plain`

3. Which providers to configure
   - `plane`
   - `linear`
   - both

4. If `plane` is selected
   - cloud or self-hosted
   - if self-hosted: Plane base URL
   - Plane API key
   - Plane workspace slug or workspace URL
   - optional default Plane project UUID

5. If `linear` is selected
   - Linear API key
   - optional default Linear team ID

6. Should package installation be skipped
   - yes -> use config-only mode
   - no -> let installer install the Python package

Do not proceed until you have these answers.

## Step 1: Pick Installer Mode

Normal:

```bash
npx @oh-my-kanban/setup
```

Config only:

```bash
npx @oh-my-kanban/setup --config-only
```

Legacy alias:

```bash
npx @oh-my-kanban/setup --skip-install
```

## Step 2: Know The Prompt Order

The installer asks in this order:

1. profile name
2. output format
3. provider selection
4. provider-specific questions
5. Python check
6. package installation unless config-only mode is active
7. config file write

## Step 3: Plane Questions

If Plane is selected, the installer asks:

1. self-hosted or not
2. base URL if self-hosted
3. Plane API key
4. Plane workspace slug or workspace URL
5. optional default project UUID

Plane validation:

- API key -> `/api/v1/users/me/`
- workspace -> `/api/v1/workspaces/{slug}/projects/`
- invalid values -> prompt again

## Step 4: Linear Questions

If Linear is selected, the installer asks:

1. Linear API key
2. optional default team ID

Linear validation:

- API key -> `{ viewer { id } }`
- team ID -> `query Team($id: String!) { team(id: $id) { id } }`
- invalid values -> prompt again

## Step 5: Python Install Behavior

Unless config-only mode is active, the installer tries:

1. `pip3`
2. `pip`
3. `python -m pip`
4. `uv pip`
5. `pipx` fallback if PEP 668 blocks direct install

If Python 3.10+ is missing, stop and fix Python first.

## Step 6: Config File Output

Target file:

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

Preserve other profiles.
Rewrite only the selected profile sections.

## Step 7: Verify

Always run:

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

## Step 8: Explain The Rules

Tell the user this explicitly:

- root CLI has only root options like `--output` and `--profile`
- Plane workspace/project context lives on `omk plane`
- Plane values resolve from:
  - group options
  - environment variables
  - profile config
- Linear credentials resolve from:
  - environment variables
  - profile config
- team-scoped Linear commands resolve from:
  - `--team`
  - `LINEAR_TEAM_ID`
  - config `linear.team_id`

## Step 9: If It Breaks

If you only need config:

```bash
npx @oh-my-kanban/setup --config-only
```

If verification fails:

1. inspect `omk config show --profile PROFILE_NAME`
2. re-check API key
3. re-check workspace slug or team ID
4. rerun the installer
