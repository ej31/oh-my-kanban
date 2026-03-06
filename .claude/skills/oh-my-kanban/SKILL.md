# oh-my-kanban Development Patterns

> Auto-generated skill from repository analysis

## Overview

oh-my-kanban is a Python-based Kanban CLI tool that follows clean architecture principles with modular command structure. The codebase emphasizes comprehensive testing, multi-language documentation, and robust error handling. It uses conventional commits and maintains strict separation between CLI commands, core logic, and configuration management.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Test files follow pattern `test_*.py`
- Configuration files in `.omc/` directory
- Documentation organized in `docs/` with language suffixes

### Import Style
```python
# Standard library imports first
import os
import sys

# Third-party imports
import click
import pytest

# Local imports
from oh_my_kanban.config import Config
from oh_my_kanban.errors import ConfigError
```

### Commit Messages
- Use conventional commit format: `type: description`
- Common prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- Keep messages under 50 characters
- Examples:
  - `feat: add board creation command`
  - `docs: update Korean README`
  - `test: add E2E tests for CLI commands`

## Workflows

### Comprehensive Testing Addition
**Trigger:** When adding extensive test coverage for CLI commands
**Command:** `/add-e2e-tests`

1. Create test files for specific command groups in `tests/test_*.py`
2. Add shared fixtures to `tests/conftest.py`
3. Create helper functions in `tests/helpers.py`
4. Update `pyproject.toml` with test dependencies
5. Regenerate `uv.lock` with new dependencies

```python
# tests/conftest.py
@pytest.fixture
def mock_config():
    return Config(provider="test", board_id="123")

# tests/helpers.py  
def create_test_board(name="Test Board"):
    """Helper to create test board instances"""
    pass
```

### Multi-Language Documentation Update
**Trigger:** When CLI commands change or new features are added
**Command:** `/update-docs`

1. Update main `README.md` with new features
2. Synchronize Korean documentation in `docs/README_kr.md`
3. Update English documentation in `docs/README_en.md`
4. Update `AGENTS.md` for AI integration patterns
5. Refresh internal documentation in `.omc/docs-outline.md`

### Dependency Management Workflow
**Trigger:** When adding new dependencies or updating existing ones
**Command:** `/update-deps`

1. Add dependency to `pyproject.toml` under appropriate section
2. Run `uv lock` to update `uv.lock` file
3. Verify compatibility with existing dependencies
4. Test that all imports work correctly

```toml
# pyproject.toml
[project.dependencies]
click = ">=8.0.0"
requests = ">=2.28.0"

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-mock>=3.0"]
```

### CLI Command Structure Refactoring
**Trigger:** When reorganizing command hierarchy or adding new providers
**Command:** `/refactor-cli`

1. Update `src/oh_my_kanban/cli.py` with new command groups
2. Create or update command modules in `src/oh_my_kanban/commands/`
3. Update documentation to reflect new command structure
4. Add corresponding tests for new commands
5. Update configuration handling in `src/oh_my_kanban/config.py`

```python
# cli.py
@click.group()
def boards():
    """Board management commands"""
    pass

@boards.command()
def create():
    """Create a new board"""
    pass
```

### Error Handling and Defensive Coding
**Trigger:** When hardening code reliability and user experience
**Command:** `/harden-errors`

1. Update error handling in `src/oh_my_kanban/errors.py`
2. Add validation in `src/oh_my_kanban/utils.py`
3. Improve context validation in `src/oh_my_kanban/context.py`
4. Enhance configuration error handling in `src/oh_my_kanban/config.py`
5. Update output formatting with guards in `src/oh_my_kanban/output.py`

```python
# errors.py
class ConfigError(Exception):
    """Configuration related errors"""
    pass

class ProviderError(Exception):
    """Provider integration errors"""
    pass

# utils.py
def validate_board_id(board_id: str) -> bool:
    if not board_id or not board_id.strip():
        raise ValueError("Board ID cannot be empty")
    return True
```

## Testing Patterns

### Test Structure
- Tests located in `tests/` directory
- Use `pytest` framework (inferred from patterns)
- Shared fixtures in `conftest.py`
- Helper functions in `tests/helpers.py`
- Test files mirror source structure: `test_commands.py` for `commands.py`

### Test Examples
```python
# tests/test_cli.py
def test_board_create_command(mock_config):
    """Test board creation via CLI"""
    result = runner.invoke(cli, ['boards', 'create', '--name', 'Test'])
    assert result.exit_code == 0

def test_invalid_config_handling():
    """Test error handling for invalid configuration"""
    with pytest.raises(ConfigError):
        Config.load_from_file("nonexistent.toml")
```

## Commands

| Command | Purpose |
|---------|---------|
| `/add-e2e-tests` | Add comprehensive E2E test suites with fixtures and helpers |
| `/update-docs` | Update documentation across all languages and formats |
| `/update-deps` | Manage Python dependencies and synchronize lock files |
| `/refactor-cli` | Refactor CLI command structure and provider groups |
| `/harden-errors` | Improve error handling and add defensive coding patterns |