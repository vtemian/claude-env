# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical and important issues from code review to achieve A-grade (95/100)

**Architecture:** Add explicit API exports, fix thread safety, improve error handling, add project infrastructure, refactor large modules

**Tech Stack:** Python 3.10+, mypy, pytest, GitHub Actions, pre-commit hooks

**Current Grade:** B+ (87/100)
**Target Grade:** A (95/100)
**Points to Recover:** 8 points

---

## Task 1: Fix Type Safety Violation - Add __all__ Exports

**Priority:** P0 (Critical) - Blocks mypy strict mode
**Impact:** +1 point
**Files:**
- Create: `tests/test_api_exports.py`
- Modify: `src/cenv/platform_utils.py`
- Modify: `src/cenv/validation.py`
- Modify: `src/cenv/exceptions.py`
- Modify: `src/cenv/config.py`
- Modify: `src/cenv/logging_config.py`
- Modify: `src/cenv/process.py`
- Modify: `src/cenv/github.py`
- Modify: `src/cenv/core.py`
- Modify: `src/cenv/cli.py`

### Step 1: Write test to enforce __all__ presence

Create `tests/test_api_exports.py`:

```python
"""Test that all modules define explicit public APIs"""
import importlib
import pkgutil
from pathlib import Path


def test_all_modules_have_explicit_exports():
    """Test that all modules define __all__"""
    src_dir = Path(__file__).parent.parent / "src" / "cenv"

    modules_without_all = []

    for module_info in pkgutil.iter_modules([str(src_dir)]):
        if module_info.name == "__init__":
            continue

        module = importlib.import_module(f"cenv.{module_info.name}")

        if not hasattr(module, "__all__"):
            modules_without_all.append(module_info.name)

    assert not modules_without_all, (
        f"Modules without __all__: {', '.join(modules_without_all)}\n"
        f"All public modules must define __all__ for explicit API"
    )


def test_all_exports_are_valid():
    """Test that __all__ only lists items that exist"""
    src_dir = Path(__file__).parent.parent / "src" / "cenv"

    errors = []

    for module_info in pkgutil.iter_modules([str(src_dir)]):
        if module_info.name == "__init__":
            continue

        module = importlib.import_module(f"cenv.{module_info.name}")

        if hasattr(module, "__all__"):
            for name in module.__all__:
                if not hasattr(module, name):
                    errors.append(f"{module_info.name}.__all__ lists '{name}' but it doesn't exist")

    assert not errors, "\n".join(errors)
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_api_exports.py::test_all_modules_have_explicit_exports -v`

Expected: FAIL - "Modules without __all__: platform_utils, validation, exceptions, ..."

### Step 3: Add __all__ to platform_utils.py

Edit `src/cenv/platform_utils.py` - add after imports:

```python
__all__ = [
    'check_platform_compatibility',
    'PlatformNotSupportedError',
]
```

### Step 4: Add __all__ to validation.py

Edit `src/cenv/validation.py` - add after imports:

```python
__all__ = [
    'validate_environment_name',
    'InvalidEnvironmentNameError',
    'VALID_NAME_PATTERN',
    'RESERVED_NAMES',
]
```

### Step 5: Add __all__ to exceptions.py

Edit `src/cenv/exceptions.py` - add after docstring:

```python
__all__ = [
    'CenvError',
    'EnvironmentNotFoundError',
    'EnvironmentExistsError',
    'ClaudeRunningError',
    'InitializationError',
    'GitOperationError',
    'PlatformNotSupportedError',
    'InvalidBackupFormatError',
    'SymlinkStateError',
    'ActiveEnvironmentError',
    'ProtectedEnvironmentError',
    'InvalidEnvironmentNameError',
]
```

### Step 6: Add __all__ to config.py

Edit `src/cenv/config.py` - add after imports:

```python
__all__ = [
    'Config',
    'load_config',
    'get_config',
]
```

### Step 7: Add __all__ to logging_config.py

Edit `src/cenv/logging_config.py` - add after imports:

```python
__all__ = [
    'setup_logging',
    'get_logger',
    'reset_logging_config',
]
```

### Step 8: Add __all__ to process.py

