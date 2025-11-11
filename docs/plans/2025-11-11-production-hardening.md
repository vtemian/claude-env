# Production Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden cenv for production use by fixing critical security vulnerabilities, race conditions, and adding operational infrastructure.

**Architecture:** Add custom exception hierarchy for better error handling, implement logging infrastructure, fix security issues in git operations, add atomic file operations to prevent race conditions, and implement backup mechanism for destructive operations.

**Tech Stack:** Python 3.10+, Click, psutil, stdlib logging, pytest

---

## Task 1: Custom Exception Hierarchy

**Files:**
- Create: `src/cenv/exceptions.py`
- Test: `tests/test_exceptions.py`

**Step 1: Write the failing test**

Create `tests/test_exceptions.py`:

```python
import pytest
from cenv.exceptions import (
    CenvError,
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
    GitOperationError,
)


def test_cenv_error_is_base_exception():
    """Test that CenvError is the base exception"""
    err = CenvError("test message")
    assert str(err) == "test message"
    assert isinstance(err, Exception)


def test_environment_not_found_error():
    """Test EnvironmentNotFoundError with environment name"""
    err = EnvironmentNotFoundError("myenv")
    assert "myenv" in str(err)
    assert isinstance(err, CenvError)


def test_environment_exists_error():
    """Test EnvironmentExistsError with environment name"""
    err = EnvironmentExistsError("myenv")
    assert "myenv" in str(err)
    assert isinstance(err, CenvError)


def test_claude_running_error():
    """Test ClaudeRunningError message"""
    err = ClaudeRunningError()
    assert "Claude" in str(err)
    assert "running" in str(err).lower()
    assert isinstance(err, CenvError)


def test_initialization_error():
    """Test InitializationError with custom message"""
    err = InitializationError("Already initialized")
    assert "Already initialized" in str(err)
    assert isinstance(err, CenvError)


def test_git_operation_error():
    """Test GitOperationError with operation details"""
    err = GitOperationError("clone", "https://github.com/user/repo", "timeout")
    assert "clone" in str(err)
    assert "timeout" in str(err)
    assert isinstance(err, CenvError)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.exceptions'"

**Step 3: Write minimal implementation**

Create `src/cenv/exceptions.py`:

```python
# ABOUTME: Custom exception hierarchy for cenv
# ABOUTME: Provides specific exception types for better error handling
"""Custom exceptions for cenv"""


class CenvError(Exception):
    """Base exception for all cenv errors"""
    pass


class EnvironmentNotFoundError(CenvError):
    """Raised when an environment does not exist"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Environment '{name}' does not exist")


class EnvironmentExistsError(CenvError):
    """Raised when trying to create an environment that already exists"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Environment '{name}' already exists")


class ClaudeRunningError(CenvError):
    """Raised when Claude Code is running and operation requires it to be stopped"""
    def __init__(self):
        super().__init__(
            "Claude Code is currently running. "
            "Please exit Claude before performing this operation."
        )


class InitializationError(CenvError):
    """Raised when initialization fails or cenv is not initialized"""
    pass


