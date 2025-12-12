# Publish Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `cenv publish <repo-url>` command to share Claude configs to GitHub repositories.

**Architecture:** New `publish.py` module handles sensitive file detection and git push operations. Follows existing patterns from `github.py` for git subprocess calls. CLI command delegates to core function.

**Tech Stack:** Python 3.10+, typer, subprocess (git), shutil, fnmatch

---

## Task 1: Sensitive File Detection

**Files:**
- Create: `src/cenv/publish.py`
- Test: `tests/test_publish.py`

### Step 1: Write the failing test for sensitive patterns

```python
# tests/test_publish.py
# ABOUTME: Tests for publish functionality
# ABOUTME: Validates sensitive file detection and git push operations
import pytest

from cenv.publish import is_sensitive_file, SENSITIVE_PATTERNS


def test_is_sensitive_file_detects_credentials():
    """Test that credentials files are detected as sensitive"""
    assert is_sensitive_file("credentials.json") is True
    assert is_sensitive_file("credentials.local.json") is True


def test_is_sensitive_file_detects_env_files():
    """Test that .env files are detected as sensitive"""
    assert is_sensitive_file(".env") is True
    assert is_sensitive_file(".env.local") is True
    assert is_sensitive_file(".env.production") is True


def test_is_sensitive_file_detects_key_files():
    """Test that key/pem files are detected as sensitive"""
    assert is_sensitive_file("private.key") is True
    assert is_sensitive_file("server.pem") is True


def test_is_sensitive_file_detects_secrets():
    """Test that secret-containing filenames are detected"""
    assert is_sensitive_file("secrets.json") is True
    assert is_sensitive_file("auth.json") is True
    assert is_sensitive_file("tokens.json") is True
    assert is_sensitive_file("my_api_secret.txt") is True
    assert is_sensitive_file("apikey.json") is True


def test_is_sensitive_file_allows_safe_files():
    """Test that normal config files are allowed"""
    assert is_sensitive_file("CLAUDE.md") is False
    assert is_sensitive_file("settings.json") is False
    assert is_sensitive_file("config.json") is False
    assert is_sensitive_file("README.md") is False
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_publish.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.publish'"

### Step 3: Write minimal implementation

```python
# src/cenv/publish.py
# ABOUTME: Publish functionality for sharing Claude configs to GitHub
# ABOUTME: Handles sensitive file detection and git push operations
"""Publish functionality for cenv"""

import fnmatch

__all__ = [
    "SENSITIVE_PATTERNS",
    "is_sensitive_file",
]

# Patterns for files that should never be published
SENSITIVE_PATTERNS: set[str] = {
    # Credential files
    "credentials.json",
    "credentials.*.json",
    # Environment files
    ".env",
    ".env.*",
    # Key files
    "*.key",
    "*.pem",
    # Secret files
    "secrets.json",
    "secrets.*.json",
    "auth.json",
    "tokens.json",
}

# Substrings that indicate sensitive content
SENSITIVE_SUBSTRINGS: set[str] = {
    "secret",
    "token",
    "password",
    "apikey",
    "api_key",
}


def is_sensitive_file(filename: str) -> bool:
    """Check if a file should be excluded from publishing

    Args:
        filename: Name of the file (not full path)

    Returns:
        True if file is sensitive and should be excluded
    """
    filename_lower = filename.lower()

    # Check exact patterns and globs
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(filename_lower, pattern.lower()):
            return True

    # Check for sensitive substrings in filename
    for substring in SENSITIVE_SUBSTRINGS:
        if substring in filename_lower:
            return True

    return False
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_publish.py -v`
Expected: PASS (all 5 tests)

### Step 5: Run mypy

Run: `uv run mypy src/cenv/publish.py --strict`
Expected: Success: no issues found

### Step 6: Commit

```bash
git add src/cenv/publish.py tests/test_publish.py
git commit -m "feat(publish): add sensitive file detection"
```

---

## Task 2: Get Files to Publish

**Files:**
- Modify: `src/cenv/publish.py`
- Test: `tests/test_publish.py`

### Step 1: Write the failing test

Add to `tests/test_publish.py`:

```python
from pathlib import Path

