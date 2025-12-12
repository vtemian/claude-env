# ABOUTME: Publish functionality for sharing Claude configs to GitHub
# ABOUTME: Handles sensitive file detection and git push operations
"""Publish functionality for cenv"""

import fnmatch
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from cenv.config import get_config
from cenv.exceptions import GitOperationError
from cenv.github import is_valid_github_url
from cenv.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "SENSITIVE_PATTERNS",
    "is_sensitive_file",
    "get_files_to_publish",
    "publish_to_repo",
    "PublishResult",
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