class GitOperationError(CenvError):
    """Raised when git operations fail"""
    def __init__(self, operation: str, url: str, reason: str):
        self.operation = operation
        self.url = url
        self.reason = reason
        super().__init__(
            f"Git {operation} failed for {url}: {reason}"
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_exceptions.py -v`

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/cenv/exceptions.py tests/test_exceptions.py
git commit -m "feat: add custom exception hierarchy for better error handling"
```

---

## Task 2: Remove Unused Dependency

**Files:**
- Modify: `pyproject.toml:6-10`

**Step 1: Write the failing test**

Create `tests/test_dependencies.py`:

```python
import subprocess


def test_requests_not_imported_in_codebase():
    """Verify requests is not used anywhere in the codebase"""
    result = subprocess.run(
        ["grep", "-r", "import requests", "src/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "requests should not be imported"

    result = subprocess.run(
        ["grep", "-r", "from requests", "src/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "requests should not be imported"
```

**Step 2: Run test to verify it passes (confirming requests is unused)**

Run: `pytest tests/test_dependencies.py -v`

Expected: PASS

**Step 3: Remove requests from dependencies**

Edit `pyproject.toml`:

```toml
dependencies = [
    "click>=8.1.0",
    "psutil>=5.9.0",
]
```

**Step 4: Verify installation still works**

Run: `uv pip install -e .`

Expected: SUCCESS (no requests installed)

**Step 5: Commit**

```bash
git add pyproject.toml tests/test_dependencies.py
git commit -m "chore: remove unused requests dependency"
```

---

## Task 3: Logging Infrastructure

**Files:**
- Create: `src/cenv/logging.py`
- Test: `tests/test_logging.py`
- Modify: `src/cenv/__init__.py`

**Step 1: Write the failing test**

Create `tests/test_logging.py`:

```python
import logging
from pathlib import Path
import pytest
from cenv.logging_config import setup_logging, get_logger


def test_setup_logging_creates_logger():
    """Test that setup_logging creates configured logger"""
    setup_logging(level=logging.DEBUG)
    logger = get_logger("test")

    assert logger is not None
    assert logger.level == logging.DEBUG


def test_get_logger_returns_logger_with_name():
    """Test that get_logger returns properly named logger"""
    logger = get_logger("cenv.test")
    assert logger.name == "cenv.test"


def test_logging_to_file(tmp_path):
    """Test that logs can be written to file"""
    log_file = tmp_path / "cenv.log"
    setup_logging(level=logging.INFO, log_file=log_file)

    logger = get_logger("test")
    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_logging_respects_level():
    """Test that logging level is respected"""
    setup_logging(level=logging.WARNING)
    logger = get_logger("test")

    # Debug and info should not be logged at WARNING level
    assert not logger.isEnabledFor(logging.DEBUG)
    assert not logger.isEnabledFor(logging.INFO)
    assert logger.isEnabledFor(logging.WARNING)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_logging.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.logging_config'"

**Step 3: Write minimal implementation**

Create `src/cenv/logging_config.py`:

```python
# ABOUTME: Logging configuration for cenv
# ABOUTME: Provides centralized logging setup with file and console handlers
"""Logging configuration for cenv"""
import logging
import sys
from pathlib import Path
from typing import Optional


_configured = False


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """Configure logging for cenv

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
    """
    global _configured

    if _configured:
        return

    # Configure root logger for cenv
    logger = logging.getLogger("cenv")
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"cenv.{name}" if not name.startswith("cenv") else name)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_logging.py -v`

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/cenv/logging_config.py tests/test_logging.py
git commit -m "feat: add logging infrastructure with file and console handlers"
```

---

## Task 4: Add Logging to Core Module

**Files:**
- Modify: `src/cenv/core.py:1-10`
- Modify: `src/cenv/core.py:54-107`
- Modify: `src/cenv/core.py:109-136`
- Modify: `src/cenv/core.py:137-161`
- Modify: `src/cenv/core.py:162-183`

**Step 1: Add logger import**

Edit `src/cenv/core.py` at the top:

```python
# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional
import shutil
from cenv.process import is_claude_running
from cenv.github import clone_from_github, is_valid_github_url
from cenv.logging_config import get_logger

logger = get_logger(__name__)
```

**Step 2: Add logging to init_environments**

Edit `src/cenv/core.py` in `init_environments()`:

```python
def init_environments() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    logger.info("Initializing cenv")
    claude_dir = get_claude_dir()
    envs_dir = get_envs_dir()
    default_env = get_env_path("default")

    # Check if ~/.claude is already a symlink
    if claude_dir.is_symlink():
        logger.error("~/.claude is already a symlink")
        raise RuntimeError("~/.claude is already a symlink. Cannot initialize.")

    # Check if already initialized
    if envs_dir.exists():
        logger.error("cenv already initialized")
        raise RuntimeError("cenv already initialized. ~/.claude-envs exists.")

    # Create backup if claude_dir exists
    backup_dir = None
    if claude_dir.exists() and not claude_dir.is_symlink():
        backup_dir = claude_dir.parent / ".claude.backup"
        logger.info(f"Creating backup at {backup_dir}")
        shutil.copytree(claude_dir, backup_dir)

    try:
        # Create envs directory
        logger.debug(f"Creating envs directory at {envs_dir}")
        envs_dir.mkdir(parents=True, exist_ok=True)

        # Move ~/.claude to default environment
        if claude_dir.exists():
            logger.info(f"Moving {claude_dir} to {default_env}")
            shutil.move(str(claude_dir), str(default_env))
        else:
            # Create empty default environment
            logger.info(f"Creating empty default environment at {default_env}")
            default_env.mkdir(parents=True, exist_ok=True)

        # Create symlink
        logger.info(f"Creating symlink {claude_dir} -> {default_env}")
        claude_dir.symlink_to(default_env)

        # Clean up backup on success
        if backup_dir and backup_dir.exists():
            logger.debug(f"Removing backup at {backup_dir}")
            shutil.rmtree(backup_dir)

        logger.info("Initialization complete")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        # Restore from backup if anything failed
        if backup_dir and backup_dir.exists():
            logger.info(f"Restoring from backup at {backup_dir}")
            # Clean up any partial state
            if claude_dir.exists():
                if claude_dir.is_symlink():
                    claude_dir.unlink()
                else:
                    shutil.rmtree(claude_dir)
            if default_env.exists():
                shutil.rmtree(default_env)
            if envs_dir.exists() and not any(envs_dir.iterdir()):
                envs_dir.rmdir()
            # Restore original .claude
            shutil.move(str(backup_dir), str(claude_dir))
        raise RuntimeError(f"Initialization failed: {e}. Configuration restored from backup.")
```

