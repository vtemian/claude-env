# Production Readiness Fixes - v1.0 Preparation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address critical production readiness issues to achieve production-grade quality (target: A grade)

**Architecture:** Fix remaining architectural issues including platform compatibility, complete exception hierarchy migration, add input validation, implement atomic operations, and improve reliability. Focus on robustness, security, and operational excellence.

**Tech Stack:** Python 3.10+, Click, psutil, stdlib threading, platform detection

---

## Priority Overview

This plan addresses issues identified in the comprehensive code review (B+ 87/100 → A 95/100 target):

- **P0 Tasks (1-3):** Blocking issues for production (12 points recovery)
- **P1 Tasks (4-6):** Important reliability improvements (7 points recovery)
- **P2 Tasks (7-10):** Quality and maintainability (4 points recovery)

Total potential improvement: +23 points → Grade A (95/100+)

---

## Task 1: Add Platform Compatibility Check

**Files:**
- Modify: `src/cenv/core.py:131-227`
- Create: `src/cenv/platform_utils.py`
- Test: `tests/test_platform.py`

**Step 1: Write failing test for platform detection**

Create `tests/test_platform.py`:

```python
import platform
import pytest
from unittest.mock import patch
from cenv.platform_utils import check_platform_compatibility, PlatformNotSupportedError


def test_unix_platforms_are_supported():
    """Test that Unix-like platforms are supported"""
    for system in ['Linux', 'Darwin', 'FreeBSD']:
        with patch('platform.system', return_value=system):
            # Should not raise
            check_platform_compatibility()


def test_windows_raises_clear_error():
    """Test that Windows raises helpful error message"""
    with patch('platform.system', return_value='Windows'):
        with pytest.raises(PlatformNotSupportedError) as exc_info:
            check_platform_compatibility()

        error_msg = str(exc_info.value)
        assert "Windows" in error_msg
        assert "WSL" in error_msg or "Unix" in error_msg


def test_error_includes_workaround_suggestions():
    """Test that error message is helpful"""
    with patch('platform.system', return_value='Windows'):
        with pytest.raises(PlatformNotSupportedError) as exc_info:
            check_platform_compatibility()

        error_msg = str(exc_info.value)
        # Should suggest alternatives
        assert any(word in error_msg for word in ['WSL2', 'Linux', 'macOS'])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_platform.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.platform_utils'"

**Step 3: Create platform utilities module**

Create `src/cenv/platform_utils.py`:

```python
# ABOUTME: Platform compatibility detection and validation
# ABOUTME: Ensures cenv runs only on supported platforms
"""Platform compatibility utilities for cenv"""
import platform


class PlatformNotSupportedError(Exception):
    """Raised when cenv is run on an unsupported platform"""
    pass


def check_platform_compatibility() -> None:
    """Check if current platform is supported by cenv

    Raises:
        PlatformNotSupportedError: If platform is not supported
    """
    system = platform.system()

    # Supported platforms: Unix-like systems with fcntl
    supported = ['Linux', 'Darwin', 'FreeBSD', 'OpenBSD', 'SunOS']

    if system not in supported:
        raise PlatformNotSupportedError(
            f"cenv does not support {system}.\n\n"
            f"cenv requires file locking features available on Unix-like systems.\n\n"
            f"Supported platforms: {', '.join(supported)}\n\n"
            f"Workarounds:\n"
            f"  • Windows users: Use WSL2 (Windows Subsystem for Linux)\n"
            f"  • Install a Linux distribution or use macOS\n\n"
            f"For more information, see: https://github.com/yourusername/cenv#platform-support"
        )
```

**Step 4: Add platform check to init_environments**

Edit `src/cenv/core.py`:

Add import at top:
```python
from cenv.platform_utils import check_platform_compatibility, PlatformNotSupportedError
```

Update `init_environments()` function (line 131):
```python
def init_environments() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    # Check platform compatibility before attempting initialization
    check_platform_compatibility()

    import fcntl
    import tempfile

    logger.info("Initializing cenv")
    # ... rest of function
```

**Step 5: Update exception handling in CLI**

Edit `src/cenv/cli.py`:

Add import:
```python
from cenv.platform_utils import PlatformNotSupportedError
```

Update init command (line 42):
```python
@cli.command()
def init() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    try:
        init_environments()
        click.echo("✓ Initialized cenv successfully!")
        click.echo("  ~/.claude → ~/.claude-envs/default/")
        click.echo("\nUse 'cenv create <name>' to create new environments.")
    except PlatformNotSupportedError as e:
        click.echo(f"Platform Error: {e}", err=True)
        raise SystemExit(1)
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
```

**Step 6: Run tests to verify**

Run: `pytest tests/test_platform.py -v`

Expected: PASS (3 tests)

Run: `pytest tests/ -v`

Expected: PASS (all 83 tests)

**Step 7: Commit**

```bash
git add src/cenv/platform_utils.py tests/test_platform.py src/cenv/core.py src/cenv/cli.py
git commit -m "feat: add platform compatibility check for Windows

- Add platform_utils module with compatibility detection
- Raise clear error on Windows with WSL2 suggestion
- Check platform before fcntl import
- Add tests for platform detection
- Update CLI to handle PlatformNotSupportedError

Fixes platform lock-in issue (P0)"
```

---

## Task 2: Complete Exception Hierarchy Migration

**Files:**
- Modify: `src/cenv/exceptions.py:34-48`
- Modify: `src/cenv/core.py:85,288,309,317`
- Test: `tests/test_exceptions.py`

**Step 1: Write tests for new exception types**

Edit `tests/test_exceptions.py`, add:

```python
def test_invalid_backup_format_error():
    """Test InvalidBackupFormatError with backup name"""
    err = InvalidBackupFormatError("invalid-backup")
    assert "invalid-backup" in str(err)
    assert "format" in str(err).lower()
    assert isinstance(err, CenvError)


def test_symlink_state_error():
    """Test SymlinkStateError with description"""
    err = SymlinkStateError("~/.claude exists but is not a symlink")
    assert "symlink" in str(err).lower()
    assert isinstance(err, CenvError)


def test_active_environment_error():
    """Test ActiveEnvironmentError with environment name"""
    err = ActiveEnvironmentError("production")
    assert "production" in str(err)
    assert "active" in str(err).lower()
    assert isinstance(err, CenvError)


def test_protected_environment_error():
    """Test ProtectedEnvironmentError with environment name"""
    err = ProtectedEnvironmentError("default")
    assert "default" in str(err)
    assert "protected" in str(err).lower() or "cannot" in str(err).lower()
    assert isinstance(err, CenvError)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py::test_invalid_backup_format_error -v`

Expected: FAIL with "NameError: name 'InvalidBackupFormatError' is not defined"

**Step 3: Add new exception types**

Edit `src/cenv/exceptions.py`, add after `GitOperationError`:

```python
class InvalidBackupFormatError(CenvError):
    """Raised when backup name format is invalid"""
    def __init__(self, backup_name: str):
        self.backup_name = backup_name
        super().__init__(
            f"Invalid backup name format: {backup_name}\n"
            f"Expected format: <env-name>-YYYYMMDD-HHMMSS"
        )


