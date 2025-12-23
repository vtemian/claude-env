# Code Style Guide

## Quick Reference

| Element | Convention | Example |
|---------|------------|---------|
| Files | `snake_case.py` | `logging_config.py` |
| Functions | `snake_case` | `get_env_path()` |
| Classes | `PascalCase` | `CenvError` |
| Constants | `SCREAMING_SNAKE_CASE` | `DEFAULT_ENV_NAME` |
| Private | `_prefix` | `_config`, `_switch_lock` |
| Tests | `test_<what>_<behavior>()` | `test_get_envs_dir_returns_correct_path()` |

## File Organization

### Source Files (`src/cenv/`)

Each module has a specific responsibility:

```python
# ABOUTME: Brief description of module purpose
# ABOUTME: Additional context if needed
"""Module docstring"""

import stdlib_modules
import third_party_modules
from cenv.internal import imports

__all__ = [
    "PublicFunction",
    "PublicClass",
]

# Constants
CONSTANT_NAME = "value"

# Module-level private state
_private_var = None
_private_lock = threading.Lock()


# Public functions/classes
def public_function() -> ReturnType:
    """Docstring."""
    pass


# Private functions
def _private_helper() -> None:
    pass
```

### ABOUTME Comments

Every source file starts with two `# ABOUTME:` comments:

```python
# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
```

### Import Order

Enforced by ruff (isort rules):

```python
# 1. Standard library
import os
import threading
from pathlib import Path

# 2. Third-party
import typer
import psutil

# 3. Local imports
from cenv.exceptions import CenvError
from cenv.logging_config import get_logger
```

## Naming Conventions

### Functions

| Pattern | Usage | Example |
|---------|-------|---------|
| `get_<noun>()` | Accessor/retrieval | `get_envs_dir()`, `get_config()` |
| `<verb>_<noun>()` | Actions | `list_environments()`, `validate_environment_name()` |
| `<verb>_<noun>_<context>()` | Contextual actions | `restore_from_trash()`, `clone_from_github()` |
| `_<name>()` | Internal/testing | `_reset_config_for_testing()` |

### Classes

| Pattern | Usage | Example |
|---------|-------|---------|
| `<Domain>Error` | Base/general errors | `CenvError`, `GitOperationError` |
| `<Noun><State>Error` | State-specific errors | `EnvironmentNotFoundError` |
| `<Adjective><Noun>Error` | Validation errors | `InvalidBackupFormatError` |
| `PascalCase` | Data classes | `Config`, `PublishResult` |

### Variables

```python
# Local variables: descriptive snake_case
trash_dir = get_trash_dir()
backup_path = trash_dir / backup_name
target_env = get_env_path(name)

# Collections: plural nouns
backups = []
envs = list_environments()

# Iterators: singular nouns
for item in trash_dir.iterdir():
    for backup in backups:

# Module-level private: underscore prefix
_config: Config | None = None
_switch_lock = threading.Lock()
```

### Constants

```python
# All caps with underscores
ENVS_DIR_NAME = ".claude-envs"
DEFAULT_ENV_NAME = "default"
DEFAULT_GIT_TIMEOUT = 300

# Collections
SHARED_ITEMS = ["projects", ".credentials.json"]
RESERVED_NAMES = {".", "..", ".trash"}

# Regex patterns
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
```

## Type Annotations

### Required Everywhere

mypy strict mode is enabled. All functions need type hints:

```python
def get_env_path(name: str) -> Path:
    """Get the path for a specific environment"""
    return get_envs_dir() / name

def list_environments() -> list[str]:
    """List all available environments"""
    ...

def get_current_environment() -> str | None:
    """Get the currently active environment name"""
    ...
```

### Union Types

Use `|` syntax (Python 3.10+):

```python
# Good
def func(value: str | None) -> Path | None:

# Avoid (old style)
def func(value: Optional[str]) -> Optional[Path]:
```

### Generic Collections

Use built-in generics:

```python
# Good
def list_trash() -> list[dict[str, str]]:

# Avoid
def list_trash() -> List[Dict[str, str]]:
```

## Docstrings

### Function Docstrings

```python
def restore_from_trash(backup_name: str) -> str:
    """Restore an environment from trash

    Args:
        backup_name: Full backup directory name (e.g., 'myenv-20251111-143022')

    Returns:
        Name of restored environment

    Raises:
        EnvironmentNotFoundError: If backup doesn't exist
        EnvironmentExistsError: If environment already exists
    """
```

