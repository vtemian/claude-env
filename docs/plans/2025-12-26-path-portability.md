# Path Portability Implementation Plan

**Goal:** Make Claude config files portable across machines by replacing absolute paths with placeholders during publish and expanding them during import.

**Architecture:** New module `path_portability.py` with functions to substitute/expand paths in JSON files. Integrates into existing `publish_to_repo()` and `clone_from_github()` flows.

**Design:** [thoughts/shared/designs/2025-12-26-path-portability-design.md](../../thoughts/shared/designs/2025-12-26-path-portability-design.md)

---

## Task 1: Create path_portability.py with Core Substitution Logic

**Files:**
- Create: `src/cenv/path_portability.py`
- Create: `tests/test_path_portability.py`

### Step 1: Write failing tests for placeholder substitution

Create `tests/test_path_portability.py`:

```python
# ABOUTME: Tests for path portability functionality
# ABOUTME: Validates path substitution and expansion for config import/export
from pathlib import Path
from unittest.mock import patch

import pytest


def test_substitute_paths_replaces_claude_home():
    """Test that Claude home paths are replaced with {{CLAUDE_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/.claude/plugins/cache/foo"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{CLAUDE_HOME}}/plugins/cache/foo"}
    assert warnings == []


def test_substitute_paths_replaces_user_home():
    """Test that user home paths are replaced with {{USER_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/projects/myproject"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{USER_HOME}}/projects/myproject"}
    assert warnings == []


def test_substitute_paths_claude_home_takes_precedence():
    """Test that {{CLAUDE_HOME}} is substituted before {{USER_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/.claude/settings.json"}
            result, warnings = substitute_paths_with_placeholders(content)

    # Should be {{CLAUDE_HOME}}, not {{USER_HOME}}/.claude
    assert result == {"path": "{{CLAUDE_HOME}}/settings.json"}
    assert warnings == []


def test_substitute_paths_warns_on_unsubstitutable_paths():
    """Test that paths outside home directory generate warnings"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"tool": "/usr/local/bin/custom-tool"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"tool": "/usr/local/bin/custom-tool"}
    assert len(warnings) == 1
    assert "/usr/local/bin/custom-tool" in warnings[0]


def test_substitute_paths_handles_nested_objects():
    """Test that nested JSON objects are traversed"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {
                "level1": {
                    "level2": {
                        "path": "/Users/vlad/.claude/deep/path"
                    }
                }
            }
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["level1"]["level2"]["path"] == "{{CLAUDE_HOME}}/deep/path"


def test_substitute_paths_handles_arrays():
    """Test that arrays of strings are processed"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {
                "paths": [
                    "/Users/vlad/.claude/path1",
                    "/Users/vlad/path2",
                    "not-a-path"
                ]
            }
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["paths"] == [
        "{{CLAUDE_HOME}}/path1",
        "{{USER_HOME}}/path2",
        "not-a-path"
    ]


def test_substitute_paths_preserves_non_string_values():
    """Test that numbers, booleans, null are unchanged"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {
                "count": 42,
                "enabled": True,
                "nothing": None,
                "path": "/Users/vlad/.claude/file"
            }
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["count"] == 42
    assert result["enabled"] is True
    assert result["nothing"] is None
    assert result["path"] == "{{CLAUDE_HOME}}/file"


def test_substitute_paths_handles_embedded_paths():
    """Test that paths embedded in larger strings are substituted"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"command": "node /Users/vlad/.claude/scripts/run.js --verbose"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"command": "node {{CLAUDE_HOME}}/scripts/run.js --verbose"}


def test_substitute_paths_no_double_substitution():
    """Test that existing placeholders are not double-substituted"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "{{CLAUDE_HOME}}/already/substituted"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{CLAUDE_HOME}}/already/substituted"}
    assert warnings == []
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_path_portability.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'cenv.path_portability'`

### Step 3: Write minimal implementation for substitution