from cenv.publish import get_files_to_publish


def test_get_files_to_publish_excludes_sensitive(tmp_path):
    """Test that sensitive files are excluded from publish list"""
    # Create test environment
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")
    (env_dir / "settings.json").write_text("{}")
    (env_dir / "credentials.json").write_text("secret")
    (env_dir / ".env").write_text("SECRET=value")

    to_publish, excluded = get_files_to_publish(env_dir)

    # Check published files
    published_names = [f.name for f in to_publish]
    assert "CLAUDE.md" in published_names
    assert "settings.json" in published_names

    # Check excluded files
    excluded_names = [f.name for f in excluded]
    assert "credentials.json" in excluded_names
    assert ".env" in excluded_names


def test_get_files_to_publish_handles_subdirectories(tmp_path):
    """Test that subdirectories are traversed"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    subdir = env_dir / "commands"
    subdir.mkdir()
    (subdir / "custom.md").write_text("# Custom")
    (subdir / "secrets.json").write_text("secret")

    to_publish, excluded = get_files_to_publish(env_dir)

    # Subdirectory files should be included/excluded appropriately
    published_names = [f.name for f in to_publish]
    excluded_names = [f.name for f in excluded]

    assert "custom.md" in published_names
    assert "secrets.json" in excluded_names


def test_get_files_to_publish_empty_directory(tmp_path):
    """Test handling of empty environment directory"""
    env_dir = tmp_path / "empty-env"
    env_dir.mkdir()

    to_publish, excluded = get_files_to_publish(env_dir)

    assert to_publish == []
    assert excluded == []
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_publish.py::test_get_files_to_publish_excludes_sensitive -v`
Expected: FAIL with "cannot import name 'get_files_to_publish'"

### Step 3: Write minimal implementation

Add to `src/cenv/publish.py`:

```python
from pathlib import Path

# Update __all__
__all__ = [
    "SENSITIVE_PATTERNS",
    "is_sensitive_file",
    "get_files_to_publish",
]


def get_files_to_publish(env_path: Path) -> tuple[list[Path], list[Path]]:
    """Get lists of files to publish and files to exclude

    Args:
        env_path: Path to the environment directory

    Returns:
        Tuple of (files_to_publish, excluded_files)
    """
    to_publish: list[Path] = []
    excluded: list[Path] = []

    for file_path in env_path.rglob("*"):
        if file_path.is_file():
            if is_sensitive_file(file_path.name):
                excluded.append(file_path)
            else:
                to_publish.append(file_path)

    return to_publish, excluded
```

### Step 4: Run tests to verify they pass

Run: `uv run pytest tests/test_publish.py -v`
Expected: PASS (all 8 tests)

### Step 5: Commit

```bash
git add src/cenv/publish.py tests/test_publish.py
git commit -m "feat(publish): add get_files_to_publish function"
```

---

## Task 3: Publish to Repository Function

**Files:**
- Modify: `src/cenv/publish.py`
- Test: `tests/test_publish.py`

### Step 1: Write the failing test for invalid URL

Add to `tests/test_publish.py`:

```python
from cenv.exceptions import GitOperationError
from cenv.publish import publish_to_repo


def test_publish_to_repo_rejects_invalid_url(tmp_path):
    """Test that publish raises error for invalid URL"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    with pytest.raises(GitOperationError, match="Invalid GitHub URL"):
        publish_to_repo(env_dir, "not-a-valid-url")
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_publish.py::test_publish_to_repo_rejects_invalid_url -v`
Expected: FAIL with "cannot import name 'publish_to_repo'"

### Step 3: Write implementation for URL validation

Add to `src/cenv/publish.py`:

```python
import shutil
import subprocess
from dataclasses import dataclass

from cenv.config import get_config
from cenv.exceptions import GitOperationError
from cenv.github import is_valid_github_url
from cenv.logging_config import get_logger

logger = get_logger(__name__)