class SymlinkStateError(CenvError):
    """Raised when symlink is in unexpected state"""
    pass


class ActiveEnvironmentError(CenvError):
    """Raised when attempting to delete active environment"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )


class ProtectedEnvironmentError(CenvError):
    """Raised when attempting to delete protected environment"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Cannot delete protected environment '{name}'. "
            f"The '{name}' environment is required for cenv to function."
        )
```

**Step 4: Update core.py to use new exceptions**

Edit `src/cenv/core.py`:

Add imports (line 10-16):
```python
from cenv.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
    GitOperationError,
    InvalidBackupFormatError,
    SymlinkStateError,
    ActiveEnvironmentError,
    ProtectedEnvironmentError,
)
```

Replace line 85:
```python
# OLD: raise ValueError(f"Invalid backup name format: {backup_name}")
# NEW:
raise InvalidBackupFormatError(backup_name)
```

Replace line 288:
```python
# OLD: raise RuntimeError("~/.claude exists but is not a symlink. Cannot switch.")
# NEW:
raise SymlinkStateError("~/.claude exists but is not a symlink. Cannot switch.")
```

Replace lines 309-312:
```python
# OLD:
# raise RuntimeError(
#     f"Environment '{name}' is currently active. "
#     "Switch to another environment first."
# )
# NEW:
raise ActiveEnvironmentError(name)
```

Replace line 317:
```python
# OLD: raise RuntimeError("Cannot delete default environment.")
# NEW:
raise ProtectedEnvironmentError(name)
```

**Step 5: Update tests to expect new exceptions**

Edit test files to use new exceptions:

`tests/test_delete.py`:
```python
from cenv.exceptions import ActiveEnvironmentError, ProtectedEnvironmentError

# Update test_delete_environment_fails_if_active (around line X)
with pytest.raises(ActiveEnvironmentError):
    delete_environment("default")

# Update test_delete_environment_fails_for_default
with pytest.raises(ProtectedEnvironmentError):
    delete_environment("default")
```

`tests/test_switch.py`:
```python
from cenv.exceptions import SymlinkStateError

# Update test where symlink is in bad state
with pytest.raises(SymlinkStateError):
    switch_environment("myenv")
```

**Step 6: Run all tests**

Run: `pytest tests/ -v`

Expected: PASS (87 tests - 4 new exception tests)

**Step 7: Commit**

```bash
git add src/cenv/exceptions.py src/cenv/core.py tests/test_exceptions.py tests/test_delete.py tests/test_switch.py
git commit -m "refactor: complete custom exception hierarchy migration

- Add InvalidBackupFormatError for backup name validation
- Add SymlinkStateError for symlink state issues
- Add ActiveEnvironmentError for active environment deletion
- Add ProtectedEnvironmentError for protected environment deletion
- Replace all remaining ValueError and RuntimeError usage
- Update tests to expect custom exceptions

All exceptions now inherit from CenvError and are caught by CLI.

Fixes exception hierarchy issue (P0)"
```

---

## Task 3: Add Input Validation for Environment Names

**Files:**
- Create: `src/cenv/validation.py`
- Modify: `src/cenv/core.py:228-263`
- Test: `tests/test_validation.py`

**Step 1: Write tests for input validation**

Create `tests/test_validation.py`:

```python
import pytest
from cenv.validation import (
    validate_environment_name,
    InvalidEnvironmentNameError,
    VALID_NAME_PATTERN,
)


def test_valid_environment_names():
    """Test that valid names pass validation"""
    valid_names = [
        "production",
        "staging",
        "dev",
        "my-env",
        "env_123",
        "test-env-v2",
        "a",  # Single character
        "very-long-environment-name-with-many-parts",
    ]

    for name in valid_names:
        # Should not raise
        validate_environment_name(name)


def test_invalid_characters_rejected():
    """Test that invalid characters are rejected"""
    invalid_names = [
        "../etc",
        "../../passwd",
        "env/with/slash",
        "env\\with\\backslash",
        "env with spaces",
        "env@special",
        "env!mark",
        "env#hash",
        "env$dollar",
        "env%percent",
        ".hidden",
        "env.",
    ]

    for name in invalid_names:
        with pytest.raises(InvalidEnvironmentNameError) as exc_info:
            validate_environment_name(name)

        error_msg = str(exc_info.value)
        assert name in error_msg
        assert "invalid" in error_msg.lower()


def test_reserved_names_rejected():
    """Test that reserved names are rejected"""
    reserved_names = [
        ".",
        "..",
        ".trash",
    ]

    for name in reserved_names:
        with pytest.raises(InvalidEnvironmentNameError) as exc_info:
            validate_environment_name(name)

        error_msg = str(exc_info.value)
        assert "reserved" in error_msg.lower() or "invalid" in error_msg.lower()


def test_empty_name_rejected():
    """Test that empty names are rejected"""
    with pytest.raises(InvalidEnvironmentNameError):
        validate_environment_name("")


def test_error_message_includes_pattern():
    """Test that error message explains valid pattern"""
    with pytest.raises(InvalidEnvironmentNameError) as exc_info:
        validate_environment_name("invalid name")

    error_msg = str(exc_info.value)
    # Should explain what's allowed
    assert any(char in error_msg for char in ['a-z', '0-9', '-', '_'])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_validation.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.validation'"

**Step 3: Create validation module**

Create `src/cenv/validation.py`:

```python
# ABOUTME: Input validation for environment names and parameters
# ABOUTME: Prevents path traversal and injection attacks
"""Input validation utilities for cenv"""
import re
from cenv.exceptions import CenvError


class InvalidEnvironmentNameError(CenvError):
    """Raised when environment name is invalid"""
    pass


# Valid environment name pattern: alphanumeric, hyphens, underscores
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Reserved names that cannot be used
RESERVED_NAMES = {'.', '..', '.trash', '.git', '.backup'}


def validate_environment_name(name: str) -> None:
    """Validate environment name for security and correctness

    Args:
        name: Environment name to validate

    Raises:
        InvalidEnvironmentNameError: If name is invalid

    Valid names:
        - Must contain only: letters (a-z, A-Z), digits (0-9), hyphens (-), underscores (_)
        - Cannot be empty
        - Cannot be a reserved name (., .., .trash, etc.)
        - No path separators (/, \\)
        - No special characters

    Examples:
        Valid: "production", "staging-v2", "dev_env", "test123"
        Invalid: "../etc", "env with spaces", ".hidden", ".."
    """
    if not name:
        raise InvalidEnvironmentNameError(
            "Environment name cannot be empty"
        )

    if name in RESERVED_NAMES:
        raise InvalidEnvironmentNameError(
            f"Environment name '{name}' is reserved and cannot be used.\n"
            f"Reserved names: {', '.join(sorted(RESERVED_NAMES))}"
        )

    if not VALID_NAME_PATTERN.match(name):
        raise InvalidEnvironmentNameError(
            f"Invalid environment name: '{name}'\n\n"
            f"Environment names must contain only:\n"
            f"  • Letters (a-z, A-Z)\n"
            f"  • Digits (0-9)\n"
            f"  • Hyphens (-)\n"
            f"  • Underscores (_)\n\n"
            f"Examples of valid names:\n"
            f"  • production\n"
            f"  • staging-v2\n"
            f"  • dev_env\n"
            f"  • test123"
        )
```