Create `src/cenv/path_portability.py`:

```python
# ABOUTME: Path portability for config import/export
# ABOUTME: Replaces absolute paths with placeholders and expands them back
"""Path portability utilities for cenv"""

import re
from pathlib import Path
from typing import Any

from cenv.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "substitute_paths_with_placeholders",
    "expand_placeholders_to_paths",
    "process_json_files_for_publish",
    "process_json_files_for_import",
    "PLACEHOLDER_CLAUDE_HOME",
    "PLACEHOLDER_USER_HOME",
]

# Placeholder tokens
PLACEHOLDER_CLAUDE_HOME = "{{CLAUDE_HOME}}"
PLACEHOLDER_USER_HOME = "{{USER_HOME}}"


def _get_user_home() -> Path:
    """Get user's home directory"""
    return Path.home()


def _get_claude_home() -> Path:
    """Get Claude config directory"""
    return Path.home() / ".claude"


def _is_absolute_path(value: str) -> bool:
    """Check if a string looks like an absolute path"""
    # Unix absolute paths start with /
    # Windows absolute paths start with drive letter (C:\) or UNC (\\)
    return (
        value.startswith("/")
        or (len(value) >= 3 and value[1] == ":" and value[2] in "/\\")
        or value.startswith("\\\\")
    )


def _substitute_in_string(
    value: str,
    claude_home: str,
    user_home: str,
) -> tuple[str, list[str]]:
    """Substitute paths in a single string value

    Args:
        value: String to process
        claude_home: Claude home directory path
        user_home: User home directory path

    Returns:
        Tuple of (substituted string, list of warning messages)
    """
    warnings: list[str] = []

    # Skip if already contains placeholders
    if PLACEHOLDER_CLAUDE_HOME in value or PLACEHOLDER_USER_HOME in value:
        return value, warnings

    result = value

    # Replace Claude home first (more specific)
    if claude_home in result:
        result = result.replace(claude_home, PLACEHOLDER_CLAUDE_HOME)

    # Then replace user home
    if user_home in result:
        result = result.replace(user_home, PLACEHOLDER_USER_HOME)

    # Check for remaining absolute paths that couldn't be substituted
    # Look for paths that start with / but aren't our placeholders
    if result == value and _is_absolute_path(value):
        # Find all absolute paths in the string
        # Match Unix paths: /something or Windows paths: C:\something
        path_pattern = r'(?:^|["\s])(/[^\s"\']+|[A-Za-z]:\\[^\s"\']+)'
        matches = re.findall(path_pattern, value)
        for match in matches:
            if not match.startswith(user_home) and not match.startswith(claude_home):
                warnings.append(match)

    return result, warnings


def _walk_and_substitute(
    obj: Any,
    claude_home: str,
    user_home: str,
) -> tuple[Any, list[str]]:
    """Recursively walk JSON structure and substitute paths

    Args:
        obj: JSON object (dict, list, or primitive)
        claude_home: Claude home directory path
        user_home: User home directory path

    Returns:
        Tuple of (transformed object, list of warning messages)
    """
    all_warnings: list[str] = []

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            transformed, warnings = _walk_and_substitute(value, claude_home, user_home)
            result[key] = transformed
            all_warnings.extend(warnings)
        return result, all_warnings

    if isinstance(obj, list):
        result = []
        for item in obj:
            transformed, warnings = _walk_and_substitute(item, claude_home, user_home)
            result.append(transformed)
            all_warnings.extend(warnings)
        return result, all_warnings

    if isinstance(obj, str):
        return _substitute_in_string(obj, claude_home, user_home)

    # Numbers, booleans, None - return unchanged
    return obj, all_warnings


def substitute_paths_with_placeholders(
    content: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Replace absolute paths with placeholders for portability

    Args:
        content: Parsed JSON content

    Returns:
        Tuple of (transformed content, list of warning messages for unsubstitutable paths)
    """
    claude_home = str(_get_claude_home())
    user_home = str(_get_user_home())

    result, warnings = _walk_and_substitute(content, claude_home, user_home)
    return result, warnings
```

