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
