# oh-my-kanban Installation Guide

This is the canonical installation and setup guide for both humans and AI agents.

If you are an agent, follow this file instead of guessing from scattered docs.

## What You Are Installing

- Runtime CLI: `omk`
- Supported providers: `plane`, `linear`
- Interactive installer: `@oh-my-kanban/setup`
- Config file: `~/.config/oh-my-kanban/config.toml`

## Fastest Path

Recommended:

```bash
npx @oh-my-kanban/setup
```

Local development path:

```bash
cd installer
npm install
npm run start
```

The installer will:

1. ask for a profile name
2. ask which providers to configure
3. collect provider-specific values
4. install the Python package unless config-only mode is used
5. write canonical namespaced TOML config

## Installer Flags

- `--config-only`
  - write config only
  - skip Python package installation
- `--skip-install`
  - legacy alias for `--config-only`
- `OMK_INSTALL_PACKAGE=<package>`
  - override the Python package name
  - intended for local testing, not normal usage

## Manual Runtime Installation

PyPI:

```bash
pip install oh-my-kanban
```

From source:

```bash
git clone https://github.com/ej31/oh-my-kanban.git
cd oh-my-kanban
pip install -e ".[dev]"
```

## Post-Install Verification

Run these in order:

```bash
omk --help
omk config --help
omk config show
omk plane --help
omk linear --help
```

If you used a non-default profile:

```bash
omk config show --profile YOUR_PROFILE
```

## Configuration Model

Canonical config format:

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

`omk config migrate` rewrites older flat config into this namespaced format.

## Environment Variables

Plane:

```bash
export PLANE_BASE_URL="https://api.plane.so"
export PLANE_API_KEY="pl_xxxxxxxxxx"
export PLANE_WORKSPACE_SLUG="my-workspace"
export PLANE_PROJECT_ID="your-project-id"
```

Linear:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxx"
export LINEAR_TEAM_ID="your-linear-team-id"
```

Profile:

```bash
export PLANE_PROFILE="default"
```

## CLI Discovery Order For Agents

Read commands in this order:

1. `omk config --help`
2. `omk config show --profile PROFILE`
3. `omk plane --help` or `omk linear --help`
4. target leaf command `--help`

Important rules:

- Root CLI has only root options such as `--output` and `--profile`
- Plane context options live on `omk plane`
- Plane values can come from:
  - group options
  - environment variables
  - selected profile config
- Linear credentials come from:
  - environment variables
  - selected profile config
- Team-scoped Linear commands can resolve team from:
  - `--team`
  - `LINEAR_TEAM_ID`
  - config `linear.team_id`

## Canonical Commands

### Config

```bash
omk config init
omk config show [--profile PROFILE]
omk config set plane.base_url VALUE
omk config set plane.api_key VALUE
omk config set plane.workspace_slug VALUE
omk config set plane.project_id VALUE
omk config set linear.api_key VALUE
omk config set linear.team_id VALUE
omk config set output VALUE
omk config migrate [--profile PROFILE]
omk config migrate --all-profiles
```

### Plane

Use provider context on the group:

```bash
omk plane --workspace MY_WORKSPACE --project PROJECT_UUID work-item list
```

Common commands:

```bash
omk plane work-item list
omk plane work-item create --name NAME
omk plane cycle create --name NAME --start-date YYYY-MM-DD --end-date YYYY-MM-DD
omk plane project list
omk plane state list
```

### Linear

Common commands:

```bash
omk linear me
omk linear team list
omk linear issue list [--team TEAM_ID]
omk linear issue create --title TITLE --team TEAM_ID
omk linear state list [--team TEAM_ID]
```

Note:

- `linear issue create` requires `--team`
- `linear state list` can fall back to `LINEAR_TEAM_ID` or config

## Troubleshooting

### Python Not Found

Installer requires Python 3.10+ for the runtime package.

### pip / PEP 668

The installer will try:

1. `pip3`
2. `pip`
3. `python -m pip`
4. `uv pip`
5. `pipx` fallback when PEP 668 blocks direct install

If you only want config output, use:

```bash
npx @oh-my-kanban/setup --config-only
```

### Validate The Final State

Plane:

```bash
omk plane --help
omk plane work-item list
```

Linear:

```bash
omk linear --help
omk linear me
```

If these commands fail, inspect:

```bash
omk config show --profile YOUR_PROFILE
```