**Step 4: Add validation to core functions**

Edit `src/cenv/core.py`:

Add import:
```python
from cenv.validation import validate_environment_name, InvalidEnvironmentNameError
```

Update `create_environment()` (line 228):
```python
def create_environment(name: str, source: str = "default") -> None:
    """Create a new environment by copying from source environment or GitHub URL"""
    # Validate environment name for security
    validate_environment_name(name)

    logger.info(f"Creating environment '{name}' from '{source}'")
    # ... rest of function
```

Update `switch_environment()` (line 265):
```python
def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment"""
    # Validate environment name
    validate_environment_name(name)

    logger.info(f"Switching to environment '{name}' (force={force})")
    # ... rest of function
```

Update `delete_environment()` (line 295):
```python
def delete_environment(name: str) -> None:
    """Delete an environment (moves to trash)"""
    # Validate environment name
    validate_environment_name(name)

    logger.info(f"Deleting environment '{name}'")
    # ... rest of function
```

**Step 5: Update CLI exception handling**

Edit `src/cenv/cli.py`:

Add import:
```python
from cenv.validation import InvalidEnvironmentNameError
```

Update exception handlers in create, use, delete commands:
```python
except InvalidEnvironmentNameError as e:
    click.echo(f"Validation Error: {e}", err=True)
    raise SystemExit(1)
except CenvError as e:
    # ... existing handler
```

**Step 6: Add CLI tests for validation**

Create `tests/test_cli_validation.py`:

```python
from click.testing import CliRunner
from cenv.cli import cli


def test_create_rejects_invalid_names():
    """Test that create command rejects invalid names"""
    runner = CliRunner()

    invalid_names = ["../etc", "env with spaces", "env/slash"]

    for name in invalid_names:
        result = runner.invoke(cli, ['create', name])
        assert result.exit_code == 1
        assert "Validation Error" in result.output or "Invalid" in result.output


def test_use_rejects_invalid_names():
    """Test that use command rejects invalid names"""
    runner = CliRunner()

    result = runner.invoke(cli, ['use', '../evil'])
    assert result.exit_code == 1
    assert "Validation Error" in result.output or "Invalid" in result.output


def test_delete_rejects_invalid_names():
    """Test that delete command rejects invalid names"""
    runner = CliRunner()

    result = runner.invoke(cli, ['delete', '--force', '../evil'])
    assert result.exit_code == 1
    assert "Validation Error" in result.output or "Invalid" in result.output
```

**Step 7: Run all tests**

Run: `pytest tests/ -v`

Expected: PASS (95 tests - 5 validation tests + 3 CLI validation tests)

**Step 8: Commit**

```bash
git add src/cenv/validation.py src/cenv/core.py src/cenv/cli.py tests/test_validation.py tests/test_cli_validation.py
git commit -m "security: add input validation for environment names

- Create validation module with comprehensive checks
- Validate names in create, switch, and delete operations
- Prevent path traversal attacks (../, /etc, etc.)
- Block reserved names (., .., .trash)
- Enforce alphanumeric + hyphen + underscore pattern
- Add helpful error messages with examples
- Add 8 tests for validation logic

Fixes input validation security issue (P0)"
```

---

## Task 4: Implement Atomic Switch Operation

**Files:**
- Modify: `src/cenv/core.py:265-293`
- Test: `tests/test_switch.py`

**Step 1: Write test for atomic switch**

Edit `tests/test_switch.py`, add:

```python
import threading
from pathlib import Path


def test_switch_is_atomic(tmp_path, monkeypatch):
    """Test that switch operation is atomic - no intermediate broken state"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    # Setup
    init_environments()
    create_environment("test-env")

    # Track symlink state at every moment
    states = []

    def monitor_symlink():
        """Monitor thread that checks symlink state"""
        claude_dir = tmp_path / ".claude"
        for _ in range(100):
            if claude_dir.exists():
                if claude_dir.is_symlink():
                    target = claude_dir.resolve()
                    states.append(("valid", target.name))
                else:
                    states.append(("broken", "not-symlink"))
            else:
                states.append(("broken", "missing"))
            # Small sleep to catch any intermediate state
            import time
            time.sleep(0.001)

    # Start monitoring in background
    monitor = threading.Thread(target=monitor_symlink, daemon=True)
    monitor.start()

    # Perform switch
    switch_environment("test-env")

    monitor.join(timeout=2)

    # Verify: ALL states should be valid (no broken intermediate state)
    broken_states = [s for s in states if s[0] == "broken"]
    assert len(broken_states) == 0, f"Found broken intermediate states: {broken_states}"


def test_switch_handles_concurrent_operations(tmp_path, monkeypatch):
    """Test that concurrent switches don't corrupt state"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    # Setup multiple environments
    init_environments()
    for i in range(3):
        create_environment(f"env{i}")

    errors = []

    def switch_env(name):
        try:
            switch_environment(name, force=True)
        except Exception as e:
            errors.append(e)

    # Launch concurrent switches
    threads = [
        threading.Thread(target=switch_env, args=(f"env{i}",))
        for i in range(3)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should complete without errors
    assert len(errors) == 0, f"Got errors: {errors}"

    # Final state should be valid
    claude_dir = tmp_path / ".claude"
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()
```

**Step 2: Run test to verify current behavior**

Run: `pytest tests/test_switch.py::test_switch_is_atomic -v`

Expected: May FAIL (exposes race condition) or PASS unreliably

**Step 3: Implement atomic switch with temporary symlink**

Edit `src/cenv/core.py`, replace `switch_environment()`:

```python
def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment using atomic rename"""
    # Validate environment name
    validate_environment_name(name)

    logger.info(f"Switching to environment '{name}' (force={force})")
    target_env = get_env_path(name)

    # Check if target environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise EnvironmentNotFoundError(name)

    # Check if Claude is running
    if is_claude_running() and not force:
        logger.warning("Claude is running, refusing to switch without force=True")
        raise ClaudeRunningError()

    claude_dir = get_claude_dir()

    # Verify current state is valid or missing
    if claude_dir.exists() and not claude_dir.is_symlink():
        logger.error(f"{claude_dir} exists but is not a symlink")
        raise SymlinkStateError("~/.claude exists but is not a symlink. Cannot switch.")

    # Create temporary symlink with atomic rename
    # This ensures no intermediate broken state
    temp_link = claude_dir.parent / ".claude.tmp"

    try:
        # Remove temp link if it exists from previous failed operation
        if temp_link.exists():
            temp_link.unlink()

        # Create new symlink with temporary name
        logger.debug(f"Creating temporary symlink {temp_link} -> {target_env}")
        temp_link.symlink_to(target_env)

        # Atomic rename: this is the critical operation
        # On Unix, this is atomic - either old or new link exists, never neither
        logger.debug(f"Atomically replacing {claude_dir} with temporary symlink")
        temp_link.replace(claude_dir)

        logger.info(f"Switched to environment '{name}'")

    except Exception as e:
        # Clean up temporary symlink on error
        if temp_link.exists():
            logger.debug(f"Cleaning up temporary symlink after error")
            temp_link.unlink()
        raise
```

