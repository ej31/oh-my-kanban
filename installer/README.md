# Installer

Interactive setup wizard for the unified `oh-my-kanban` CLI.

Intended published entrypoint:

```bash
npx @oh-my-kanban/setup
```

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

- `--config-only`: write config only and skip Python package installation
- `--skip-install`: legacy alias for `--config-only`
- `OMK_INSTALL_PACKAGE=<package>`: override the Python package name for testing

Validation:

```bash
npm test
npm run build
```