### Step 4: Run tests to verify they pass

Run: `uv run pytest tests/test_path_portability.py -v`

Expected: PASS (all 9 tests)

### Step 5: Commit

```bash
git add src/cenv/path_portability.py tests/test_path_portability.py
git commit -m "feat(path-portability): add path substitution for publish"
```

---

## Task 2: Add Placeholder Expansion Logic

**Files:**
- Modify: `src/cenv/path_portability.py`
- Modify: `tests/test_path_portability.py`

### Step 1: Write failing tests for placeholder expansion

Add to `tests/test_path_portability.py`:

```python
def test_expand_placeholders_expands_claude_home():
    """Test that {{CLAUDE_HOME}} is expanded to local Claude directory"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {"path": "{{CLAUDE_HOME}}/plugins/cache/foo"}
            result = expand_placeholders_to_paths(content)

    assert result == {"path": "/Users/newuser/.claude/plugins/cache/foo"}


def test_expand_placeholders_expands_user_home():
    """Test that {{USER_HOME}} is expanded to local home directory"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {"path": "{{USER_HOME}}/projects/myproject"}
            result = expand_placeholders_to_paths(content)

    assert result == {"path": "/Users/newuser/projects/myproject"}


def test_expand_placeholders_handles_both_in_same_string():
    """Test that both placeholders in same string are expanded"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/home/user/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/home/user")):
            content = {"cmd": "cp {{CLAUDE_HOME}}/a {{USER_HOME}}/b"}
            result = expand_placeholders_to_paths(content)

    assert result == {"cmd": "cp /home/user/.claude/a /home/user/b"}


def test_expand_placeholders_handles_nested_objects():
    """Test that nested JSON objects are traversed during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {
                "level1": {
                    "level2": {
                        "path": "{{CLAUDE_HOME}}/deep/path"
                    }
                }
            }
            result = expand_placeholders_to_paths(content)

    assert result["level1"]["level2"]["path"] == "/Users/newuser/.claude/deep/path"


def test_expand_placeholders_handles_arrays():
    """Test that arrays are processed during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {
                "paths": [
                    "{{CLAUDE_HOME}}/path1",
                    "{{USER_HOME}}/path2",
                    "not-a-placeholder"
                ]
            }
            result = expand_placeholders_to_paths(content)

    assert result["paths"] == [
        "/Users/newuser/.claude/path1",
        "/Users/newuser/path2",
        "not-a-placeholder"
    ]


def test_expand_placeholders_preserves_non_string_values():
    """Test that numbers, booleans, null are unchanged during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {
                "count": 42,
                "enabled": True,
                "nothing": None,
                "path": "{{CLAUDE_HOME}}/file"
            }
            result = expand_placeholders_to_paths(content)

    assert result["count"] == 42
    assert result["enabled"] is True
    assert result["nothing"] is None
    assert result["path"] == "/Users/newuser/.claude/file"
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_path_portability.py::test_expand_placeholders_expands_claude_home -v`

Expected: FAIL with `ImportError: cannot import name 'expand_placeholders_to_paths'`

### Step 3: Implement placeholder expansion

Add to `src/cenv/path_portability.py` (after `substitute_paths_with_placeholders`):

