# Installer

Interactive setup wizard for the unified `oh-my-kanban` CLI.

Current capabilities:

- Multi-select provider setup for `plane` and `linear`
- Provider-specific prompts for API keys and defaults
- Canonical namespaced `~/.config/oh-my-kanban/config.toml` writing
- Unified Python package installation through `pip`, `python -m pip`, `uv pip`, or `pipx` fallback
- Shared provider metadata sourced from [`shared/provider-metadata.json`](../shared/provider-metadata.json)

Local usage:

```bash
cd installer
npm install
npm run start
```

Useful flags:

- `--skip-install`: skip Python package installation and only write config
- `OMK_INSTALL_PACKAGE=<package>`: override the Python package name for testing

Validation:

```bash
npm test
npm run build
```