**Step 3: Add logging to create_environment**

Edit `src/cenv/core.py` in `create_environment()`:

```python
def create_environment(name: str, source: str = "default") -> None:
    """Create a new environment by copying from source environment or GitHub URL"""
    logger.info(f"Creating environment '{name}' from '{source}'")
    envs_dir = get_envs_dir()

    # Check if initialized
    if not envs_dir.exists():
        logger.error("cenv not initialized")
        raise RuntimeError("cenv not initialized. Run 'cenv init' first.")

    # Check if environment already exists
    target_env = get_env_path(name)
    if target_env.exists():
        logger.error(f"Environment '{name}' already exists")
        raise RuntimeError(f"Environment '{name}' already exists.")

    # Check if source is a GitHub URL
    if source.startswith("https://") or source.startswith("git@"):
        if not is_valid_github_url(source):
            logger.error(f"Invalid GitHub URL: {source}")
            raise ValueError(f"Invalid GitHub URL: {source}")

        logger.info(f"Cloning from GitHub: {source}")
        clone_from_github(source, target_env)
    else:
        # Source is an environment name
        source_env = get_env_path(source)
        if not source_env.exists():
            logger.error(f"Source environment '{source}' not found")
            raise RuntimeError(f"{source} environment not found.")

        # Copy source to target
        logger.debug(f"Copying {source_env} to {target_env}")
        shutil.copytree(source_env, target_env, symlinks=True)

    logger.info(f"Environment '{name}' created successfully")
```

**Step 4: Add logging to switch_environment**

Edit `src/cenv/core.py` in `switch_environment()`:

```python
def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment"""
    logger.info(f"Switching to environment '{name}' (force={force})")
    target_env = get_env_path(name)

    # Check if target environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise RuntimeError(f"Environment '{name}' does not exist.")

    # Check if Claude is running
    if is_claude_running() and not force:
        logger.warning("Claude is running, refusing to switch without force=True")
        raise RuntimeError(
            "Claude is running. Please exit Claude first or use force=True."
        )

    claude_dir = get_claude_dir()

    # Remove existing symlink
    if claude_dir.is_symlink():
        logger.debug(f"Removing existing symlink at {claude_dir}")
        claude_dir.unlink()
    elif claude_dir.exists():
        logger.error(f"{claude_dir} exists but is not a symlink")
        raise RuntimeError("~/.claude exists but is not a symlink. Cannot switch.")

    # Create new symlink
    logger.debug(f"Creating symlink {claude_dir} -> {target_env}")
    claude_dir.symlink_to(target_env)
    logger.info(f"Switched to environment '{name}'")
```

**Step 5: Add logging to delete_environment**

Edit `src/cenv/core.py` in `delete_environment()`:

```python
def delete_environment(name: str) -> None:
    """Delete an environment"""
    logger.info(f"Deleting environment '{name}'")
    target_env = get_env_path(name)

    # Check if environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise RuntimeError(f"Environment '{name}' does not exist.")

    # Check if it's currently active
    current = get_current_environment()
    if current == name:
        logger.error(f"Cannot delete active environment '{name}'")
        raise RuntimeError(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )

    # Check if it's the default environment
    if name == "default":
        logger.error("Cannot delete default environment")
        raise RuntimeError("Cannot delete default environment.")

    # Delete the environment
    logger.debug(f"Removing directory {target_env}")
    shutil.rmtree(target_env)
    logger.info(f"Environment '{name}' deleted")
```

**Step 6: Run tests to verify nothing broke**

Run: `pytest tests/ -v`

Expected: PASS (all 61 tests still passing)

**Step 7: Commit**

```bash
git add src/cenv/core.py
git commit -m "feat: add comprehensive logging to core operations"
```

