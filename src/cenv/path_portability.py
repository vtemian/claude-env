# ABOUTME: Path portability for config import/export
# ABOUTME: Replaces absolute paths with placeholders and expands them back
"""Path portability utilities for cenv"""

import json
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