Edit `src/cenv/process.py` - add after imports:

```python
__all__ = [
    'is_claude_running',
    'get_claude_processes',
]
```

### Step 9: Add __all__ to github.py

Edit `src/cenv/github.py` - add after imports:

```python
__all__ = [
    'is_valid_github_url',
    'clone_from_github',
    'get_git_timeout',
]
```

### Step 10: Add __all__ to core.py

Edit `src/cenv/core.py` - add after constants:

```python
__all__ = [
    # Path utilities
    'get_envs_dir',
    'get_env_path',
    'get_claude_dir',
    'get_trash_dir',

    # Environment management
    'list_environments',
    'get_current_environment',
    'environment_exists',

    # Operations
    'init_environments',
    'create_environment',
    'switch_environment',
    'delete_environment',

    # Trash management
    'list_trash',
    'restore_from_trash',

    # Constants
    'ENVS_DIR_NAME',
    'CLAUDE_DIR_NAME',
    'DEFAULT_ENV_NAME',
    'TRASH_DIR_NAME',
]
```

### Step 11: Add __all__ to cli.py

Edit `src/cenv/cli.py` - add after imports:

```python
__all__ = ['cli']
```

### Step 12: Run test to verify it passes

Run: `pytest tests/test_api_exports.py -v`

Expected: PASS (2 tests)

### Step 13: Run mypy to verify type safety

Run: `mypy src/cenv --strict`

Expected: Success! (no errors)

### Step 14: Commit

```bash
git add tests/test_api_exports.py src/cenv/*.py
git commit -m "fix: add explicit __all__ exports to all modules

- Define public API for each module
- Fix mypy strict type checking error
- Add tests to enforce __all__ presence
- Improve discoverability of public API

Fixes: Module does not explicitly export attribute"
```

---

## Task 2: Fix Thread-Unsafe Config Singleton

**Priority:** P0 (Critical) - Race condition
**Impact:** +1 point
**Files:**
- Modify: `src/cenv/config.py:97-111`
- Modify: `tests/test_config.py`

### Step 1: Write test for thread safety

Add to `tests/test_config.py`:

```python
import threading
from cenv.config import get_config


def test_get_config_is_thread_safe():
    """Test that concurrent get_config calls don't create multiple instances"""
    # Reset config for this test
    import cenv.config
    cenv.config._config = None

    configs = []

    def get_and_store():
        config = get_config()
        configs.append(id(config))

    # Launch 10 concurrent threads
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=get_and_store)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # All threads should get the SAME instance (same id)
    assert len(set(configs)) == 1, (
        f"Expected singleton, got {len(set(configs))} different instances"
    )


def test_concurrent_config_loading():
    """Test that concurrent config loading doesn't cause errors"""
    import cenv.config
    cenv.config._config = None

    errors = []

    def load_config_safely():
        try:
            config = get_config()
            assert config.git_timeout == 300
        except Exception as e:
            errors.append(str(e))

    threads = []
    for _ in range(20):
        thread = threading.Thread(target=load_config_safely)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors, f"Config loading errors: {errors}"
```

### Step 2: Run test to see timing-dependent behavior

Run: `pytest tests/test_config.py::test_get_config_is_thread_safe -v -s`

Expected: May pass or fail (race condition is non-deterministic)

### Step 3: Add thread safety to config.py

Edit `src/cenv/config.py` - add import at top:

```python
import threading
```

Edit `src/cenv/config.py` - replace lines 97-111:

```python
# Global config instance (lazy-loaded with thread safety)
_config: Optional[Config] = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """Get global config instance (thread-safe singleton)

    Returns:
        Global Config instance

    Thread Safety:
        This function uses double-checked locking to ensure thread-safe
        singleton initialization. Multiple concurrent calls will all
        receive the same Config instance.
    """
    global _config

    # Fast path - no lock needed if already configured
    if _config is not None:
        return _config

    # Slow path - acquire lock for initialization
    with _config_lock:
        # Check again inside lock (another thread may have initialized)
        if _config is None:
            _config = load_config()
        return _config
```

### Step 4: Add test helper for config reset