---

## Task 5: Update CLI to Initialize Logging

**Files:**
- Modify: `src/cenv/cli.py:1-12`
- Modify: `src/cenv/cli.py:14-21`

**Step 1: Add logging setup to CLI**

Edit `src/cenv/cli.py`:

```python
# ABOUTME: CLI interface for cenv using Click framework
# ABOUTME: Provides commands for init, create, use, list, current, and delete
import click
import logging
import os
from pathlib import Path
from cenv.core import (
    init_environments,
    create_environment,
    switch_environment,
    delete_environment,
    list_environments,
    get_current_environment,
)
from cenv.process import is_claude_running
from cenv.logging_config import setup_logging


@click.group()
@click.version_option()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Write logs to file"
)
def cli(verbose: bool, log_file: Path):
    """cenv - Claude environment manager

    Manage isolated Claude Code configurations like pyenv manages Python versions.
    """
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level, log_file=log_file)
```

**Step 2: Run CLI to verify logging works**

Run: `uvx --from . cenv --verbose list`

Expected: Should show debug logs if any exist

**Step 3: Commit**

```bash
git add src/cenv/cli.py
git commit -m "feat: add verbose logging and log-file options to CLI"
```

---

## Task 6: Update Core to Use Custom Exceptions

**Files:**
- Modify: `src/cenv/core.py:1-10`
- Modify: `src/cenv/core.py:54-107`
- Modify: `src/cenv/core.py:109-136`
- Modify: `src/cenv/core.py:137-161`
- Modify: `src/cenv/core.py:162-183`

**Step 1: Import custom exceptions**

Edit `src/cenv/core.py` at the top:

```python
from cenv.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
)
```

**Step 2: Update init_environments to use custom exceptions**

Edit `src/cenv/core.py` in `init_environments()`:

Replace:
```python
raise RuntimeError("~/.claude is already a symlink. Cannot initialize.")
```

With:
```python
raise InitializationError("~/.claude is already a symlink. Cannot initialize.")
```

Replace:
```python
raise RuntimeError("cenv already initialized. ~/.claude-envs exists.")
```

With:
```python
raise InitializationError("cenv already initialized. ~/.claude-envs exists.")
```

Replace the final RuntimeError:
```python
raise InitializationError(f"Initialization failed: {e}. Configuration restored from backup.")
```

**Step 3: Update create_environment to use custom exceptions**

Edit `src/cenv/core.py` in `create_environment()`:

Replace:
```python
raise RuntimeError("cenv not initialized. Run 'cenv init' first.")
```

With:
```python
raise InitializationError("cenv not initialized. Run 'cenv init' first.")
```

Replace:
```python
raise RuntimeError(f"Environment '{name}' already exists.")
```

With:
```python
raise EnvironmentExistsError(name)
```

Replace:
```python
raise RuntimeError(f"{source} environment not found.")
```

With:
```python
raise EnvironmentNotFoundError(source)
```

**Step 4: Update switch_environment to use custom exceptions**

Edit `src/cenv/core.py` in `switch_environment()`:

Replace:
```python
raise RuntimeError(f"Environment '{name}' does not exist.")
```

With:
```python
raise EnvironmentNotFoundError(name)
```

Replace:
```python
raise RuntimeError(
    "Claude is running. Please exit Claude first or use force=True."
)
```

With:
```python
raise ClaudeRunningError()
```

