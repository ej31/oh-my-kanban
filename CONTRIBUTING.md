# Contributing to oh-my-kanban

Thank you for your interest in contributing! This document outlines how to get started.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to uphold these standards.

## How to Contribute

### Reporting Bugs

Before opening a bug report, please search [existing issues](https://github.com/ej31/oh-my-kanban/issues).

When filing a bug, include:
- A clear title and description
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Python version, oh-my-kanban version)

### Suggesting Features

Open a [feature request](https://github.com/ej31/oh-my-kanban/issues/new?template=feature_request.md) and describe:
- The problem it solves
- Your proposed solution
- Alternatives you've considered

### Submitting Pull Requests

1. Fork the repository and create your branch from `main`
2. Use the naming convention: `feat/...`, `fix/...`, `docs/...`, `chore/...`
3. Ensure your code follows the project style
4. Add or update tests as appropriate
5. Make sure all tests pass locally
6. Open a PR targeting `main` with a clear description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/oh-my-kanban.git
cd oh-my-kanban

# Install dependencies (requires uv)
uv sync

# Run the CLI locally
uv run omk --help
```

## Commit Messages

Follow the format: `type(scope): description`

Types: `feat`, `fix`, `docs`, `refactor`, `style`, `perf`, `test`, `chore`

Example:

```text
feat(cycle): add archive command
fix(auth): handle missing API key gracefully
```

## Questions?

Open a [Discussion](https://github.com/ej31/oh-my-kanban/discussions) for questions that aren't bug reports or feature requests.