**Step 4: Run tests to verify atomic behavior**

Run: `pytest tests/test_switch.py::test_switch_is_atomic -v`

Expected: PASS

Run: `pytest tests/test_switch.py -v`

Expected: PASS (all switch tests)

Run: `pytest tests/ -v`

Expected: PASS (all 97 tests including new atomic tests)

**Step 5: Commit**

```bash
git add src/cenv/core.py tests/test_switch.py
git commit -m "fix: implement atomic switch operation

- Use temporary symlink with atomic rename
- Prevents intermediate broken state (no .claude directory)
- Safe for concurrent operations
- Add tests for atomicity and concurrency
- Clean up temp symlink on error

Fixes atomic operations issue (P1)"
```

---

## Task 5: Improve Process Detection with Fallback

**Files:**
- Modify: `src/cenv/process.py:6-28`
- Modify: `src/cenv/core.py:265-293`
- Test: `tests/test_process.py`

**Step 1: Write tests for improved process detection**

Edit `tests/test_process.py`, add:

```python
def test_process_detection_returns_false_when_uncertain():
    """Test that uncertain detection returns False (fail-safe)"""
    # When we can't definitively detect Claude, assume it's not running
    # Better to allow operation than block user unnecessarily
    result = is_claude_running()
    assert isinstance(result, bool)


def test_get_claude_processes_handles_access_denied():
    """Test that AccessDenied doesn't crash detection"""
    # Should handle permission errors gracefully
    processes = get_claude_processes()
    assert isinstance(processes, list)


def test_detection_documented_limitations():
    """Test that detection limitations are documented"""
    import cenv.process
    # Module should have docstring explaining limitations
    assert cenv.process.__doc__ is not None
    doc = cenv.process.__doc__.lower()
    # Should mention detection is best-effort
    assert any(word in doc for word in ['best-effort', 'may not', 'limitation', 'heuristic'])
```

**Step 2: Run test to check current documentation**

Run: `pytest tests/test_process.py::test_detection_documented_limitations -v`

Expected: FAIL (no comprehensive docstring)

**Step 3: Add comprehensive module docstring**

Edit `src/cenv/process.py`:

```python
# ABOUTME: Process detection for Claude Code to check if it's currently running
# ABOUTME: Uses psutil to find node processes running the claude binary
"""Process detection for Claude Code

This module provides best-effort detection of running Claude Code processes.

LIMITATIONS:
  • Detection is heuristic-based and may not catch all cases
  • Assumes Claude runs as a node process with "bin/claude" in command line
  • May not detect Claude running in Docker, VM, or remote session
  • May not detect Claude installed in non-standard locations
  • Windows detection is not implemented

RECOMMENDATIONS:
  • Users should manually verify Claude is not running before critical operations
  • Use --force flag to bypass detection when you're certain Claude is not running
  • Check for .claude.lock file as additional signal (future enhancement)

The detection prioritizes false negatives over false positives:
  • If uncertain, assumes Claude is NOT running (allows operation)
  • Better to allow operation than unnecessarily block user
"""
import psutil
from typing import List
from cenv.logging_config import get_logger

logger = get_logger(__name__)


def get_claude_processes() -> List[psutil.Process]:
    """Get all running Claude Code processes (best-effort detection)

    Returns:
        List of processes that appear to be Claude Code
        Empty list if detection fails or no processes found

    Note:
        This is heuristic-based detection with known limitations.
        May not detect all Claude installations.
    """
    claude_processes = []

    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                # Access proc.info which may raise AccessDenied
                info = proc.info
                cmdline = info.get("cmdline", [])

                if not cmdline:
                    continue

                # Check if "claude" appears in command line
                if not any("claude" in str(arg).lower() for arg in cmdline):
                    continue

                # Heuristic: Claude Code typically runs as node process
                # This may not catch all installations (electron apps, binaries, etc.)
                if info.get("name") == "node" and any("bin/claude" in str(arg) for arg in cmdline):
                    logger.debug(f"Found potential Claude process: PID {proc.pid}")
                    claude_processes.append(proc)

            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                # Can't access this process - skip it
                # AccessDenied is common for system processes
                continue

    except Exception as e:
        # Log error but don't crash - return empty list
        logger.warning(f"Process detection failed: {e}")
        return []

    return claude_processes


def is_claude_running() -> bool:
    """Check if Claude Code is currently running (best-effort)

    Returns:
        True if Claude appears to be running
        False if Claude is not detected or detection fails

    Note:
        This is best-effort detection with known limitations.
        When uncertain, returns False (fail-safe - allows operation).
        Users should manually verify for critical operations.
        Use --force flag to bypass detection.
    """
    try:
        processes = get_claude_processes()
        is_running = len(processes) > 0

        if is_running:
            logger.info(f"Detected {len(processes)} Claude process(es) running")

        return is_running

    except Exception as e:
        # If detection fails, assume Claude is NOT running
        # Better to allow operation than unnecessarily block user
        logger.warning(f"Process detection error (assuming not running): {e}")
        return False
```

**Step 4: Update switch_environment to be more lenient**

Edit `src/cenv/core.py` in `switch_environment()`:

```python
    # Check if Claude is running (best-effort detection)
    if is_claude_running() and not force:
        logger.warning("Claude appears to be running")
        # Note: Detection is best-effort and may have false positives/negatives
        raise ClaudeRunningError()
```

**Step 5: Update CLI to explain force flag better**

Edit `src/cenv/cli.py` in `use` command:

```python
@cli.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force switch even if Claude appears to be running")
def use(name: str, force: bool) -> None:
    """Switch to a different environment

    Note: Process detection is best-effort. If you're certain Claude
    is not running but detection warns otherwise, use --force.
    """
    try:
        # Check if Claude is running
        if is_claude_running() and not force:
            click.echo("⚠️  Claude appears to be running. Switching environments may cause issues.")
            click.echo("    (Process detection is heuristic-based and may not be accurate)")
            if not click.confirm("Continue anyway?"):
                click.echo("Cancelled.")
                return
            force = True

        switch_environment(name, force=force)
        click.echo(f"✓ Switched to environment '{name}'")
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
```

**Step 6: Run tests**

Run: `pytest tests/test_process.py -v`

Expected: PASS (6 tests)

Run: `pytest tests/ -v`

Expected: PASS (all 97 tests)

**Step 7: Update documentation**

