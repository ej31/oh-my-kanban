# oh-my-kanban Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill covers development patterns for oh-my-kanban, a Python-based kanban board application. The codebase follows conventional commit patterns, emphasizes comprehensive testing, and maintains multilingual documentation. Key patterns include test refactoring workflows, internationalization processes, dependency management, and configuration hardening.

## Coding Conventions

### File Naming
- Use `snake_case` for all Python files
- Test files follow pattern `test_*.py`
- Configuration files use descriptive names like `conftest.py`

### Import Style
```python
# Mixed import style - organize by:
# 1. Standard library imports
# 2. Third-party imports  
# 3. Local application imports
import os
from pathlib import Path

import click
import pytest

from oh_my_kanban.config import Config
```

### Project Structure
```
src/oh_my_kanban/
├── commands/
│   └── config_cmd.py
├── config.py
└── errors.py
tests/
├── conftest.py
├── helpers.py
└── test_*.py
docs/
├── README_en.md
└── README_kr.md
```

## Workflows

### Test Refactoring Cleanup
**Trigger:** When test code becomes repetitive or contains duplicate patterns  
**Command:** `/refactor-tests`

1. Create or update `tests/helpers.py` with common utility functions
2. Add shared fixtures to `tests/conftest.py`
3. Update multiple `test_*.py` files to use shared helpers
4. Remove duplicate code patterns across test files
5. Ensure all tests still pass after refactoring

```python
# tests/helpers.py
def create_mock_config():
    """Common helper for test configuration"""
    return MockConfig(...)

# tests/conftest.py
@pytest.fixture
def sample_board():
    """Shared fixture for board testing"""
    return Board(...)
```

### Documentation Internationalization
**Trigger:** When documentation needs to be available in multiple languages  
**Command:** `/internationalize-docs`

1. Update main `README.md` with latest content
2. Create or update `docs/README_kr.md` (Korean version)
3. Create or update `docs/README_en.md` (English version)
4. Add language switcher links at the top of each document
5. Sync content structure and features across all language versions
6. Update `AGENTS.md` if applicable

```markdown
<!-- Language switcher example -->
[English](./docs/README_en.md) | [한국어](./docs/README_kr.md)

# oh-my-kanban
[Translated content follows...]
```

### Dependency Lock Update
**Trigger:** When new dependencies are added or dependency resolution changes  
**Command:** `/update-deps`

1. Add or modify dependencies in `pyproject.toml`
2. Run dependency resolution to update `uv.lock` file
3. Verify compatibility between all dependencies
4. Test that the application still functions correctly

```toml
# pyproject.toml
[project]
dependencies = [
    "click>=8.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-mock",
]
```

### Config Error Handling Improvement
**Trigger:** When configuration code needs better error handling or validation  
**Command:** `/harden-config`

1. Update `src/oh_my_kanban/config.py` with validation and error handling
2. Modify `src/oh_my_kanban/commands/config_cmd.py` with defensive guards
3. Enhance `src/oh_my_kanban/errors.py` with specific error types
4. Add clear, user-friendly error messages
5. Include fallback behavior for common failure cases

```python
# config.py example
class Config:
    def load_config(self, path: Path) -> None:
        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ConfigNotFoundError(f"Config file not found: {path}")
        except json.JSONDecodeError as e:
            raise ConfigParseError(f"Invalid JSON in config: {e}")
        
        self._validate_config(data)
```

### Comprehensive Testing Addition
**Trigger:** When new features need test coverage or existing functionality lacks tests  
**Command:** `/add-comprehensive-tests`

1. Create or update multiple `test_*.py` files for different components
2. Add test fixtures and helpers in `tests/conftest.py`
3. Update `pyproject.toml` with test configuration
4. Update `uv.lock` with any new test dependencies
5. Include E2E tests that mock external services
6. Ensure good test coverage across CLI functionality

```python
# Example comprehensive test structure
def test_cli_command_with_mocked_service(mock_service, sample_config):
    """E2E test with mocked external dependencies"""
    result = runner.invoke(cli, ['command', '--option', 'value'])
    assert result.exit_code == 0
    mock_service.assert_called_once_with(expected_params)
```

## Testing Patterns

### Test Organization
- Place all tests in `tests/` directory
- Use `conftest.py` for shared fixtures
- Create `helpers.py` for common test utilities
- Mock external services in E2E tests

### Test Structure
```python
# Standard test pattern
def test_feature_with_valid_input(fixture_name):
    # Arrange
    setup_data = create_test_data()
    
    # Act  
    result = function_under_test(setup_data)
    
    # Assert
    assert result.status == "expected"
    assert result.data == expected_data
```

## Commit Patterns

Follow conventional commits with these prefixes:
- `feat:` - New features
- `fix:` - Bug fixes  
- `refactor:` - Code refactoring
- `test:` - Test updates
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks

Keep commit messages under 50 characters when possible.

## Commands

| Command | Purpose |
|---------|---------|
| `/refactor-tests` | Clean up test code by extracting helpers and removing duplication |
| `/internationalize-docs` | Create/update documentation in multiple languages |
| `/update-deps` | Update dependency lock file after adding packages |
| `/harden-config` | Improve configuration error handling and validation |
| `/add-comprehensive-tests` | Add extensive test coverage for new features |