# Update __all__
__all__ = [
    "SENSITIVE_PATTERNS",
    "is_sensitive_file",
    "get_files_to_publish",
    "publish_to_repo",
    "PublishResult",
]


@dataclass
class PublishResult:
    """Result of a publish operation"""
    success: bool
    files_published: int
    files_excluded: int
    excluded_files: list[str]


def publish_to_repo(env_path: Path, repo_url: str) -> PublishResult:
    """Publish environment to a GitHub repository

    Args:
        env_path: Path to the environment directory
        repo_url: GitHub repository URL

    Returns:
        PublishResult with operation details

    Raises:
        GitOperationError: If git operations fail
    """
    if not is_valid_github_url(repo_url):
        raise GitOperationError("validation", repo_url, "Invalid GitHub URL format")

    # Get files to publish
    to_publish, excluded = get_files_to_publish(env_path)
    excluded_names = [f.name for f in excluded]

    if excluded:
        logger.info(f"Excluding {len(excluded)} sensitive files: {excluded_names}")

    # Create temp directory for git operations
    temp_dir = env_path.parent / f".tmp_publish_{env_path.name}"

    try:
        # Clone the target repository
        logger.info(f"Cloning {repo_url}")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(temp_dir)],
            capture_output=True,
            text=True,
            check=False,
            timeout=get_config().git_timeout,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                raise GitOperationError("clone", repo_url, "Repository not found or access denied")
            raise GitOperationError("clone", repo_url, error_msg)

        # Clear existing files (except .git)
        for item in temp_dir.iterdir():
            if item.name != ".git":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Copy files to publish
        for file_path in to_publish:
            relative = file_path.relative_to(env_path)
            target = temp_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target)

        # Git add, commit, push
        logger.info("Committing changes")
        subprocess.run(
            ["git", "add", "-A"],
            cwd=temp_dir,
            capture_output=True,
            check=True,
        )

        # Check if there are changes to commit
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if not status_result.stdout.strip():
            logger.info("No changes to publish")
            return PublishResult(
                success=True,
                files_published=0,
                files_excluded=len(excluded),
                excluded_files=excluded_names,
            )

        commit_result = subprocess.run(
            ["git", "commit", "-m", "Update Claude config via cenv publish"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if commit_result.returncode != 0:
            raise GitOperationError("commit", repo_url, commit_result.stderr.strip())

        logger.info("Pushing to remote")
        push_result = subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=get_config().git_timeout,
        )

        if push_result.returncode != 0:
            error_msg = push_result.stderr.strip()
            if "rejected" in error_msg.lower() or "failed to push" in error_msg.lower():
                raise GitOperationError(
                    "push",
                    repo_url,
                    "Push failed - remote has changes not present locally. "
                    "Pull the repo manually, resolve conflicts, and try again.",
                )
            if "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                raise GitOperationError(
                    "push",
                    repo_url,
                    "Authentication failed - check your git credentials",
                )
            raise GitOperationError("push", repo_url, error_msg)

        logger.info("Publish successful")
        return PublishResult(
            success=True,
            files_published=len(to_publish),
            files_excluded=len(excluded),
            excluded_files=excluded_names,
        )

    except subprocess.TimeoutExpired:
        raise GitOperationError(
            "push",
            repo_url,
            f"Operation timed out after {get_config().git_timeout} seconds",
        )
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_publish.py::test_publish_to_repo_rejects_invalid_url -v`
Expected: PASS

### Step 5: Commit

```bash
git add src/cenv/publish.py tests/test_publish.py
git commit -m "feat(publish): add publish_to_repo function"
```

---

## Task 4: Additional Publish Tests

**Files:**
- Test: `tests/test_publish.py`

### Step 1: Write tests for git operations

Add to `tests/test_publish.py`:

```python
from unittest.mock import MagicMock, patch