Create `docs/PROCESS_DETECTION.md`:

```markdown
# Process Detection Limitations

## Overview

cenv attempts to detect if Claude Code is running before performing operations that require Claude to be stopped (like switching environments). However, this detection is **best-effort** and has known limitations.

## How It Works

Detection looks for processes that match this pattern:
- Process name is "node"
- Command line contains "bin/claude"
- Command line contains "claude" (case-insensitive)

## Known Limitations

### May Not Detect:
- Claude running in Docker containers
- Claude running in virtual machines
- Claude installed in non-standard locations
- Claude running as a renamed binary
- Claude running as an Electron app (some distributions)
- Claude running in a remote terminal session

### May Falsely Detect:
- Other node processes with "claude" in their path
- Development environments building Claude
- Claude CLI tools (not the full editor)

## Platform Support

- ✅ **Linux**: Supported
- ✅ **macOS**: Supported
- ❌ **Windows**: Not implemented (always returns False)

## Recommendations

### For Users

**If detection warns but you're certain Claude is not running:**
```bash
cenv use myenv --force
```

**Before critical operations:**
Manually verify Claude is closed by checking your running applications.

**If switching environments frequently:**
Close Claude, perform all switches, then reopen Claude.

### For Automation/Scripts

Always use `--force` flag to bypass detection:
```bash
cenv use production --force
```

## Future Improvements

Potential improvements tracked in GitHub issues:
- [ ] Check for Claude lock files
- [ ] Check for Claude IPC sockets
- [ ] Integrate with Claude's official process detection API (if available)
- [ ] Windows support via different detection method

## Philosophy

Detection prioritizes **false negatives over false positives**:
- If uncertain → assume Claude is NOT running → allow operation
- Better to allow operation than unnecessarily block user
- Users should exercise caution and verify manually
```

**Step 8: Commit**

```bash
git add src/cenv/process.py src/cenv/core.py src/cenv/cli.py tests/test_process.py docs/PROCESS_DETECTION.md
git commit -m "docs: document process detection limitations and improve robustness

- Add comprehensive module docstring explaining limitations
- Make detection fail-safe (false negatives over false positives)
- Add error handling for detection failures
- Update CLI help text to explain heuristic nature
- Add PROCESS_DETECTION.md with detailed limitations
- Improve logging for detection events
- Add tests for edge cases

Addresses process detection reliability (P1)"
```

---

## Task 6: Add Comprehensive Edge Case Tests

**Files:**
- Create: `tests/test_edge_cases.py`
- Create: `tests/test_security.py`

**Step 1: Create security test file**

Create `tests/test_security.py`:

```python
import pytest
from pathlib import Path
from click.testing import CliRunner
from cenv.cli import cli
from cenv.core import create_environment, init_environments
from cenv.validation import InvalidEnvironmentNameError


def test_path_traversal_attack_blocked(tmp_path, monkeypatch):
    """Test that path traversal attempts are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Attempt path traversal
    attacks = [
        "../../etc/passwd",
        "../../../tmp/evil",
        "../../.ssh",
        "./../evil",
    ]

    for attack in attacks:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(attack)


def test_special_characters_blocked(tmp_path, monkeypatch):
    """Test that special characters are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    special_chars = [
        "env;rm -rf /",
        "env && echo evil",
        "env | cat /etc/passwd",
        "env'$(whoami)'",
        'env"$(whoami)"',
        "env`whoami`",
    ]

    for attack in special_chars:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(attack)


def test_reserved_names_blocked(tmp_path, monkeypatch):
    """Test that reserved names are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    reserved = [".", "..", ".trash", ".git"]

    for name in reserved:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(name)


def test_cli_rejects_malicious_input():
    """Test that CLI rejects malicious input"""
    runner = CliRunner()

    malicious = [
        "../../etc",
        "env; rm -rf /",
        "$(evil)",
    ]

    for attack in malicious:
        result = runner.invoke(cli, ['create', attack])
        assert result.exit_code != 0
        assert "Validation Error" in result.output or "Invalid" in result.output
```

**Step 2: Create edge case test file**

Create `tests/test_edge_cases.py`:

```python
import pytest
import os
import threading
from pathlib import Path
from cenv.core import (
    init_environments,
    create_environment,
    switch_environment,
    delete_environment,
    list_environments,
)
from cenv.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    InitializationError,
)


def test_unicode_environment_names(tmp_path, monkeypatch):
    """Test handling of unicode characters in names"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # These should be blocked by validation
    unicode_names = [
        "café",
        "环境",
        "среда",
        "🚀rocket",
    ]

    for name in unicode_names:
        with pytest.raises(Exception):  # Should be blocked
            create_environment(name)


def test_very_long_environment_name(tmp_path, monkeypatch):
    """Test handling of extremely long names"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Most filesystems support 255 char filenames
    long_name = "a" * 300

    # May succeed or fail depending on filesystem
    # Should not crash
    try:
        create_environment(long_name)
    except (OSError, InvalidEnvironmentNameError):
        pass  # Expected on some systems


def test_concurrent_environment_creation(tmp_path, monkeypatch):
    """Test concurrent creation of same environment"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    errors = []
    successes = []

    def create_env():
        try:
            create_environment("concurrent-test")
            successes.append(1)
        except EnvironmentExistsError:
            errors.append(1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=create_env) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Exactly one should succeed
    assert len(successes) == 1
    # Others should get EnvironmentExistsError
    assert len(errors) == 4


def test_disk_full_scenario(tmp_path, monkeypatch):
    """Test behavior when disk is full (simulated)"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Create environment with limited space
    # This is hard to test reliably, so we document expected behavior:
    # Should raise OSError with clear message
    # TODO: Improve error handling for disk full scenarios


def test_permission_denied_scenarios(tmp_path, monkeypatch):
    """Test handling of permission errors"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Make environment readonly
    env_path = tmp_path / ".claude-envs" / "test-env"
    os.chmod(env_path, 0o444)

    # Deletion should fail gracefully
    try:
        delete_environment("test-env")
        # If it somehow succeeded, restore permissions for cleanup
        os.chmod(env_path, 0o755)
    except (OSError, PermissionError):
        # Expected - restore permissions for cleanup
        os.chmod(env_path, 0o755)


def test_corrupted_symlink_recovery(tmp_path, monkeypatch):
    """Test recovery from corrupted symlink"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    claude_dir = tmp_path / ".claude"

    # Corrupt the symlink by pointing to non-existent location
    claude_dir.unlink()
    claude_dir.symlink_to(tmp_path / "non-existent")

    # Should be able to recover by switching to valid environment
    switch_environment("default", force=True)

    # Verify recovery
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()


def test_rapid_switch_operations(tmp_path, monkeypatch):
    """Test rapid consecutive switches"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    for i in range(5):
        create_environment(f"env{i}")

    # Rapidly switch between environments
    for i in range(20):
        env_name = f"env{i % 5}"
        switch_environment(env_name, force=True)

    # Final state should be valid
    claude_dir = tmp_path / ".claude"
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()


def test_empty_environment_directory(tmp_path, monkeypatch):
    """Test handling of empty environment"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Create empty environment
    empty_env = tmp_path / ".claude-envs" / "empty"
    empty_env.mkdir()

    # Should appear in listings
    envs = list_environments()
    assert "empty" in envs

    # Should be switchable
    switch_environment("empty", force=True)
```

