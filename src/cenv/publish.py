# ABOUTME: Publish functionality for sharing Claude configs to GitHub
# ABOUTME: Handles sensitive file detection and git push operations
"""Publish functionality for cenv"""

import fnmatch
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cenv.config import get_config
from cenv.exceptions import GitOperationError
from cenv.github import is_valid_github_url
from cenv.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "SENSITIVE_PATTERNS",
    "EXCLUDED_DIRECTORIES",
    "EXCLUDED_FILE_PATTERNS",
    "is_sensitive_file",
    "is_excluded_path",
    "transform_plugins_to_manifest",
    "install_plugins_from_manifest",
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

# Directories that contain cache/temp/local data (not config)
EXCLUDED_DIRECTORIES: set[str] = {
    # Cache and temporary data
    "debug",
    "file-history",
    "ide",
    "plans",
    "session-env",
    "shell-snapshots",
    "statsig",
    "telemetry",
    "todos",
    # Project-specific data (contains local paths)
    "projects",
    # Local scripts and dependencies
    "local",
    # Plugin cache (but not plugin config)
    "cache",
    "marketplaces",
    "repos",
}

# File patterns for cache/temp/local data
EXCLUDED_FILE_PATTERNS: set[str] = {
    # History and stats
    "history.jsonl",
    "stats-cache.json",
    "leaderboard.json",
    # Package files for local scripts
    "package.json",
    "package-lock.json",
    # Backup files
    "*.bak",
    # Plugin state (transformed to manifest on publish)
    "installed_plugins.json",
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


def is_excluded_path(file_path: Path, base_path: Path) -> bool:
    """Check if a file path should be excluded based on directory or pattern

    Args:
        file_path: Full path to the file
        base_path: Base environment directory path

    Returns:
        True if file should be excluded (in excluded dir or matches excluded pattern)
    """
    # Check if any parent directory is in the excluded list
    try:
        relative = file_path.relative_to(base_path)
        for part in relative.parts[:-1]:  # All parts except filename
            if part in EXCLUDED_DIRECTORIES:
                return True
    except ValueError:
        pass  # file_path not relative to base_path

    # Check file patterns
    filename_lower = file_path.name.lower()
    for pattern in EXCLUDED_FILE_PATTERNS:
        if fnmatch.fnmatch(filename_lower, pattern.lower()):
            return True

    return False


def transform_plugins_to_manifest(installed_plugins: dict[str, Any]) -> dict[str, Any]:
    """Transform installed_plugins.json to a portable manifest format

    Args:
        installed_plugins: Contents of installed_plugins.json

    Returns:
        Manifest with just plugin names and versions
    """
    manifest: dict[str, str] = {}

    plugins = installed_plugins.get("plugins", {})
    for plugin_name, plugin_entries in plugins.items():
        if plugin_entries and isinstance(plugin_entries, list):
            # Take the first entry's version (typically there's only one)
            version = plugin_entries[0].get("version")
            if version:
                manifest[plugin_name] = version

    return {"plugins": manifest}


def install_plugins_from_manifest(env_path: Path) -> list[str]:
    """Install plugins listed in plugins-manifest.json

    Args:
        env_path: Path to the environment directory

    Returns:
        List of successfully installed plugin names
    """
    manifest_path = env_path / "plugins" / "plugins-manifest.json"
    if not manifest_path.exists():
        logger.debug("No plugins-manifest.json found, skipping plugin installation")
        return []

    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read plugins manifest: {e}")
        return []

    plugins = manifest.get("plugins", {})
    if not plugins:
        return []

    installed = []
    for plugin_name, version in plugins.items():
        logger.info(f"Installing plugin: {plugin_name}")
        result = subprocess.run(
            ["claude", "plugin", "install", plugin_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            installed.append(plugin_name)
            logger.info(f"Installed {plugin_name}")
        else:
            logger.warning(f"Failed to install {plugin_name}: {result.stderr.strip()}")

    return installed


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
            if is_sensitive_file(file_path.name) or is_excluded_path(file_path, env_path):
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
        logger.info(f"Excluding {len(excluded)} sensitive/cache files")

    # Create temp directory for git operations
    temp_dir = env_path.parent / f".tmp_publish_{env_path.name}"

    # Clean up any leftover temp directory from previous interrupted runs
    if temp_dir.exists():
        logger.debug(f"Cleaning up leftover temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)

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

        logger.info("Clone successful, preparing files")

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

        # Generate plugins manifest from installed_plugins.json if it exists
        installed_plugins_path = env_path / "plugins" / "installed_plugins.json"
        if installed_plugins_path.exists():
            try:
                installed_plugins = json.loads(installed_plugins_path.read_text())
                manifest = transform_plugins_to_manifest(installed_plugins)
                if manifest.get("plugins"):
                    manifest_dir = temp_dir / "plugins"
                    manifest_dir.mkdir(parents=True, exist_ok=True)
                    manifest_path = manifest_dir / "plugins-manifest.json"
                    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
                    logger.debug("Generated plugins-manifest.json")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not generate plugins manifest: {e}")

        # Git add, commit, push
        logger.info(f"Staging {len(to_publish)} files for commit")
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
            logger.info("No changes detected, nothing to publish")
            return PublishResult(
                success=True,
                files_published=0,
                files_excluded=len(excluded),
                excluded_files=excluded_names,
            )

        logger.info("Creating commit")
        commit_result = subprocess.run(
            ["git", "commit", "-m", "Update Claude config via cenv publish"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if commit_result.returncode != 0:
            raise GitOperationError("commit", repo_url, commit_result.stderr.strip())

        logger.info(f"Pushing to remote (timeout: {get_config().git_timeout}s)...")
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

        logger.info(f"Published {len(to_publish)} files successfully")
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
