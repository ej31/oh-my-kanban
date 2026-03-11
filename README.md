# oh-my-kanban

| [한국어](docs/README_kr.md) | [ENGLISH](docs/README_en.md) |
|---|---|

You are setting up one CLI for two providers: Plane and Linear.

We already separated the runtime, installer, config format, and provider flows.
Use the installation guide. Do not reverse-engineer setup from random files.

## Installation

### For Humans

Paste this into your coding agent:

```text
Install and configure oh-my-kanban by following the guide here:
https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

Or read the guide directly:

- [Installation Guide](docs/guide/installation.md)

### For LLM Agents

Fetch the guide and follow it exactly:

```bash
curl -fsSL https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

### Skip This README

If you already know what to do, use this:

```text
Read and follow this installation guide exactly:
https://raw.githubusercontent.com/ej31/oh-my-kanban/refs/heads/main/docs/guide/installation.md
```

## Highlights

- Unified runtime: `omk`
- Providers: `plane`, `linear`
- Interactive installer: `npx @oh-my-kanban/setup`
- Canonical config guide: [`docs/guide/installation.md`](docs/guide/installation.md)