Add to `src/cenv/config.py` at end:

```python
def _reset_config_for_testing() -> None:
    """Reset config singleton for testing

    Warning:
        This is for testing only and is not thread-safe during reset.
        Only call from test fixtures.
    """
    global _config
    _config = None
```

Update `__all__` in config.py to include:

```python
__all__ = [
    'Config',
    'load_config',
    'get_config',
    '_reset_config_for_testing',  # Add this
]
```

### Step 5: Update tests to use reset helper

Edit `tests/test_config.py` - add fixture at top:

```python
import pytest
from cenv.config import _reset_config_for_testing


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config before and after each test"""
    _reset_config_for_testing()
    yield
    _reset_config_for_testing()
```

Update the thread safety tests to remove manual reset:

```python
def test_get_config_is_thread_safe():
    """Test that concurrent get_config calls don't create multiple instances"""
    # Fixture handles reset
    configs = []
    # ... rest unchanged
```

### Step 6: Run tests to verify thread safety

Run: `pytest tests/test_config.py -v`

Expected: PASS (all config tests including new thread safety tests)

### Step 7: Commit

```bash
git add src/cenv/config.py tests/test_config.py
git commit -m "fix: make config singleton thread-safe

- Add threading.Lock for config initialization
- Use double-checked locking pattern
- Add tests for concurrent access
- Add _reset_config_for_testing() helper
- Consistent with logging_config.py pattern

Prevents race condition where multiple Config instances could be created."
```

---

## Task 3: Fix Bare Except Clauses

**Priority:** P0 (Critical) - CLI reliability
**Impact:** +0.5 point
**Files:**
- Create: `tests/test_exception_handling.py`
- Modify: `src/cenv/config.py:80-82`
- Modify: `src/cenv/core.py:247-248`

### Step 1: Write test for KeyboardInterrupt propagation

Create `tests/test_exception_handling.py`:

```python
"""Test that exception handling doesn't swallow critical exceptions"""
import pytest
from unittest.mock import patch
from cenv.config import load_config


def test_keyboard_interrupt_propagates_in_config():
    """Test that KeyboardInterrupt isn't swallowed during config loading"""

    # Mock file reading to raise KeyboardInterrupt
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=KeyboardInterrupt):
            # KeyboardInterrupt should propagate, not be swallowed
            with pytest.raises(KeyboardInterrupt):
                load_config()


def test_config_handles_io_errors_gracefully():
    """Test that IOError in config loading is handled gracefully"""

    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=IOError("Disk error")):
            # Should not raise, should fall back to defaults
            config = load_config()
            assert config.git_timeout == 300  # Default
```

### Step 2: Run test to see it fail

Run: `pytest tests/test_exception_handling.py::test_keyboard_interrupt_propagates_in_config -v`

Expected: FAIL - KeyboardInterrupt is caught by bare except

### Step 3: Fix config.py bare except

Edit `src/cenv/config.py` - replace lines 80-82:

```python
        except (OSError, IOError, UnicodeDecodeError):
            # If config file is malformed or unreadable, use defaults
            # Note: We don't use logging here as logging config depends on this
            pass
        # Note: KeyboardInterrupt, SystemExit, and other critical exceptions
        # will propagate naturally
```

### Step 4: Run config test to verify it passes

Run: `pytest tests/test_exception_handling.py::test_keyboard_interrupt_propagates_in_config -v`

Expected: PASS

### Step 5: Add test for lock cleanup exceptions

Add to `tests/test_exception_handling.py`:

```python
import fcntl
import tempfile
from pathlib import Path
from unittest.mock import mock_open, MagicMock


def test_lock_cleanup_handles_os_errors():
    """Test that lock cleanup handles OS errors gracefully"""
    # This is harder to test directly, so we document expected behavior
    # The cleanup code should catch (OSError, IOError) only
    # This test verifies the pattern exists
    import inspect
    from cenv.core import init_environments

    source = inspect.getsource(init_environments)

    # Verify we're catching specific exceptions, not bare except
    assert "except (OSError, IOError)" in source or "except OSError" in source, \
        "Lock cleanup should catch specific exceptions, not bare except"

    # Verify we're not using bare except Exception
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'except Exception:' in line and 'finally:' in lines[max(0, i-5):i]:
            pytest.fail(f"Found bare 'except Exception:' in finally block at line {i}")
```