### Class Docstrings

```python
class Config:
    """Configuration for cenv operations"""

class EnvironmentNotFoundError(CenvError):
    """Raised when an environment does not exist"""
```

## Error Handling

### Exception Hierarchy

All custom exceptions inherit from `CenvError`:

```python
class CenvError(Exception):
    """Base exception for all cenv errors"""
    pass

class EnvironmentNotFoundError(CenvError):
    """Raised when an environment does not exist"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Environment '{name}' does not exist")
```

### Exception Pattern

Store context in exception attributes:

```python
class GitOperationError(CenvError):
    def __init__(self, operation: str, url: str, reason: str):
        self.operation = operation
        self.url = url
        self.reason = reason
        super().__init__(f"Git {operation} failed for {url}: {reason}")
```

### Catching Exceptions

```python
# Catch specific exceptions
try:
    switch_environment(name, force=force)
except CenvError as e:
    typer.echo(format_error_with_help(e), err=True)
    raise SystemExit(1)

# Let critical exceptions propagate
# KeyboardInterrupt, SystemExit, etc. are NOT caught
```

## Logging

### Logger Setup

```python
from cenv.logging_config import get_logger

logger = get_logger(__name__)
```

### Log Levels

```python
logger.debug(f"Creating temporary symlink {temp_link} -> {target_env}")
logger.info(f"Switching to environment '{name}'")
logger.warning("Claude is running, refusing to switch without force=True")
logger.error(f"Environment '{name}' does not exist")
```

### Pattern

- `debug`: Implementation details, paths, internal state
- `info`: User-visible operations, success messages
- `warning`: Recoverable issues, user should be aware
- `error`: Operation failures, before raising exception

## Testing

### Test File Naming

```
tests/
├── test_core.py           # Tests for core.py
├── test_cli_create.py     # Tests for CLI create command
├── test_cli_use.py        # Tests for CLI use command
├── test_validation.py     # Tests for validation.py
└── test_integration.py    # End-to-end tests
```

### Test Function Naming

```python
def test_get_envs_dir_returns_correct_path():
    """Test that envs directory path is ~/.claude-envs"""

def test_switch_environment_logs_error_on_failure():
    """Test that switch_environment logs detailed error when cleanup is needed."""

def test_setup_shared_symlinks_idempotent():
    """Test that setup can be run multiple times safely"""
```

Pattern: `test_<function_or_feature>_<expected_behavior>()`

### Test Structure

```python
def test_something(tmp_path, monkeypatch):
    """Docstring describing what is being tested"""
    # Arrange
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    # Act
    result = some_function()

    # Assert
    assert result == expected
    assert (envs_dir / "something").exists()
```

### Fixtures

Use pytest's built-in fixtures:
- `tmp_path`: Temporary directory
- `monkeypatch`: Mock functions/attributes
- `caplog`: Capture log output

## CLI Patterns

### Command Definition

```python
@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the environment to create")],
    from_repo: Annotated[
        str | None, typer.Option("--from-repo", help="Clone from GitHub repository URL")
    ] = None,
) -> None:
    """Create a new environment"""
    try:
        # Implementation
        typer.echo(f"Created environment '{name}'")
    except CenvError as e:
        typer.echo(format_error_with_help(e), err=True)
        raise SystemExit(1)
```

### User Feedback

```python
# Success
typer.echo(f"Created environment '{name}'")

# Error (to stderr)
typer.echo(format_error_with_help(e), err=True)

# Confirmation prompt
if not typer.confirm(f"Delete environment '{name}'?"):
    typer.echo("Cancelled.")
    return
```

## Do's and Don'ts

### Do

- Use type hints everywhere
- Write docstrings for public functions
- Use `Path` objects, not string paths
- Validate all user input
- Use specific exception types
- Log before raising exceptions
- Use `tmp_path` in tests, not real filesystem

### Don't

- Catch `Exception` or `BaseException` broadly
- Use `os.path` (use `pathlib.Path`)
- Hardcode paths (use constants)
- Skip type hints (mypy strict will fail)
- Use `print()` (use `typer.echo()` or logging)
- Modify global state without locks
- Delete tests that fail (fix them)

## Linting Rules

Configured in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "I",   # isort
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
]
```

Run with: `make lint` or `ruff check src/cenv tests/`