Keep the last RuntimeError about symlink as-is (it's a different error type).

**Step 5: Update delete_environment to use custom exceptions**

Edit `src/cenv/core.py` in `delete_environment()`:

Replace:
```python
raise RuntimeError(f"Environment '{name}' does not exist.")
```

With:
```python
raise EnvironmentNotFoundError(name)
```

Keep the other RuntimeErrors as-is (they're operational errors).

**Step 6: Update CLI to catch custom exceptions**

Edit `src/cenv/cli.py`:

Add import:
```python
from cenv.exceptions import CenvError
```

Update all exception handlers from `except (RuntimeError, ValueError)` to `except CenvError`.

For example in the `init` command:
```python
except CenvError as e:
    click.echo(f"Error: {e}", err=True)
    raise SystemExit(1)
```

Do this for all commands: `init`, `create`, `use`, `delete`.

**Step 7: Run tests to verify**

Run: `pytest tests/ -v`

Expected: All tests should still pass

**Step 8: Commit**

```bash
git add src/cenv/core.py src/cenv/cli.py
git commit -m "refactor: use custom exceptions instead of RuntimeError"
```

---

## Task 7: Fix Git Clone Security Issues

**Files:**
- Modify: `src/cenv/github.py:17-54`
- Test: `tests/test_github.py`

**Step 1: Write tests for timeout and shallow clone**

Edit `tests/test_github.py`, add tests:

```python
import pytest
from unittest.mock import patch, MagicMock
from cenv.github import clone_from_github
from cenv.exceptions import GitOperationError


def test_clone_uses_timeout(tmp_path):
    """Test that git clone includes timeout parameter"""
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        clone_from_github("https://github.com/user/repo.git", target)

        # Verify timeout was passed
        call_args = mock_run.call_args
        assert call_args.kwargs.get("timeout") is not None
        assert call_args.kwargs["timeout"] > 0


def test_clone_uses_shallow_clone(tmp_path):
    """Test that git clone uses --depth 1 for shallow clone"""
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        clone_from_github("https://github.com/user/repo.git", target)

        # Verify --depth 1 was used
        call_args = mock_run.call_args
        assert "--depth" in call_args.args[0]
        assert "1" in call_args.args[0]


def test_clone_timeout_raises_error(tmp_path):
    """Test that timeout raises GitOperationError"""
    import subprocess
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=30)

        with pytest.raises(GitOperationError) as exc_info:
            clone_from_github("https://github.com/user/repo.git", target)

        assert "timeout" in str(exc_info.value).lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_github.py::test_clone_uses_timeout -v`

Expected: FAIL

**Step 3: Update clone_from_github implementation**

Edit `src/cenv/github.py`:

```python
# ABOUTME: GitHub repository cloning functionality for cenv
# ABOUTME: Validates GitHub URLs and clones repositories using git subprocess
import subprocess
import shutil
from pathlib import Path
import re
from cenv.exceptions import GitOperationError

# Security: 5 minute timeout for git operations
GIT_TIMEOUT = 300


def is_valid_github_url(url: str) -> bool:
    """Validate if URL is a valid GitHub repository URL"""
    patterns = [
        r"^https://github\.com/[\w-]+/[\w.-]+(\.git)?$",
        r"^git@github\.com:[\w-]+/[\w.-]+\.git$",
    ]

    return any(re.match(pattern, url) for pattern in patterns)


def clone_from_github(url: str, target: Path) -> None:
    """Clone a GitHub repository to target directory

    Args:
        url: GitHub repository URL
        target: Target directory path

    Raises:
        GitOperationError: If clone fails or times out
    """
    if not is_valid_github_url(url):
        raise GitOperationError("validation", url, "Invalid GitHub URL format")

    # Create temporary directory for cloning
    temp_dir = target.parent / f".tmp_{target.name}"

    try:
        # Clone the repository with shallow clone and timeout
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(temp_dir)],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT,
        )

        if result.returncode != 0:
            raise GitOperationError("clone", url, result.stderr.strip())

        # Remove .git directory if it exists
        git_dir = temp_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        # Move to final location
        if target.exists():
            shutil.rmtree(target)

        # Only move if temp_dir exists (for real git clone)
        if temp_dir.exists():
            shutil.move(str(temp_dir), str(target))

    except subprocess.TimeoutExpired:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise GitOperationError("clone", url, f"Operation timed out after {GIT_TIMEOUT} seconds")
    except Exception as e:
        # Clean up temp directory if it exists
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if isinstance(e, GitOperationError):
            raise
        raise GitOperationError("clone", url, str(e))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_github.py -v`

Expected: PASS (all github tests)

**Step 5: Commit**

```bash
git add src/cenv/github.py tests/test_github.py
git commit -m "security: add timeout and shallow clone to git operations"
```

---

## Task 8: Add Backup Mechanism for Delete

**Files:**
- Modify: `src/cenv/core.py:10-20`
- Modify: `src/cenv/core.py:162-183`
- Test: `tests/test_delete.py`

**Step 1: Write test for backup creation**

Edit `tests/test_delete.py`, add test:

```python
import pytest
from pathlib import Path
import shutil
from cenv.core import (
    get_envs_dir,
    delete_environment,
    create_environment,
    init_environments,
    get_trash_dir,
    restore_from_trash,
    list_trash,
)


def test_get_trash_dir_returns_correct_path():
    """Test that trash directory is ~/.claude-envs/.trash"""
    result = get_trash_dir()
    assert result == Path.home() / ".claude-envs" / ".trash"


def test_delete_creates_backup_in_trash(tmp_path, monkeypatch):
    """Test that delete creates timestamped backup in trash"""
    # Setup
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Delete should create backup
    delete_environment("test-env")

    trash_dir = get_trash_dir()
    assert trash_dir.exists()

    # Should have one backup with timestamp
    backups = list(trash_dir.iterdir())
    assert len(backups) == 1
    assert backups[0].name.startswith("test-env-")


def test_list_trash_returns_backups(tmp_path, monkeypatch):
    """Test listing trash backups"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")
    delete_environment("test-env")

    backups = list_trash()
    assert len(backups) == 1
    assert backups[0]["name"] == "test-env"
    assert "timestamp" in backups[0]


def test_restore_from_trash(tmp_path, monkeypatch):
    """Test restoring environment from trash"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Create a marker file
    test_file = tmp_path / ".claude-envs" / "test-env" / "marker.txt"
    test_file.write_text("test content")

    delete_environment("test-env")

    # Environment should be gone
    env_path = tmp_path / ".claude-envs" / "test-env"
    assert not env_path.exists()

    # Get backup name
    backups = list_trash()
    backup_name = backups[0]["backup_name"]

    # Restore
    restore_from_trash(backup_name)

    # Should be restored
    assert env_path.exists()
    restored_file = env_path / "marker.txt"
    assert restored_file.exists()
    assert restored_file.read_text() == "test content"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_delete.py::test_get_trash_dir_returns_correct_path -v`

Expected: FAIL

**Step 3: Implement trash functionality**

Edit `src/cenv/core.py`:

Add after the `get_claude_dir()` function:

```python
def get_trash_dir() -> Path:
    """Get the trash directory for deleted environments"""
    return get_envs_dir() / ".trash"


def list_trash() -> List[dict]:
    """List backups in trash

    Returns:
        List of dicts with 'name', 'backup_name', 'timestamp' keys
    """
    trash_dir = get_trash_dir()

    if not trash_dir.exists():
        return []

    backups = []
    for item in trash_dir.iterdir():
        if item.is_dir():
            # Parse name: <env-name>-YYYYMMDD-HHMMSS
            parts = item.name.rsplit("-", 2)
            if len(parts) == 3:
                name = parts[0]
                timestamp = f"{parts[1]}-{parts[2]}"
                backups.append({
                    "name": name,
                    "backup_name": item.name,
                    "timestamp": timestamp,
                })

    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


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
    trash_dir = get_trash_dir()
    backup_path = trash_dir / backup_name

    if not backup_path.exists():
        raise EnvironmentNotFoundError(backup_name)

    # Extract original name
    parts = backup_name.rsplit("-", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid backup name format: {backup_name}")

    name = parts[0]
    target_path = get_env_path(name)

    if target_path.exists():
        raise EnvironmentExistsError(name)

    logger.info(f"Restoring '{name}' from trash backup '{backup_name}'")
    shutil.move(str(backup_path), str(target_path))
    logger.info(f"Environment '{name}' restored")

    return name
```

Update `delete_environment()`:

```python
def delete_environment(name: str) -> None:
    """Delete an environment (moves to trash)"""
    logger.info(f"Deleting environment '{name}'")
    target_env = get_env_path(name)

    # Check if environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise EnvironmentNotFoundError(name)

    # Check if it's currently active
    current = get_current_environment()
    if current == name:
        logger.error(f"Cannot delete active environment '{name}'")
        raise RuntimeError(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )

    # Check if it's the default environment
    if name == "default":
        logger.error("Cannot delete default environment")
        raise RuntimeError("Cannot delete default environment.")

    # Create trash directory if it doesn't exist
    trash_dir = get_trash_dir()
    trash_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup name
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"{name}-{timestamp}"
    backup_path = trash_dir / backup_name

    # Move to trash instead of deleting
    logger.info(f"Moving '{name}' to trash as '{backup_name}'")
    shutil.move(str(target_env), str(backup_path))
    logger.info(f"Environment '{name}' moved to trash (backup: {backup_name})")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_delete.py -v`

Expected: PASS (all delete tests)

**Step 5: Add CLI commands for trash management**

Edit `src/cenv/cli.py`, add new commands:

```python
@cli.command()
def trash():
    """List deleted environments in trash"""
    from cenv.core import list_trash

    backups = list_trash()

    if not backups:
        click.echo("Trash is empty.")
        return

    click.echo("Deleted environments (newest first):")
    for backup in backups:
        click.echo(f"  {backup['backup_name']}")
        click.echo(f"    Environment: {backup['name']}")
        click.echo(f"    Deleted: {backup['timestamp']}")
        click.echo()


@cli.command()
@click.argument("backup_name")
def restore(backup_name: str):
    """Restore an environment from trash"""
    from cenv.core import restore_from_trash

    try:
        name = restore_from_trash(backup_name)
        click.echo(f"✓ Restored environment '{name}' from trash")
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
```

**Step 6: Test CLI commands**

Run: `uvx --from . cenv trash`

Expected: Shows trash contents

**Step 7: Commit**

```bash
git add src/cenv/core.py src/cenv/cli.py tests/test_delete.py
git commit -m "feat: add trash mechanism with restore for deleted environments"
```

---

## Task 9: Fix TOCTOU Race Condition in init_environments

**Files:**
- Modify: `src/cenv/core.py:54-107`
- Test: `tests/test_init.py`

**Step 1: Write test for atomic initialization**

Edit `tests/test_init.py`, add test:

```python
import pytest
from pathlib import Path
import time
import threading
from cenv.core import init_environments


def test_concurrent_init_only_one_succeeds(tmp_path, monkeypatch):
    """Test that concurrent initialization is safe"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    results = []

    def init_thread():
        try:
            init_environments()
            results.append("success")
        except Exception:
            results.append("failed")

    # Launch multiple threads trying to init
    threads = [threading.Thread(target=init_thread) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Only one should succeed
    assert results.count("success") == 1
    assert results.count("failed") == 4
```

**Step 2: Run test to see current behavior**

Run: `pytest tests/test_init.py::test_concurrent_init_only_one_succeeds -v`

Expected: May FAIL or PASS unreliably (race condition)

**Step 3: Implement atomic initialization with lock file**

Edit `src/cenv/core.py`, update `init_environments()`:

```python
def init_environments() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    import fcntl
    import tempfile

    logger.info("Initializing cenv")
    claude_dir = get_claude_dir()
    envs_dir = get_envs_dir()
    default_env = get_env_path("default")

    # Use lock file to prevent concurrent initialization
    lock_file_path = Path(tempfile.gettempdir()) / "cenv-init.lock"
    lock_file = None

    try:
        lock_file = open(lock_file_path, "w")
        # Try to acquire exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise InitializationError(
                "Another cenv initialization is in progress. Please wait."
            )

        # Check if ~/.claude is already a symlink
        if claude_dir.is_symlink():
            logger.error("~/.claude is already a symlink")
            raise InitializationError("~/.claude is already a symlink. Cannot initialize.")

        # Check if already initialized
        if envs_dir.exists():
            logger.error("cenv already initialized")
            raise InitializationError("cenv already initialized. ~/.claude-envs exists.")

        # Create backup if claude_dir exists
        backup_dir = None
        if claude_dir.exists() and not claude_dir.is_symlink():
            backup_dir = claude_dir.parent / ".claude.backup"
            logger.info(f"Creating backup at {backup_dir}")
            shutil.copytree(claude_dir, backup_dir)

        try:
            # Create envs directory
            logger.debug(f"Creating envs directory at {envs_dir}")
            envs_dir.mkdir(parents=True, exist_ok=True)

            # Move ~/.claude to default environment
            if claude_dir.exists():
                logger.info(f"Moving {claude_dir} to {default_env}")
                shutil.move(str(claude_dir), str(default_env))
            else:
                # Create empty default environment
                logger.info(f"Creating empty default environment at {default_env}")
                default_env.mkdir(parents=True, exist_ok=True)

            # Create symlink
            logger.info(f"Creating symlink {claude_dir} -> {default_env}")
            claude_dir.symlink_to(default_env)

            # Clean up backup on success
            if backup_dir and backup_dir.exists():
                logger.debug(f"Removing backup at {backup_dir}")
                shutil.rmtree(backup_dir)

            logger.info("Initialization complete")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            # Restore from backup if anything failed
            if backup_dir and backup_dir.exists():
                logger.info(f"Restoring from backup at {backup_dir}")
                # Clean up any partial state
                if claude_dir.exists():
                    if claude_dir.is_symlink():
                        claude_dir.unlink()
                    else:
                        shutil.rmtree(claude_dir)
                if default_env.exists():
                    shutil.rmtree(default_env)
                if envs_dir.exists() and not any(envs_dir.iterdir()):
                    envs_dir.rmdir()
                # Restore original .claude
                shutil.move(str(backup_dir), str(claude_dir))
            raise InitializationError(f"Initialization failed: {e}. Configuration restored from backup.")

    finally:
        # Release lock and clean up
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                lock_file_path.unlink(missing_ok=True)
            except Exception:
                pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_init.py::test_concurrent_init_only_one_succeeds -v`

Expected: PASS (consistently)

**Step 5: Run all tests**

Run: `pytest tests/ -v`

Expected: PASS (all tests)

**Step 6: Commit**

```bash
git add src/cenv/core.py tests/test_init.py
git commit -m "fix: prevent race conditions in init_environments with file lock"
```

---

## Task 10: Add Type Checking with mypy

**Files:**
- Create: `pyproject.toml` (add mypy config)
- Modify: `Makefile`
- Create: `.github/workflows/ci.yml` (if doesn't exist)

**Step 1: Add mypy to dev dependencies**

Edit `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

**Step 2: Add mypy to Makefile**

Edit `Makefile`:

```makefile
.PHONY: install test clean typecheck

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/ -v

typecheck:
	mypy src/cenv

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

**Step 3: Run mypy to see errors**

Run: `uv pip install mypy && make typecheck`

Expected: May show type errors

**Step 4: Fix type errors if any**

Fix any type issues mypy reports. Common fixes:
- Add return type annotations
- Add parameter type annotations
- Handle Optional types properly

**Step 5: Verify mypy passes**

Run: `make typecheck`

Expected: Success: no issues found

**Step 6: Commit**

```bash
git add pyproject.toml Makefile src/cenv/
git commit -m "chore: add mypy strict type checking"
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/SECURITY.md`

**Step 1: Update README with new features**

Edit `README.md`, add sections:

```markdown
## Security

- Git clone operations use shallow clones (`--depth 1`) and have a 5-minute timeout
- All operations use custom exception types for better error handling
- Comprehensive logging available with `--verbose` flag
- See [SECURITY.md](docs/SECURITY.md) for security considerations

## Logging

Enable verbose logging:

```bash
cenv --verbose list
```

Write logs to file:

```bash
cenv --log-file ~/cenv.log list
```

## Trash and Recovery

Deleted environments are moved to trash instead of permanently deleted:

```bash
# Delete an environment (moves to trash)
cenv delete myenv

# List deleted environments
cenv trash

# Restore from trash
cenv restore myenv-20251111-143022
```

## Development

Run type checking:

```bash
make typecheck
```
```

**Step 2: Create security documentation**

Create `docs/SECURITY.md`:

```markdown
# Security Considerations

## Git Clone Operations

- **Timeout**: All git clone operations have a 5-minute timeout to prevent hanging
- **Shallow Clone**: Uses `--depth 1` to minimize data transfer and disk usage
- **URL Validation**: GitHub URLs are validated with regex before cloning

## File Operations

- **Atomic Operations**: Initialization uses file locks to prevent race conditions
- **Backup System**: Deleted environments are moved to trash, not permanently deleted
- **Symlink Validation**: All symlink operations validate paths

## Logging

- Sensitive information is not logged
- Log files may contain file paths and environment names
- Use `--log-file` carefully in shared environments

## Best Practices

1. Always use HTTPS URLs for git clone operations
2. Review environment contents before switching
3. Use `--verbose` flag when debugging issues
4. Keep cenv updated to latest version
5. Backup important configurations separately

## Reporting Security Issues

Please report security vulnerabilities to [maintainer email]
```

**Step 3: Commit**

```bash
git add README.md docs/SECURITY.md
git commit -m "docs: add security documentation and update README"
```

---

## Verification Steps

**Run all tests:**
```bash
pytest tests/ -v --cov=src/cenv --cov-report=term-missing
```

**Expected:**
- All tests pass
- Coverage > 80%

**Run type checking:**
```bash
make typecheck
```

**Expected:** Success: no issues found

**Test CLI commands:**
```bash
uvx --from . cenv --help
uvx --from . cenv --verbose list
```

**Expected:** All commands work with logging

---

## Summary

This plan addresses the critical production hardening issues:

✅ **Custom exception hierarchy** - Better error handling
✅ **Logging infrastructure** - Operational visibility
✅ **Security fixes** - Timeout and shallow clone for git
✅ **Backup mechanism** - Trash system prevents data loss
✅ **Race condition fix** - File lock prevents concurrent init
✅ **Type checking** - mypy strict mode
✅ **Documentation** - Security and feature docs

**Remaining for future:**
- Configuration system
- Better process detection
- Progress indicators
- Performance testing
- Property-based testing