### Step 6: Fix core.py bare except

Edit `src/cenv/core.py` - replace lines 247-248:

```python
            except (OSError, IOError) as e:
                # Best effort cleanup - log but don't fail
                logger.warning(f"Failed to clean up lock file: {e}")
            # Note: Other exceptions (KeyboardInterrupt, etc.) will propagate
```

### Step 7: Run all exception tests

Run: `pytest tests/test_exception_handling.py -v`

Expected: PASS (3 tests)

### Step 8: Run full test suite

Run: `pytest tests/ -v`

Expected: PASS (all 125+ tests)

### Step 9: Commit

```bash
git add src/cenv/config.py src/cenv/core.py tests/test_exception_handling.py
git commit -m "fix: replace bare except clauses with specific exceptions

- Catch only (OSError, IOError, UnicodeDecodeError) in config loading
- Catch only (OSError, IOError) in lock cleanup
- Allow KeyboardInterrupt and SystemExit to propagate
- Add tests for exception propagation

Prevents accidentally swallowing critical exceptions in CLI tools."
```

---

## Task 4: Add LICENSE File

**Priority:** P0 (Critical) - Required for public release
**Impact:** +0.3 point
**Files:**
- Create: `LICENSE`

### Step 1: Create MIT LICENSE file

Create `LICENSE`:

```txt
MIT License

Copyright (c) 2025 cenv contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Step 2: Verify file was created

Run: `cat LICENSE | head -5`

Expected: Shows "MIT License" and copyright

### Step 3: Commit

```bash
git add LICENSE
git commit -m "chore: add MIT LICENSE file

Required for open source distribution."
```

---

## Task 5: Add CHANGELOG.md

**Priority:** P0 (Critical) - Required for public release
**Impact:** +0.3 point
**Files:**
- Create: `CHANGELOG.md`

### Step 1: Create CHANGELOG.md

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Explicit `__all__` exports in all modules
- Thread-safe configuration singleton
- Exception handling tests

### Fixed
- MyPy strict mode type checking errors
- Race condition in config singleton
- Bare except clauses swallowing critical exceptions

## [0.1.0] - 2025-11-11

### Added
- Initial release
- Environment management (init, create, switch, delete)
- GitHub repository cloning support
- Trash/restore functionality
- Platform compatibility checks
- Input validation for security
- Atomic switch operations
- Thread-safe logging
- Comprehensive test suite (122 tests, 91% coverage)
- Configuration system (environment variables and config file)

### Security
- Path traversal prevention
- Command injection prevention
- Reserved name validation
- Git operation timeouts

[Unreleased]: https://github.com/yourusername/cenv/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/cenv/releases/tag/v0.1.0
```

### Step 2: Verify file was created

Run: `head -10 CHANGELOG.md`

Expected: Shows "# Changelog" and format description

### Step 3: Commit

```bash
git add CHANGELOG.md
git commit -m "chore: add CHANGELOG.md

Following Keep a Changelog format for version tracking."
```

---

## Task 6: Add CONTRIBUTING.md

**Priority:** P0 (Critical) - Required for contributors
**Impact:** +0.3 point
**Files:**
- Create: `CONTRIBUTING.md`

### Step 1: Create CONTRIBUTING.md

Create `CONTRIBUTING.md`:

```markdown
# Contributing to cenv

Thank you for considering contributing to cenv!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/cenv.git
cd cenv

# Install in development mode with dev dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cenv --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py -v
```

### Type Checking

```bash
# Run mypy type checker
mypy src/cenv --strict

# Should output: Success: no issues found
```

### Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters
- **Type hints**: Required for all functions
- **Docstrings**: Google style
- **f-strings**: Preferred over .format()

### Testing Guidelines

- **Test-Driven Development**: Write tests before code
- **Coverage**: Maintain >90% coverage
- **Edge cases**: Test error conditions

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `chore`: Build/tooling changes