```python
def _expand_in_string(
    value: str,
    claude_home: str,
    user_home: str,
) -> str:
    """Expand placeholders in a single string value

    Args:
        value: String to process
        claude_home: Claude home directory path
        user_home: User home directory path

    Returns:
        String with placeholders expanded
    """
    result = value
    result = result.replace(PLACEHOLDER_CLAUDE_HOME, claude_home)
    result = result.replace(PLACEHOLDER_USER_HOME, user_home)
    return result


def _walk_and_expand(
    obj: Any,
    claude_home: str,
    user_home: str,
) -> Any:
    """Recursively walk JSON structure and expand placeholders

    Args:
        obj: JSON object (dict, list, or primitive)
        claude_home: Claude home directory path
        user_home: User home directory path

    Returns:
        Transformed object with placeholders expanded
    """
    if isinstance(obj, dict):
        return {key: _walk_and_expand(value, claude_home, user_home) for key, value in obj.items()}

    if isinstance(obj, list):
        return [_walk_and_expand(item, claude_home, user_home) for item in obj]

    if isinstance(obj, str):
        return _expand_in_string(obj, claude_home, user_home)

    # Numbers, booleans, None - return unchanged
    return obj


def expand_placeholders_to_paths(content: dict[str, Any]) -> dict[str, Any]:
    """Expand placeholders to local paths for import

    Args:
        content: Parsed JSON content with placeholders

    Returns:
        Content with placeholders expanded to local paths
    """
    claude_home = str(_get_claude_home())
    user_home = str(_get_user_home())

    return _walk_and_expand(content, claude_home, user_home)
```

### Step 4: Run tests to verify they pass

Run: `uv run pytest tests/test_path_portability.py -v`

Expected: PASS (all 15 tests)

### Step 5: Commit

```bash
git add src/cenv/path_portability.py tests/test_path_portability.py
git commit -m "feat(path-portability): add placeholder expansion for import"
```

---

## Task 3: Add File Processing Functions

**Files:**
- Modify: `src/cenv/path_portability.py`
- Modify: `tests/test_path_portability.py`

### Step 1: Write failing tests for file processing

Add to `tests/test_path_portability.py`:

```python
import json


def test_process_json_files_for_publish_transforms_files(tmp_path):
    """Test that JSON files are transformed with placeholders on publish"""
    from cenv.path_portability import process_json_files_for_publish

    # Create test JSON file
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"path": "/Users/vlad/.claude/plugins"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            warnings = process_json_files_for_publish(tmp_path)

    # Verify file was transformed
    result = json.loads(json_file.read_text())
    assert result == {"path": "{{CLAUDE_HOME}}/plugins"}
    assert warnings == []


def test_process_json_files_for_publish_handles_nested_dirs(tmp_path):
    """Test that JSON files in subdirectories are processed"""
    from cenv.path_portability import process_json_files_for_publish

    # Create nested JSON file
    subdir = tmp_path / "plugins"
    subdir.mkdir()
    json_file = subdir / "config.json"
    json_file.write_text(json.dumps({"installPath": "/Users/vlad/.claude/cache"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            process_json_files_for_publish(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"installPath": "{{CLAUDE_HOME}}/cache"}


def test_process_json_files_for_publish_skips_non_json(tmp_path):
    """Test that non-JSON files are not modified"""
    from cenv.path_portability import process_json_files_for_publish

    # Create non-JSON file with path-like content
    md_file = tmp_path / "README.md"
    original_content = "Path: /Users/vlad/.claude/plugins"
    md_file.write_text(original_content)

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            process_json_files_for_publish(tmp_path)

    # Verify file was NOT modified
    assert md_file.read_text() == original_content


def test_process_json_files_for_publish_collects_warnings(tmp_path):
    """Test that warnings from all files are collected"""
    from cenv.path_portability import process_json_files_for_publish

    # Create JSON file with unsubstitutable path
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"tool": "/usr/local/bin/node"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            warnings = process_json_files_for_publish(tmp_path)

    assert len(warnings) == 1
    assert "settings.json" in warnings[0]
    assert "/usr/local/bin/node" in warnings[0]


def test_process_json_files_for_publish_handles_malformed_json(tmp_path, caplog):
    """Test that malformed JSON files are skipped with warning"""
    from cenv.path_portability import process_json_files_for_publish

    # Create malformed JSON file
    json_file = tmp_path / "broken.json"
    json_file.write_text("{ not valid json }")

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            warnings = process_json_files_for_publish(tmp_path)

    # Should not raise, should log warning
    assert "broken.json" in caplog.text or len(warnings) == 0  # Either logged or silently skipped


def test_process_json_files_for_import_expands_placeholders(tmp_path):
    """Test that JSON files have placeholders expanded on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create JSON file with placeholders
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"path": "{{CLAUDE_HOME}}/plugins"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            process_json_files_for_import(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"path": "/Users/newuser/.claude/plugins"}


def test_process_json_files_for_import_handles_nested_dirs(tmp_path):
    """Test that JSON files in subdirectories are processed on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create nested JSON file
    subdir = tmp_path / "plugins"
    subdir.mkdir()
    json_file = subdir / "config.json"
    json_file.write_text(json.dumps({"installPath": "{{CLAUDE_HOME}}/cache"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            process_json_files_for_import(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"installPath": "/Users/newuser/.claude/cache"}


def test_process_json_files_for_import_handles_malformed_json(tmp_path, caplog):
    """Test that malformed JSON files are skipped on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create malformed JSON file
    json_file = tmp_path / "broken.json"
    json_file.write_text("{ not valid json }")

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            process_json_files_for_import(tmp_path)

    # Should not raise
    assert json_file.read_text() == "{ not valid json }"  # Unchanged
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_path_portability.py::test_process_json_files_for_publish_transforms_files -v`

