# oh-my-kanban Development Patterns

> Auto-generated skill from repository analysis

## Overview

oh-my-kanban is a Python CLI application for managing Kanban boards across multiple project management platforms. The codebase follows conventional commit patterns and emphasizes defensive coding practices, comprehensive testing, and multi-provider integration architecture.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Test files follow pattern: `test_*.py`
- Provider-specific modules: `{provider}_client.py`, `{provider}_context.py`, `{provider}_errors.py`

### Project Structure
```
src/oh_my_kanban/
├── cli.py                    # Main CLI entry point
├── config.py                 # Configuration management
├── context.py                # Shared context and validation
├── errors.py                 # Common error definitions
├── utils.py                  # Utility functions
├── output.py                 # Output formatting
├── {provider}_client.py      # Provider-specific API clients
├── {provider}_context.py     # Provider-specific context
└── commands/
    └── {provider}/           # Provider command modules
```

### Import Style
- Mixed import style accepted
- Prefer absolute imports for project modules
- Group imports: stdlib, third-party, local

### Commit Convention
- Use conventional commits with prefixes: `docs:`, `chore:`, `refactor:`, `fix:`, `test:`, `feat:`
- Keep commit messages around 50 characters
- Example: `feat: add Linear provider integration`

## Workflows

### Test Suite Addition
**Trigger:** When implementing new CLI functionality that needs test coverage
**Command:** `/add-tests`

1. Create test files in `tests/` directory following `test_*.py` pattern
2. Add test helpers and fixtures to `tests/helpers.py` and `tests/conftest.py`
3. Update `pyproject.toml` with new test dependencies
4. Run `uv lock` to update `uv.lock` after dependency changes
5. Ensure E2E test coverage for CLI commands

**Example test structure:**
```python
# tests/test_board_commands.py
import pytest
from oh_my_kanban.cli import cli

def test_board_list_command(runner, mock_config):
    result = runner.invoke(cli, ['board', 'list'])
    assert result.exit_code == 0
```

### Documentation Update
**Trigger:** When CLI commands change and documentation needs to be synchronized
**Command:** `/update-docs`

1. Update `README.md` with new command structure and examples
2. Update language-specific documentation in `docs/README_en.md` and `docs/README_kr.md`
3. Update `AGENTS.md` for AI integration instructions
4. Update internal documentation outlines in `.omc/docs-outline.md`
5. Ensure all command examples are current and functional

### Defensive Coding Hardening
**Trigger:** When addressing code review feedback or preventing runtime errors
**Command:** `/harden-code`

1. Add input validation and guards in relevant modules
2. Improve error handling and exception translation in `errors.py`
3. Add defensive checks for None/empty values throughout codebase
4. Standardize error message language and format
5. Update context validation methods in `context.py`

**Example defensive pattern:**
```python
def validate_board_id(board_id: str | None) -> str:
    if not board_id or not board_id.strip():
        raise ValidationError("Board ID cannot be empty")
    return board_id.strip()
```

### CLI Command Refactoring
**Trigger:** When consolidating duplicate code or restructuring command hierarchy
**Command:** `/refactor-cli`

1. Extract common validation logic to `context.py` methods
2. Update command files in `commands/` to use centralized helpers
3. Modify CLI structure in `cli.py` for better organization
4. Update command imports and ensure proper module organization
5. Test all command functionality after refactoring

### New Provider Integration
**Trigger:** When integrating a new project management or development platform
**Command:** `/add-provider`

1. Create provider-specific client: `src/oh_my_kanban/{provider}_client.py`
2. Implement provider context: `src/oh_my_kanban/{provider}_context.py`
3. Add provider error handling: `src/oh_my_kanban/{provider}_errors.py`
4. Create command directory: `src/oh_my_kanban/commands/{provider}/`
5. Implement provider commands with `__init__.py` and command modules
6. Update `config.py` with provider-specific configuration fields
7. Register provider subgroup in `cli.py`

**Provider integration template:**
```python
# {provider}_client.py
class {Provider}Client:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def get_boards(self) -> list[dict]:
        # Implementation
        pass

# cli.py
@cli.group()
def {provider}():
    """{Provider} integration commands."""
    pass
```

## Testing Patterns

### Test Organization
- Place all tests in `tests/` directory
- Use `conftest.py` for shared fixtures
- Create `helpers.py` for test utilities
- Follow naming convention: `test_{module_name}.py`

### Common Test Patterns
```python
# Fixture for CLI testing
@pytest.fixture
def runner():
    from click.testing import CliRunner
    return CliRunner()

# Mock configuration
@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    # Setup mock config
    return config_file
```

## Commands

| Command | Purpose |
|---------|---------|
| `/add-tests` | Add comprehensive E2E test coverage for new CLI functionality |
| `/update-docs` | Synchronize documentation with current CLI structure |
| `/harden-code` | Strengthen error handling, validation, and edge case protection |
| `/refactor-cli` | Refactor CLI command structure and extract common patterns |
| `/add-provider` | Integrate support for new external service providers |