Examples:
```
feat(cli): add --dry-run flag
fix(core): prevent race condition in switch
docs(readme): add troubleshooting section
```

### Design Principles

1. **Functional First**: Prefer functions over classes
2. **Type Safety**: Use type hints everywhere
3. **Fail Fast**: Validate early, raise clear errors
4. **Atomic Operations**: No partial state
5. **Security First**: Validate all inputs

## Questions?

Open an issue with the question label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
```

### Step 2: Verify file was created

Run: `head -20 CONTRIBUTING.md`

Expected: Shows contributing guidelines

### Step 3: Commit

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md

Guidelines for contributors on development setup and workflow."
```

---

## Task 7: Add SECURITY.md

**Priority:** P0 (Critical) - Required for security policy
**Impact:** +0.3 point
**Files:**
- Create: `SECURITY.md`

### Step 1: Create SECURITY.md

Create `SECURITY.md`:

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email or preferred contact method.

Include:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

You should receive a response within 48 hours.

## Security Measures

cenv implements several security measures:

### Input Validation
- All environment names validated against strict regex
- Path traversal prevention (../, etc.)
- Reserved name blocking (., .., .trash, etc.)
- Special character rejection

### Git Operations
- URL validation for GitHub repositories
- Operation timeouts (default: 5 minutes)
- Shallow clones by default
- .git directory removal after clone

### File Operations
- Atomic symlink switching
- Thread-safe operations
- File locking for concurrent access
- Backup mechanism (trash instead of hard delete)

### Platform Safety
- Unix-only (prevents Windows-specific attacks)
- Platform checks before operations
- fcntl file locking

## Best Practices

When using cenv:

1. **Close Claude before switching**: Don't rely solely on process detection
2. **Review Git URLs**: Verify repository URLs before cloning
3. **Use --verbose**: Enable logging for audit trails
4. **Regular backups**: Trash is not a permanent backup

## Version History

- **v0.1.0**: Initial security-hardened release
  - Input validation
  - Atomic operations
  - Thread safety
  - Platform checks
```

### Step 2: Verify file was created

Run: `head -20 SECURITY.md`

Expected: Shows security policy

### Step 3: Commit

```bash
git add SECURITY.md
git commit -m "security: add SECURITY.md

Security policy and reporting guidelines."
```

---

## Task 8: Add GitHub Actions CI

**Priority:** P0 (Critical) - Required for automated testing
**Impact:** +0.3 point
**Files:**
- Create: `.github/workflows/ci.yml`

### Step 1: Create CI workflow file

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: |
        uv pip install --system -e ".[dev]"

    - name: Run tests with coverage
      run: |
        pytest --cov=src/cenv --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  type-check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: |
        uv pip install --system -e ".[dev]"

    - name: Run mypy
      run: |
        mypy src/cenv --strict
```

### Step 2: Verify file structure

Run: `ls -la .github/workflows/`

Expected: Shows ci.yml file

### Step 3: Commit

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow

- Test on Ubuntu and macOS
- Test Python 3.10, 3.11, 3.12
- Run type checking with mypy strict
- Upload coverage to Codecov"
```

---

## Task 9: Update pyproject.toml with Metadata

**Priority:** P0 (Critical) - Required for PyPI
**Impact:** +0.3 point
**Files:**
- Modify: `pyproject.toml`

### Step 1: Add project metadata

Edit `pyproject.toml` - update [project] section:

```toml
[project]
name = "cenv"
version = "0.1.0"
description = "Claude environment manager - switch between Claude Code configurations"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "cenv contributors", email = "contributors@cenv.io"}
]
keywords = ["claude", "environment", "cli", "devtools", "configuration"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: POSIX",
    "Operating System :: MacOS",
    "Topic :: Software Development :: Tools",
    "Topic :: System :: Installation/Setup",
]
dependencies = [
    "click>=8.1.0,<9.0.0",
    "psutil>=5.9.0,<6.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/cenv"
Documentation = "https://github.com/yourusername/cenv#readme"
Repository = "https://github.com/yourusername/cenv"
"Bug Tracker" = "https://github.com/yourusername/cenv/issues"
Changelog = "https://github.com/yourusername/cenv/blob/main/CHANGELOG.md"
```

### Step 2: Verify changes

Run: `grep -A 5 "classifiers =" pyproject.toml | head -10`

Expected: Shows new classifiers

### Step 3: Commit

```bash
git add pyproject.toml
git commit -m "chore: update pyproject.toml with complete metadata

- Add license, authors, keywords
- Add PyPI classifiers
- Pin dependency versions to prevent breaking changes
- Add project URLs"
```

---

## Task 10: Update README with Placeholder URLs

**Priority:** P1 (Important) - Fix placeholder
**Impact:** +0.5 point
**Files:**
- Modify: `README.md`
- Modify: `src/cenv/platform_utils.py`

### Step 1: Find placeholder URLs

Run: `grep -n "yourusername\|placeholder" README.md src/cenv/platform_utils.py`

Expected: Shows placeholder GitHub URLs

### Step 2: Update platform_utils.py

Edit `src/cenv/platform_utils.py` - replace placeholder URL line:

```python
            f"For more information, see:\n"
            f"  • https://github.com/yourusername/cenv#platform-support (update to your repo)\n"
            f"  • https://docs.cenv.io/platform-support (if docs site exists)"
```

Or remove the line entirely if no docs site exists:

```python
            f"Supported platforms: {', '.join(supported)}\n\n"
            f"Workarounds:\n"
            f"  • Windows users: Use WSL2 (Windows Subsystem for Linux)\n"
            f"  • Install a Linux distribution or use macOS"
```

### Step 3: Update README.md URLs

Edit `README.md` - replace all "yourusername" placeholders:

Search for: `yourusername/cenv`
Replace with: Your actual GitHub username/org

Or add a note at the top of README:

```markdown
> **Note:** Replace `yourusername` with your actual GitHub username throughout this README.
```

### Step 4: Verify no placeholders remain

Run: `grep -n "yourusername" README.md src/cenv/platform_utils.py || echo "All placeholders removed"`

Expected: Shows remaining placeholders or "All placeholders removed"

### Step 5: Commit

```bash
git add README.md src/cenv/platform_utils.py
git commit -m "docs: update placeholder URLs

Replace yourusername placeholders with actual values or notes."
```

---

## Summary

**Total Tasks:** 10
**Estimated Time:** 2-3 hours
**Grade Improvement:** 87/100 (B+) → 92/100 (A-)

### Tasks by Priority

**P0 (Critical - Required for Public Release):**
1. ✅ Add __all__ exports (fix mypy)
2. ✅ Fix thread-unsafe config singleton
3. ✅ Fix bare except clauses
4. ✅ Add LICENSE
5. ✅ Add CHANGELOG.md
6. ✅ Add CONTRIBUTING.md
7. ✅ Add SECURITY.md
8. ✅ Add GitHub Actions CI
9. ✅ Update pyproject.toml metadata

**P1 (Important - Quality):**
10. ✅ Update placeholder URLs

### Next Steps (Future Tasks)

For additional improvements to reach A (95/100):

- **Task 11**: Split core.py into modules (1-2 hours, +1 point)
- **Task 12**: Remove unnecessary str() conversions (30 min, +0.5 point)
- **Task 13**: Add retry logic for file operations (1 hour, +0.5 point)
- **Task 14**: Add shell completion (1 hour, +0.5 point)
- **Task 15**: Add performance metrics (1 hour, +0.5 point)

### Verification Commands

After completing all tasks:

```bash
# Type checking
mypy src/cenv --strict

# Tests
pytest tests/ -v --cov=src/cenv

# Coverage should be >90%
pytest --cov=src/cenv --cov-report=term-missing

# Verify exports
python -c "from cenv import core; print('Imports work')"

# Check for placeholders
grep -r "yourusername\|TODO\|FIXME" src/ || echo "Clean"
```

### Success Criteria

- ✅ MyPy strict passes with no errors
- ✅ All 128+ tests passing
- ✅ Test coverage >90%
- ✅ All infrastructure files present
- ✅ No placeholder URLs (or documented)
- ✅ Ready for GitHub Actions CI
- ✅ **Grade: A- (92/100)**