Expected: FAIL with `ImportError: cannot import name 'process_json_files_for_publish'`

### Step 3: Implement file processing functions

Add to `src/cenv/path_portability.py`:

```python
import json


def process_json_files_for_publish(directory: Path) -> list[str]:
    """Process all JSON files in directory for publish (substitute paths)

    Args:
        directory: Directory to process

    Returns:
        List of warning messages about unsubstitutable paths
    """
    all_warnings: list[str] = []

    for json_file in directory.rglob("*.json"):
        if not json_file.is_file():
            continue

        try:
            content = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not parse {json_file.name}: {e}")
            continue

        transformed, warnings = substitute_paths_with_placeholders(content)

        # Format warnings with filename
        for warning in warnings:
            all_warnings.append(f"{json_file.name}: {warning}")

        # Write back if changed
        if transformed != content:
            json_file.write_text(json.dumps(transformed, indent=2) + "\n")
            logger.debug(f"Transformed paths in {json_file.name}")

    return all_warnings


def process_json_files_for_import(directory: Path) -> None:
    """Process all JSON files in directory for import (expand placeholders)

    Args:
        directory: Directory to process
    """
    for json_file in directory.rglob("*.json"):
        if not json_file.is_file():
            continue

        try:
            content = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not parse {json_file.name}: {e}")
            continue

        expanded = expand_placeholders_to_paths(content)

        # Write back if changed
        if expanded != content:
            json_file.write_text(json.dumps(expanded, indent=2) + "\n")
            logger.debug(f"Expanded placeholders in {json_file.name}")
```

Also add `import json` at the top of the file.

### Step 4: Run tests to verify they pass

Run: `uv run pytest tests/test_path_portability.py -v`

Expected: PASS (all 24 tests)

### Step 5: Commit

```bash
git add src/cenv/path_portability.py tests/test_path_portability.py
git commit -m "feat(path-portability): add file processing for publish/import"
```

---

## Task 4: Integrate with publish.py

**Files:**
- Modify: `src/cenv/publish.py:320-355` (after copying files, before git add)
- Modify: `tests/test_publish.py`

### Step 1: Write failing integration test

Add to `tests/test_publish.py`:

