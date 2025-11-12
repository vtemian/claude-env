# ABOUTME: GitHub repository cloning functionality for cenv
# ABOUTME: Validates GitHub URLs and clones repositories using git subprocess
import subprocess
import shutil
from pathlib import Path
import re
from cenv.exceptions import GitOperationError
from cenv.config import get_config

__all__ = [
    'is_valid_github_url',
    'clone_from_github',
    'get_git_timeout',
]


def get_git_timeout() -> int:
    """Get configured git timeout"""
    return get_config().git_timeout

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
            timeout=get_git_timeout(),
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
        timeout_val = get_git_timeout()
        raise GitOperationError("clone", url, f"Operation timed out after {timeout_val} seconds")
    except Exception as e:
        # Clean up temp directory if it exists
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if isinstance(e, GitOperationError):
            raise
        raise GitOperationError("clone", url, str(e))
