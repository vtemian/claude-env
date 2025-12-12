# ABOUTME: Publish functionality for sharing Claude configs to GitHub
# ABOUTME: Handles sensitive file detection and git push operations
"""Publish functionality for cenv"""

import fnmatch
from pathlib import Path

__all__ = [
    "SENSITIVE_PATTERNS",
    "is_sensitive_file",
    "get_files_to_publish",
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