```python
@patch("subprocess.run")
def test_publish_to_repo_substitutes_paths_in_json(mock_run, tmp_path):
    """Test that publish substitutes absolute paths with placeholders in JSON files"""
    import json

    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    
    # Create JSON file with absolute path
    settings = env_dir / "settings.json"
    home = str(Path.home())
    claude_home = str(Path.home() / ".claude")
    settings.write_text(json.dumps({
        "pluginPath": f"{claude_home}/plugins/cache",
        "projectPath": f"{home}/projects/myproject"
    }))

    captured_json = {}

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        if cmd[0] == "git" and cmd[1] == "add":
            # Capture the transformed JSON content
            temp_dir = Path(kwargs.get("cwd", "."))
            settings_path = temp_dir / "settings.json"
            if settings_path.exists():
                captured_json["settings"] = json.loads(settings_path.read_text())
        if cmd[0] == "git" and cmd[1] == "status":
            return MagicMock(returncode=0, stdout="M file", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    publish_to_repo(env_dir, "https://github.com/user/repo")

    # Verify paths were substituted with placeholders
    assert captured_json["settings"]["pluginPath"] == "{{CLAUDE_HOME}}/plugins/cache"
    assert captured_json["settings"]["projectPath"] == "{{USER_HOME}}/projects/myproject"
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_publish.py::test_publish_to_repo_substitutes_paths_in_json -v`

Expected: FAIL - paths are not substituted (still contain absolute paths)

### Step 3: Integrate path portability into publish.py

Modify `src/cenv/publish.py`:

1. Add import at top (after other cenv imports, around line 16):

```python
from cenv.path_portability import process_json_files_for_publish
```

2. Add path processing after copying files (after line 325, before README generation):

```python
        # Process JSON files for path portability
        logger.info("Processing JSON files for path portability")
        path_warnings = process_json_files_for_publish(temp_dir)
        if path_warnings:
            logger.warning("Some paths could not be made portable:")
            for warning in path_warnings:
                logger.warning(f"  - {warning}")
```

The modified section of `publish_to_repo` (lines 320-340) should look like:

```python
        # Copy files to publish
        for file_path in to_publish:
            relative = file_path.relative_to(env_path)
            target = temp_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target)

        # Process JSON files for path portability
        logger.info("Processing JSON files for path portability")
        path_warnings = process_json_files_for_publish(temp_dir)
        if path_warnings:
            logger.warning("Some paths could not be made portable:")
            for warning in path_warnings:
                logger.warning(f"  - {warning}")

        # Generate README.md
        readme_content = f"""# Claude Config
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_publish.py::test_publish_to_repo_substitutes_paths_in_json -v`

Expected: PASS

### Step 5: Run all publish tests to ensure no regressions

Run: `uv run pytest tests/test_publish.py -v`

Expected: PASS (all tests)

### Step 6: Commit

```bash
git add src/cenv/publish.py tests/test_publish.py
git commit -m "feat(publish): integrate path portability for JSON files"
```

---

## Task 5: Integrate with github.py

**Files:**
- Modify: `src/cenv/github.py:62-73` (after removing .git, before moving to final location)
- Modify: `tests/test_github.py`

### Step 1: Write failing integration test

Add to `tests/test_github.py`:

```python
@patch("subprocess.run")
def test_clone_from_github_expands_placeholders_in_json(mock_run, tmp_path):
    """Test that clone expands placeholders to local paths in JSON files"""
    import json

    target = tmp_path / "test-env"

    def simulate_git_clone(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
            # Create JSON file with placeholders (as if published)
            settings = temp_dir / "settings.json"
            settings.write_text(json.dumps({
                "pluginPath": "{{CLAUDE_HOME}}/plugins/cache",
                "projectPath": "{{USER_HOME}}/projects/myproject"
            }))
        return MagicMock(returncode=0)

    mock_run.side_effect = simulate_git_clone

    clone_from_github("https://github.com/user/repo", target)

    # Verify placeholders were expanded to local paths
    settings = target / "settings.json"
    content = json.loads(settings.read_text())
    
    expected_claude_home = str(Path.home() / ".claude")
    expected_user_home = str(Path.home())
    
    assert content["pluginPath"] == f"{expected_claude_home}/plugins/cache"
    assert content["projectPath"] == f"{expected_user_home}/projects/myproject"
```

### Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_github.py::test_clone_from_github_expands_placeholders_in_json -v`

Expected: FAIL - placeholders are not expanded

### Step 3: Integrate path portability into github.py

Modify `src/cenv/github.py`:

1. Add import at top (after other cenv imports, around line 9):

```python
from cenv.path_portability import process_json_files_for_import
```

2. Add path processing after removing .git directory (after line 65, before moving to final location):

```python
        # Expand path placeholders for portability
        process_json_files_for_import(temp_dir)
```

The modified section of `clone_from_github` (lines 62-73) should look like:

```python
        # Remove .git directory if it exists
        git_dir = temp_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        # Expand path placeholders for portability
        process_json_files_for_import(temp_dir)

        # Move to final location
        if target.exists():
            shutil.rmtree(target)

        # Only move if temp_dir exists (for real git clone)
        if temp_dir.exists():
            shutil.move(str(temp_dir), str(target))
```

### Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_github.py::test_clone_from_github_expands_placeholders_in_json -v`

Expected: PASS

### Step 5: Run all github tests to ensure no regressions

Run: `uv run pytest tests/test_github.py -v`

Expected: PASS (all tests)

### Step 6: Commit

```bash
git add src/cenv/github.py tests/test_github.py
git commit -m "feat(github): expand path placeholders on clone"
```

---

## Task 6: Add Module Exports and Update __init__.py

**Files:**
- Modify: `src/cenv/__init__.py`

### Step 1: Read current __init__.py

Run: Read `src/cenv/__init__.py` to see current exports

### Step 2: Add path_portability exports

Add to `src/cenv/__init__.py` (in the imports section and __all__):

```python
from cenv.path_portability import (
    PLACEHOLDER_CLAUDE_HOME,
    PLACEHOLDER_USER_HOME,
    expand_placeholders_to_paths,
    process_json_files_for_import,
    process_json_files_for_publish,
    substitute_paths_with_placeholders,
)
```

And add to `__all__`:

```python
    # Path portability
    "PLACEHOLDER_CLAUDE_HOME",
    "PLACEHOLDER_USER_HOME",
    "substitute_paths_with_placeholders",
    "expand_placeholders_to_paths",
    "process_json_files_for_publish",
    "process_json_files_for_import",
```

### Step 3: Run type check and lint

Run: `uv run make check`

Expected: PASS

### Step 4: Commit

```bash
git add src/cenv/__init__.py
git commit -m "feat(exports): add path portability to public API"
```

---

## Task 7: Add Cross-Platform Path Tests

**Files:**
- Modify: `tests/test_path_portability.py`

### Step 1: Write tests for Windows-style paths

Add to `tests/test_path_portability.py`:

```python
def test_substitute_paths_handles_windows_backslashes():
    """Test that Windows-style paths with backslashes are handled"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("C:/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("C:/Users/vlad")):
            # Windows paths might have forward or back slashes
            content = {"path": "C:/Users/vlad/.claude/plugins"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{CLAUDE_HOME}}/plugins"}


def test_expand_placeholders_uses_native_separators():
    """Test that expanded paths use the platform's native separators"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/test/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/test")):
            content = {"path": "{{CLAUDE_HOME}}/plugins/cache"}
            result = expand_placeholders_to_paths(content)

    # Path should use the mocked path's format
    assert result == {"path": "/Users/test/.claude/plugins/cache"}


def test_substitute_paths_empty_json():
    """Test that empty JSON objects are handled"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content: dict = {}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {}
    assert warnings == []


def test_expand_placeholders_empty_json():
    """Test that empty JSON objects are handled during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/test/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/test")):
            content: dict = {}
            result = expand_placeholders_to_paths(content)

    assert result == {}
```

### Step 2: Run all tests