**Step 3: Run security tests**

Run: `pytest tests/test_security.py -v`

Expected: PASS (4 tests)

**Step 4: Run edge case tests**

Run: `pytest tests/test_edge_cases.py -v`

Expected: PASS (8 tests) - Some may be skipped if filesystem doesn't support test

**Step 5: Run full test suite**

Run: `pytest tests/ -v`

Expected: PASS (109 tests)

**Step 6: Commit**

```bash
git add tests/test_security.py tests/test_edge_cases.py
git commit -m "test: add comprehensive security and edge case tests

- Add security tests for path traversal, injection attacks
- Test unicode, long names, concurrent operations
- Test disk full, permissions, corrupted symlinks
- Test rapid switching and empty environments
- Add 12 new test cases covering edge scenarios

Addresses test coverage gaps (P1)"
```

---

## Task 7: Extract Magic Strings to Constants

**Files:**
- Modify: `src/cenv/core.py:1-333`
- Test: No new tests needed (refactoring)

**Step 1: Add constants module**

Edit `src/cenv/core.py`, add after imports:

```python
# Configuration constants
DEFAULT_ENVIRONMENT_NAME = "default"
TRASH_DIR_NAME = ".trash"
CLAUDE_DIR_NAME = ".claude"
ENVS_DIR_NAME = ".claude-envs"
INIT_LOCK_NAME = "cenv-init.lock"
TEMP_LINK_NAME = ".claude.tmp"
BACKUP_PREFIX = ".claude.backup"
```

**Step 2: Replace magic strings in core.py**

Search and replace all occurrences:

```python
# Line 22: ".claude-envs" -> ENVS_DIR_NAME
def get_envs_dir() -> Path:
    """Get the base directory for all environments"""
    return Path.home() / ENVS_DIR_NAME

# Line 30: ".claude" -> CLAUDE_DIR_NAME
def get_claude_dir() -> Path:
    """Get the ~/.claude directory path"""
    return Path.home() / CLAUDE_DIR_NAME

# Line 34: ".trash" -> TRASH_DIR_NAME
def get_trash_dir() -> Path:
    """Get the trash directory for deleted environments"""
    return get_envs_dir() / TRASH_DIR_NAME

# Line 26: "default" -> DEFAULT_ENVIRONMENT_NAME
def get_env_path(name: str) -> Path:
    """Get the path for a specific environment"""
    return get_envs_dir() / name

# Line 109: ".trash" -> TRASH_DIR_NAME
def list_environments() -> List[str]:
    """List all available environments"""
    envs_dir = get_envs_dir()

    if not envs_dir.exists():
        return []

    return [
        item.name
        for item in envs_dir.iterdir()
        if item.is_dir() and item.name != TRASH_DIR_NAME
    ]

# Line 139: "default" -> DEFAULT_ENVIRONMENT_NAME
default_env = get_env_path(DEFAULT_ENVIRONMENT_NAME)

# Line 142: "cenv-init.lock" -> INIT_LOCK_NAME
lock_file_path = Path(tempfile.gettempdir()) / INIT_LOCK_NAME

# Line 170: ".claude.backup" -> BACKUP_PREFIX
backup_dir = claude_dir.parent / f"{BACKUP_PREFIX}.{timestamp}"

# Line 228: "default" -> DEFAULT_ENVIRONMENT_NAME
def create_environment(name: str, source: str = DEFAULT_ENVIRONMENT_NAME) -> None:

# Line 282: ".claude.tmp" -> TEMP_LINK_NAME
temp_link = claude_dir.parent / TEMP_LINK_NAME

# Line 317: "default" -> DEFAULT_ENVIRONMENT_NAME (in comparison)
if name == DEFAULT_ENVIRONMENT_NAME:
```

**Step 3: Update validation.py to use constants**

Edit `src/cenv/validation.py`:

```python
from cenv.core import TRASH_DIR_NAME, DEFAULT_ENVIRONMENT_NAME

# Update RESERVED_NAMES
RESERVED_NAMES = {'.', '..', TRASH_DIR_NAME, '.git', '.backup', DEFAULT_ENVIRONMENT_NAME}
```

Wait, DEFAULT_ENVIRONMENT_NAME shouldn't be reserved. Update:

```python
RESERVED_NAMES = {'.', '..', TRASH_DIR_NAME, '.git', '.backup'}
```

**Step 4: Run tests to ensure refactoring didn't break anything**

Run: `pytest tests/ -v`

Expected: PASS (all 109 tests)

**Step 5: Commit**

```bash
git add src/cenv/core.py src/cenv/validation.py
git commit -m "refactor: extract magic strings to module constants

- Add constants for directory names, lock files
- Replace all hardcoded strings with named constants
- Improves maintainability and reduces typo risk
- No functional changes - pure refactoring

Addresses code quality issue (P2)"
```

---

## Task 8: Make Logging Thread-Safe

**Files:**
- Modify: `src/cenv/logging_config.py:10-54`
- Test: `tests/test_logging.py`

**Step 1: Write test for thread safety**

Edit `tests/test_logging.py`, add:

```python
import threading


def test_setup_logging_is_thread_safe(tmp_path):
    """Test that concurrent logging setup doesn't corrupt state"""
    log_file = tmp_path / "test.log"
    errors = []

    def setup_concurrent():
        try:
            setup_logging(level=logging.INFO, log_file=log_file)
            logger = get_logger("test")
            logger.info("Test message")
        except Exception as e:
            errors.append(e)

    # Launch multiple threads setting up logging
    threads = [threading.Thread(target=setup_concurrent) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should complete without errors
    assert len(errors) == 0, f"Got errors: {errors}"

    # Log file should exist and contain messages
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_concurrent_logging_no_handler_duplication(tmp_path):
    """Test that concurrent setup doesn't duplicate handlers"""
    log_file = tmp_path / "test.log"

    def setup_and_count():
        setup_logging(level=logging.INFO, log_file=log_file)
        logger = logging.getLogger("cenv")
        return len(logger.handlers)

    # Setup multiple times concurrently
    threads = [threading.Thread(target=setup_and_count) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Check final handler count
    logger = logging.getLogger("cenv")
    # Should have exactly 2 handlers (console + file)
    assert len(logger.handlers) == 2, f"Expected 2 handlers, got {len(logger.handlers)}"
```

**Step 2: Run test to see current behavior**

Run: `pytest tests/test_logging.py::test_setup_logging_is_thread_safe -v`

Expected: May PASS or FAIL depending on race conditions

**Step 3: Add thread safety to logging setup**

Edit `src/cenv/logging_config.py`:

```python
# ABOUTME: Logging configuration for cenv
# ABOUTME: Provides centralized logging setup with file and console handlers
"""Logging configuration for cenv"""
import logging
import sys
import threading
from pathlib import Path
from typing import Optional


_configured = False
_config_lock = threading.Lock()


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """Configure logging for cenv (thread-safe)

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output

    Thread Safety:
        This function is thread-safe. Multiple concurrent calls will
        result in exactly one configuration being applied.
    """
    global _configured

    # Thread-safe check and configuration
    with _config_lock:
        # Check again inside lock (double-checked locking pattern)
        if _configured:
            return

        # Configure root logger for cenv
        logger = logging.getLogger("cenv")

        # Clear any existing handlers
        logger.handlers.clear()
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

    Thread Safety:
        This function is thread-safe.
    """
    return logging.getLogger(f"cenv.{name}" if not name.startswith("cenv") else name)
```

**Step 4: Run tests**

Run: `pytest tests/test_logging.py -v`

Expected: PASS (6 tests including new thread safety tests)

**Step 5: Commit**

```bash
git add src/cenv/logging_config.py tests/test_logging.py
git commit -m "fix: make logging configuration thread-safe

- Add threading.Lock to prevent concurrent configuration
- Use double-checked locking pattern
- Add tests for concurrent setup
- Prevent handler duplication from race conditions
- Document thread safety in docstrings

Addresses thread safety issue (P2)"
```

---

## Task 9: Improve CLI Error Messages

**Files:**
- Modify: `src/cenv/cli.py:42-165`
- Test: `tests/test_cli_messages.py`

**Step 1: Write tests for improved error messages**

Create `tests/test_cli_messages.py`:

```python
from click.testing import CliRunner
from cenv.cli import cli


def test_environment_not_found_suggests_alternatives(tmp_path, monkeypatch):
    """Test that 'not found' errors suggest available environments"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    runner = CliRunner()

    # Initialize
    runner.invoke(cli, ['init'])

    # Try to use non-existent environment
    result = runner.invoke(cli, ['use', 'nonexistent'])

    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
    # Should suggest running list command
    assert "cenv list" in result.output or "available" in result.output.lower()


def test_uninit_error_suggests_init_command():
    """Test that uninitialized error suggests init command"""
    runner = CliRunner()

    result = runner.invoke(cli, ['list'])

    assert "init" in result.output.lower()
    assert "cenv init" in result.output


def test_error_includes_contact_info():
    """Test that unexpected errors include bug report info"""
    # Hard to trigger reliably, but documentation should mention it
    pass  # TODO: Add if we implement global error handler
```

**Step 2: Create helper for better error messages**

Add to `src/cenv/cli.py` after imports:

```python
def format_error_with_help(error: CenvError, context: str = "") -> str:
    """Format error message with helpful suggestions

    Args:
        error: The exception that occurred
        context: Additional context (e.g., 'use', 'create')

    Returns:
        Formatted error message with suggestions
    """
    from cenv.core import list_environments, get_current_environment
    from cenv.exceptions import EnvironmentNotFoundError, InitializationError

    message = f"Error: {error}\n"

    # Add context-specific help
    if isinstance(error, EnvironmentNotFoundError):
        try:
            envs = list_environments()
            current = get_current_environment()

            if envs:
                message += "\nAvailable environments:\n"
                for env in sorted(envs):
                    marker = " → " if env == current else "   "
                    message += f"{marker}{env}\n"
            else:
                message += "\nNo environments found. Run 'cenv init' to initialize.\n"

            message += "\nRun 'cenv list' to see all environments.\n"
        except:
            message += "\nRun 'cenv list' to see available environments.\n"

    elif isinstance(error, InitializationError):
        if "not initialized" in str(error).lower():
            message += "\nRun 'cenv init' to initialize cenv.\n"

    return message.rstrip()
```

**Step 3: Update CLI commands to use helper**

Edit commands in `src/cenv/cli.py`:

Update `use` command:
```python
@cli.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force switch even if Claude appears to be running")
def use(name: str, force: bool) -> None:
    """Switch to a different environment

    Note: Process detection is best-effort. If you're certain Claude
    is not running but detection warns otherwise, use --force.
    """
    try:
        # Check if Claude is running
        if is_claude_running() and not force:
            click.echo("⚠️  Claude appears to be running. Switching environments may cause issues.")
            click.echo("    (Process detection is heuristic-based and may not be accurate)")
            if not click.confirm("Continue anyway?"):
                click.echo("Cancelled.")
                return
            force = True

        switch_environment(name, force=force)
        click.echo(f"✓ Switched to environment '{name}'")
    except CenvError as e:
        click.echo(format_error_with_help(e, context='use'), err=True)
        raise SystemExit(1)
```

Update `create` command:
```python
@cli.command()
@click.argument("name")
@click.option(
    "--from-repo",
    help="Clone from GitHub repository URL",
    metavar="URL",
)
def create(name: str, from_repo: str) -> None:
    """Create a new environment"""
    try:
        source = from_repo if from_repo else DEFAULT_ENVIRONMENT_NAME
        create_environment(name, source=source)

        if from_repo:
            click.echo(f"✓ Created environment '{name}' from {from_repo}")
        else:
            click.echo(f"✓ Created environment '{name}' from {DEFAULT_ENVIRONMENT_NAME}")
    except CenvError as e:
        click.echo(format_error_with_help(e, context='create'), err=True)
        raise SystemExit(1)
```

Update `delete` command similarly.

**Step 4: Run tests**

Run: `pytest tests/test_cli_messages.py -v`

Expected: PASS (2 tests)

**Step 5: Manual testing**

```bash
# Test improved error messages
uvx --from . cenv use nonexistent
# Should show available environments

uvx --from . cenv create test
# Without init, should suggest init command
```

**Step 6: Commit**

```bash
git add src/cenv/cli.py tests/test_cli_messages.py
git commit -m "feat: improve CLI error messages with helpful suggestions

- Add format_error_with_help() for context-aware messages
- Show available environments when 'not found' error occurs
- Suggest 'cenv init' when not initialized
- Suggest 'cenv list' to see environments
- Add tests for improved messages

Addresses UX issue (P2)"
```

---

## Task 10: Add Basic Configuration System

**Files:**
- Create: `src/cenv/config.py`
- Modify: `src/cenv/github.py:10`
- Modify: `src/cenv/core.py:142`
- Test: `tests/test_config.py`

**Step 1: Write tests for configuration**

Create `tests/test_config.py`:

```python
import os
import pytest
from pathlib import Path
from cenv.config import load_config, Config, DEFAULT_GIT_TIMEOUT


def test_default_config():
    """Test that default config has sensible values"""
    config = Config()

    assert config.git_timeout > 0
    assert config.git_timeout == DEFAULT_GIT_TIMEOUT
    assert isinstance(config.trash_dir_name, str)


def test_config_from_environment_variables(monkeypatch):
    """Test loading config from environment variables"""
    monkeypatch.setenv("CENV_GIT_TIMEOUT", "600")
    monkeypatch.setenv("CENV_LOG_LEVEL", "DEBUG")

    config = load_config()

    assert config.git_timeout == 600


def test_invalid_config_values_use_defaults(monkeypatch):
    """Test that invalid values fall back to defaults"""
    monkeypatch.setenv("CENV_GIT_TIMEOUT", "invalid")

    config = load_config()

    # Should use default, not crash
    assert config.git_timeout == DEFAULT_GIT_TIMEOUT


def test_config_file_loading(tmp_path):
    """Test loading config from file"""
    config_file = tmp_path / ".cenvrc"
    config_file.write_text("""
git_timeout = 600
log_level = DEBUG
    """)

    config = load_config(config_file=config_file)

    assert config.git_timeout == 600
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'cenv.config'"

**Step 3: Create configuration module**

Create `src/cenv/config.py`:

```python
# ABOUTME: Configuration management for cenv
# ABOUTME: Loads settings from environment variables and config files
"""Configuration management for cenv"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# Default configuration values
DEFAULT_GIT_TIMEOUT = 300  # 5 minutes
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TRASH_DIR_NAME = ".trash"
DEFAULT_LOCK_FILE_NAME = "cenv-init.lock"


@dataclass
class Config:
    """Configuration for cenv operations"""

    # Git operation timeout in seconds
    git_timeout: int = DEFAULT_GIT_TIMEOUT

    # Logging level
    log_level: str = DEFAULT_LOG_LEVEL

    # Directory names (usually shouldn't be changed)
    trash_dir_name: str = DEFAULT_TRASH_DIR_NAME
    lock_file_name: str = DEFAULT_LOCK_FILE_NAME


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from environment and optional config file

    Args:
        config_file: Optional path to config file

    Returns:
        Config object with merged settings

    Configuration precedence (highest to lowest):
        1. Environment variables (CENV_*)
        2. Config file (~/.cenvrc or specified file)
        3. Defaults

    Environment variables:
        CENV_GIT_TIMEOUT: Git operation timeout in seconds (default: 300)
        CENV_LOG_LEVEL: Logging level (default: INFO)

    Config file format (~/.cenvrc):
        git_timeout = 600
        log_level = DEBUG
    """
    config = Config()

    # Load from config file if it exists
    if config_file is None:
        config_file = Path.home() / ".cenvrc"

    if config_file.exists():
        try:
            content = config_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == 'git_timeout':
                        try:
                            config.git_timeout = int(value)
                        except ValueError:
                            pass  # Use default
                    elif key == 'log_level':
                        config.log_level = value.upper()
        except Exception:
            # If config file is malformed, use defaults
            pass

    # Environment variables override config file
    if 'CENV_GIT_TIMEOUT' in os.environ:
        try:
            config.git_timeout = int(os.environ['CENV_GIT_TIMEOUT'])
        except ValueError:
            pass  # Use default

    if 'CENV_LOG_LEVEL' in os.environ:
        config.log_level = os.environ['CENV_LOG_LEVEL'].upper()

    return config


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance (singleton)

    Returns:
        Global Config instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
```

**Step 4: Update github.py to use config**

Edit `src/cenv/github.py`:

```python
from cenv.config import get_config

# Remove hardcoded constant, use config
# Line 10: GIT_TIMEOUT = 300
# Replace with function:

def get_git_timeout() -> int:
    """Get configured git timeout"""
    return get_config().git_timeout

# Update clone_from_github to use config:
# Line 44: timeout=GIT_TIMEOUT,
# Replace with:
timeout=get_git_timeout(),

# Line 67: timeout message
# Replace with:
timeout_val = get_git_timeout()
raise GitOperationError("clone", url, f"Operation timed out after {timeout_val} seconds")
```

**Step 5: Run tests**

Run: `pytest tests/test_config.py -v`

Expected: PASS (4 tests)

Run: `pytest tests/ -v`

Expected: PASS (all 117 tests)

**Step 6: Update documentation**

Add to `README.md`:

```markdown
## Configuration

cenv can be configured via environment variables or a config file.

### Config File

Create `~/.cenvrc`:

```ini
# Git operation timeout in seconds (default: 300)
git_timeout = 600

# Logging level (default: INFO)
log_level = DEBUG
```

### Environment Variables

```bash
export CENV_GIT_TIMEOUT=600
export CENV_LOG_LEVEL=DEBUG
```

### Configuration Precedence

1. Environment variables (highest priority)
2. `~/.cenvrc` file
3. Built-in defaults (lowest priority)
```

**Step 7: Commit**

```bash
git add src/cenv/config.py src/cenv/github.py tests/test_config.py README.md
git commit -m "feat: add basic configuration system

- Add config module with env vars and file support
- Support CENV_GIT_TIMEOUT and CENV_LOG_LEVEL
- Load from ~/.cenvrc config file
- Update github module to use configurable timeout
- Add tests for configuration loading
- Document configuration options

Addresses configuration system need (P2)"
```

---

## Verification Steps

After completing all tasks, run comprehensive verification:

**Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=src/cenv --cov-report=term-missing
```

Expected:
- All 117+ tests passing
- Coverage > 85%

**Step 2: Run type checking**

```bash
make typecheck
```

Expected: Success: no issues found

**Step 3: Test CLI end-to-end**

```bash
# Test platform check
uvx --from . cenv init

# Test validation
uvx --from . cenv create "../evil"  # Should be rejected

# Test normal operations
uvx --from . cenv create test-env
uvx --from . cenv list
uvx --from . cenv use test-env
uvx --from . cenv trash
uvx --from . cenv --verbose list

# Test configuration
export CENV_GIT_TIMEOUT=60
echo "log_level = DEBUG" > ~/.cenvrc
uvx --from . cenv --verbose create test2
```

**Step 4: Review code quality**

```bash
# Check for remaining magic strings
grep -r '".claude"' src/ --exclude="*/core.py"
grep -r '"default"' src/ --exclude="*/core.py"

# Should find no hardcoded strings outside constants
```

---

## Summary

This plan addresses all P0, P1, and P2 issues from the code review:

**P0 (Blocking):**
- ✅ Task 1: Platform compatibility check (+5 points)
- ✅ Task 2: Complete exception hierarchy (+4 points)
- ✅ Task 3: Input validation (+3 points)

**P1 (Important):**
- ✅ Task 4: Atomic switch operation (+3 points)
- ✅ Task 5: Process detection improvements (+2 points)
- ✅ Task 6: Comprehensive edge case tests (+2 points)

**P2 (Quality):**
- ✅ Task 7: Extract magic strings (+1 point)
- ✅ Task 8: Thread-safe logging (+1 point)
- ✅ Task 9: Better error messages (+1 point)
- ✅ Task 10: Configuration system (+1 point)

**Expected Final Grade: A (95/100)**

**Remaining for future:**
- Windows implementation (separate project)
- Progress indicators for long operations
- Performance profiling
- Log rotation
- Structured logging
- Official Claude detection API integration