@patch("subprocess.run")
def test_publish_to_repo_calls_git_clone(mock_run, tmp_path):
    """Test that publish clones the target repository"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            # Create temp dir with .git
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    result = publish_to_repo(env_dir, "https://github.com/user/repo")

    # Verify git clone was called
    clone_calls = [c for c in mock_run.call_args_list if "clone" in c[0][0]]
    assert len(clone_calls) == 1


@patch("subprocess.run")
def test_publish_to_repo_handles_no_changes(mock_run, tmp_path):
    """Test that publish handles no-changes scenario gracefully"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        if cmd[0] == "git" and cmd[1] == "status":
            # Return empty status (no changes)
            return MagicMock(returncode=0, stdout="", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    result = publish_to_repo(env_dir, "https://github.com/user/repo")

    assert result.success is True
    assert result.files_published == 0


@patch("subprocess.run")
def test_publish_to_repo_reports_excluded_files(mock_run, tmp_path):
    """Test that publish reports excluded sensitive files"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")
    (env_dir / "credentials.json").write_text("secret")
    (env_dir / ".env").write_text("SECRET=x")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        if cmd[0] == "git" and cmd[1] == "status":
            return MagicMock(returncode=0, stdout="M file", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    result = publish_to_repo(env_dir, "https://github.com/user/repo")

    assert result.files_excluded == 2
    assert "credentials.json" in result.excluded_files
    assert ".env" in result.excluded_files
```

### Step 2: Run all tests

Run: `uv run pytest tests/test_publish.py -v`
Expected: PASS (all tests)

### Step 3: Commit

```bash
git add tests/test_publish.py
git commit -m "test(publish): add git operation tests"
```

---

## Task 5: Core Module Integration

**Files:**
- Modify: `src/cenv/core.py`

### Step 1: Write the failing test

Add to `tests/test_publish.py`:

```python
def test_publish_environment_exported_from_core():
    """Test that publish_environment is exported from core"""
    from cenv.core import publish_environment
    assert callable(publish_environment)
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_publish.py::test_publish_environment_exported_from_core -v`
Expected: FAIL with "cannot import name 'publish_environment'"

### Step 3: Add publish_environment to core.py

Add import at top of `src/cenv/core.py`:

```python
from cenv.publish import publish_to_repo, PublishResult
```

Add to `__all__` in `src/cenv/core.py` (in the "# Operations" section):

```python
    "publish_environment",
```

Add function to `src/cenv/core.py`:

```python
def publish_environment(repo_url: str) -> PublishResult:
    """Publish the currently active environment to a GitHub repository

    Args:
        repo_url: GitHub repository URL

    Returns:
        PublishResult with operation details

    Raises:
        InitializationError: If cenv is not initialized
        GitOperationError: If git operations fail
    """
    logger.info(f"Publishing current environment to {repo_url}")

    current = get_current_environment()
    if current is None:
        raise InitializationError("No active environment. Run 'cenv init' first.")

    env_path = get_env_path(current)
    return publish_to_repo(env_path, repo_url)
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_publish.py::test_publish_environment_exported_from_core -v`
Expected: PASS

### Step 5: Run mypy

Run: `uv run mypy src/cenv/core.py --strict`
Expected: Success

### Step 6: Commit

```bash
git add src/cenv/core.py tests/test_publish.py
git commit -m "feat(core): add publish_environment function"
```

---

## Task 6: CLI Command

**Files:**
- Modify: `src/cenv/cli.py`
- Create: `tests/test_cli_publish.py`

### Step 1: Write the failing test

```python
# tests/test_cli_publish.py
# ABOUTME: Tests for CLI publish command
# ABOUTME: Verifies publish command calls core function and formats output
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from cenv.cli import cli
from cenv.publish import PublishResult


def test_publish_command_calls_publish_environment():
    """Test that 'cenv publish' calls publish_environment"""
    runner = CliRunner()

    mock_result = PublishResult(
        success=True,
        files_published=5,
        files_excluded=2,
        excluded_files=["credentials.json", ".env"],
    )

    with patch("cenv.cli.publish_environment", return_value=mock_result) as mock_publish:
        result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

        assert result.exit_code == 0
        mock_publish.assert_called_once_with("https://github.com/user/repo")
        assert "Published" in result.output
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_cli_publish.py -v`
Expected: FAIL with "No such command 'publish'"

### Step 3: Add publish command to cli.py

Add import at top of `src/cenv/cli.py`:

```python
from cenv.core import (
    DEFAULT_ENV_NAME,
    create_environment,
    delete_environment,
    get_current_environment,
    init_environments,
    list_environments,
    list_trash,
    publish_environment,  # Add this
    restore_from_trash,
    switch_environment,
)
```

Add command to `src/cenv/cli.py`:

```python
@app.command()
def publish(
    repo_url: Annotated[str, typer.Argument(help="GitHub repository URL to publish to")],
) -> None:
    """Publish current environment to a GitHub repository"""
    try:
        current = get_current_environment()
        if current is None:
            typer.echo("Error: No active environment to publish.", err=True)
            typer.echo("Run 'cenv init' to initialize.", err=True)
            raise SystemExit(1)

        result = publish_environment(repo_url)

        typer.echo(f"✓ Published environment '{current}' to {repo_url}")
        if result.files_excluded > 0:
            typer.echo(
                f"  Excluded {result.files_excluded} sensitive file(s) "
                "(use --verbose to see details)"
            )
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="publish"), err=True)
        raise SystemExit(1)
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_cli_publish.py -v`
Expected: PASS

### Step 5: Commit

```bash
git add src/cenv/cli.py tests/test_cli_publish.py
git commit -m "feat(cli): add publish command"
```

---

## Task 7: CLI Output Formatting Tests

**Files:**
- Test: `tests/test_cli_publish.py`

### Step 1: Write additional CLI tests

Add to `tests/test_cli_publish.py`:

```python
from cenv.exceptions import GitOperationError, InitializationError


def test_publish_command_shows_excluded_count():
    """Test that publish shows count of excluded files"""
    runner = CliRunner()

    mock_result = PublishResult(
        success=True,
        files_published=3,
        files_excluded=2,
        excluded_files=["credentials.json", ".env"],
    )

    with patch("cenv.cli.publish_environment", return_value=mock_result):
        with patch("cenv.cli.get_current_environment", return_value="work"):
            result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

            assert result.exit_code == 0
            assert "Excluded 2 sensitive file(s)" in result.output


def test_publish_command_shows_error_on_failure():
    """Test that publish shows error message on git failure"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value="work"):
        with patch(
            "cenv.cli.publish_environment",
            side_effect=GitOperationError("push", "url", "Push failed"),
        ):
            result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

            assert result.exit_code == 1
            assert "Error" in result.output


def test_publish_command_shows_error_when_not_initialized():
    """Test that publish shows error when not initialized"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value=None):
        result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

        assert result.exit_code == 1
        assert "No active environment" in result.output
```

### Step 2: Run all CLI tests

Run: `uv run pytest tests/test_cli_publish.py -v`
Expected: PASS (all 4 tests)

### Step 3: Commit

```bash
git add tests/test_cli_publish.py
git commit -m "test(cli): add publish command output tests"
```

---

## Task 8: Final Verification

### Step 1: Run full test suite

Run: `uv run pytest -v`
Expected: All tests PASS (140+ tests)

### Step 2: Run mypy

Run: `uv run mypy src/cenv --strict`
Expected: Success: no issues found

### Step 3: Run ruff

Run: `uv run ruff check src/cenv`
Expected: All checks passed

### Step 4: Final commit

```bash
git add -A
git commit -m "feat: complete publish command implementation"
```

### Step 5: Push

```bash
git push
```

---

## Summary

**Files Created:**
- `src/cenv/publish.py` - Sensitive file detection and publish logic
- `tests/test_publish.py` - Unit tests for publish module
- `tests/test_cli_publish.py` - CLI command tests

**Files Modified:**
- `src/cenv/core.py` - Added `publish_environment` export
- `src/cenv/cli.py` - Added `publish` command

**Total Tests Added:** ~15 new tests

**Commands Available After Implementation:**
```bash
cenv publish https://github.com/user/my-claude-config
```