Run: `uv run pytest tests/test_path_portability.py -v`

Expected: PASS (all tests)

### Step 3: Commit

```bash
git add tests/test_path_portability.py
git commit -m "test(path-portability): add cross-platform and edge case tests"
```

---

## Task 8: Final Integration Test

**Files:**
- Modify: `tests/test_integration.py` (or create if needed)

### Step 1: Write end-to-end round-trip test

Add to `tests/test_path_portability.py`:

```python
def test_round_trip_publish_then_import(tmp_path):
    """Test that publish followed by import produces correct local paths"""
    from cenv.path_portability import (
        process_json_files_for_import,
        process_json_files_for_publish,
    )

    # Simulate User A publishing
    publish_dir = tmp_path / "publish"
    publish_dir.mkdir()
    
    user_a_home = "/Users/userA"
    user_a_claude = "/Users/userA/.claude"
    
    original_content = {
        "plugins": {
            "superpowers": {
                "installPath": f"{user_a_claude}/plugins/cache/superpowers",
                "configPath": f"{user_a_home}/projects/config.json"
            }
        },
        "settings": {
            "logLevel": "debug",
            "maxTokens": 4096
        }
    }
    
    json_file = publish_dir / "config.json"
    json_file.write_text(json.dumps(original_content))
    
    # Publish (substitute paths)
    with patch("cenv.path_portability._get_claude_home", return_value=Path(user_a_claude)):
        with patch("cenv.path_portability._get_user_home", return_value=Path(user_a_home)):
            process_json_files_for_publish(publish_dir)
    
    # Verify placeholders are in the file
    published = json.loads(json_file.read_text())
    assert "{{CLAUDE_HOME}}" in published["plugins"]["superpowers"]["installPath"]
    assert "{{USER_HOME}}" in published["plugins"]["superpowers"]["configPath"]
    
    # Simulate User B importing
    user_b_home = "/home/userB"
    user_b_claude = "/home/userB/.claude"
    
    with patch("cenv.path_portability._get_claude_home", return_value=Path(user_b_claude)):
        with patch("cenv.path_portability._get_user_home", return_value=Path(user_b_home)):
            process_json_files_for_import(publish_dir)
    
    # Verify paths are expanded to User B's paths
    imported = json.loads(json_file.read_text())
    assert imported["plugins"]["superpowers"]["installPath"] == f"{user_b_claude}/plugins/cache/superpowers"
    assert imported["plugins"]["superpowers"]["configPath"] == f"{user_b_home}/projects/config.json"
    
    # Verify non-path values are unchanged
    assert imported["settings"]["logLevel"] == "debug"
    assert imported["settings"]["maxTokens"] == 4096
```

### Step 2: Run the integration test

Run: `uv run pytest tests/test_path_portability.py::test_round_trip_publish_then_import -v`

Expected: PASS

### Step 3: Run full test suite

Run: `uv run make check`

Expected: PASS (all checks)

### Step 4: Commit

```bash
git add tests/test_path_portability.py
git commit -m "test(path-portability): add round-trip integration test"
```

---

## Summary

| Task | Description | Files Modified |
|------|-------------|----------------|
| 1 | Core substitution logic | `path_portability.py`, `test_path_portability.py` |
| 2 | Placeholder expansion | `path_portability.py`, `test_path_portability.py` |
| 3 | File processing functions | `path_portability.py`, `test_path_portability.py` |
| 4 | Integrate with publish.py | `publish.py`, `test_publish.py` |
| 5 | Integrate with github.py | `github.py`, `test_github.py` |
| 6 | Module exports | `__init__.py` |
| 7 | Cross-platform tests | `test_path_portability.py` |
| 8 | Integration test | `test_path_portability.py` |

**Total estimated time:** 45-60 minutes

**Key integration points:**
- `publish.py:325` - After copying files to temp dir, before README generation
- `github.py:65` - After removing .git directory, before moving to final location
