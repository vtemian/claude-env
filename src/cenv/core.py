# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional
import shutil
from cenv.process import is_claude_running
from cenv.github import clone_from_github, is_valid_github_url
from cenv.logging_config import get_logger
from cenv.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
)

logger = get_logger(__name__)

def get_envs_dir() -> Path:
    """Get the base directory for all environments"""
    return Path.home() / ".claude-envs"

def get_env_path(name: str) -> Path:
    """Get the path for a specific environment"""
    return get_envs_dir() / name

def get_claude_dir() -> Path:
    """Get the ~/.claude directory path"""
    return Path.home() / ".claude"

def list_environments() -> List[str]:
    """List all available environments"""
    envs_dir = get_envs_dir()

    if not envs_dir.exists():
        return []

    return [
        item.name
        for item in envs_dir.iterdir()
        if item.is_dir()
    ]

def get_current_environment() -> Optional[str]:
    """Get the currently active environment name"""
    claude_dir = get_claude_dir()

    if not claude_dir.is_symlink():
        return None

    target = claude_dir.resolve()
    envs_dir = get_envs_dir()

    if target.parent == envs_dir:
        return target.name

    return None

def environment_exists(name: str) -> bool:
    """Check if an environment exists"""
    return get_env_path(name).exists()

def init_environments() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    logger.info("Initializing cenv")
    claude_dir = get_claude_dir()
    envs_dir = get_envs_dir()
    default_env = get_env_path("default")

    # Check if ~/.claude is already a symlink
    if claude_dir.is_symlink():
        logger.error("~/.claude is already a symlink")
        raise InitializationError("~/.claude is already a symlink. Cannot initialize.")

    # Check if already initialized
    if envs_dir.exists():
        logger.error("cenv already initialized")
        raise InitializationError("cenv already initialized. ~/.claude-envs exists.")

    # Create backup if claude_dir exists
    backup_dir = None
    if claude_dir.exists() and not claude_dir.is_symlink():
        backup_dir = claude_dir.parent / ".claude.backup"
        logger.info(f"Creating backup at {backup_dir}")
        shutil.copytree(claude_dir, backup_dir)

    try:
        # Create envs directory
        logger.debug(f"Creating envs directory at {envs_dir}")
        envs_dir.mkdir(parents=True, exist_ok=True)

        # Move ~/.claude to default environment
        if claude_dir.exists():
            logger.info(f"Moving {claude_dir} to {default_env}")
            shutil.move(str(claude_dir), str(default_env))
        else:
            # Create empty default environment
            logger.info(f"Creating empty default environment at {default_env}")
            default_env.mkdir(parents=True, exist_ok=True)

        # Create symlink
        logger.info(f"Creating symlink {claude_dir} -> {default_env}")
        claude_dir.symlink_to(default_env)

        # Clean up backup on success
        if backup_dir and backup_dir.exists():
            logger.debug(f"Removing backup at {backup_dir}")
            shutil.rmtree(backup_dir)

        logger.info("Initialization complete")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        # Restore from backup if anything failed
        if backup_dir and backup_dir.exists():
            logger.info(f"Restoring from backup at {backup_dir}")
            # Clean up any partial state
            if claude_dir.exists():
                if claude_dir.is_symlink():
                    claude_dir.unlink()
                else:
                    shutil.rmtree(claude_dir)
            if default_env.exists():
                shutil.rmtree(default_env)
            if envs_dir.exists() and not any(envs_dir.iterdir()):
                envs_dir.rmdir()
            # Restore original .claude
            shutil.move(str(backup_dir), str(claude_dir))
        raise InitializationError(f"Initialization failed: {e}. Configuration restored from backup.")

def create_environment(name: str, source: str = "default") -> None:
    """Create a new environment by copying from source environment or GitHub URL"""
    logger.info(f"Creating environment '{name}' from '{source}'")
    envs_dir = get_envs_dir()

    # Check if initialized
    if not envs_dir.exists():
        logger.error("cenv not initialized")
        raise InitializationError("cenv not initialized. Run 'cenv init' first.")

    # Check if environment already exists
    target_env = get_env_path(name)
    if target_env.exists():
        logger.error(f"Environment '{name}' already exists")
        raise EnvironmentExistsError(name)

    # Check if source is a GitHub URL
    if source.startswith("https://") or source.startswith("git@"):
        if not is_valid_github_url(source):
            logger.error(f"Invalid GitHub URL: {source}")
            raise ValueError(f"Invalid GitHub URL: {source}")

        logger.info(f"Cloning from GitHub: {source}")
        clone_from_github(source, target_env)
    else:
        # Source is an environment name
        source_env = get_env_path(source)
        if not source_env.exists():
            logger.error(f"Source environment '{source}' not found")
            raise EnvironmentNotFoundError(source)

        # Copy source to target
        logger.debug(f"Copying {source_env} to {target_env}")
        shutil.copytree(source_env, target_env, symlinks=True)

    logger.info(f"Environment '{name}' created successfully")

def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment"""
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

    # Remove existing symlink
    if claude_dir.is_symlink():
        logger.debug(f"Removing existing symlink at {claude_dir}")
        claude_dir.unlink()
    elif claude_dir.exists():
        logger.error(f"{claude_dir} exists but is not a symlink")
        raise RuntimeError("~/.claude exists but is not a symlink. Cannot switch.")

    # Create new symlink
    logger.debug(f"Creating symlink {claude_dir} -> {target_env}")
    claude_dir.symlink_to(target_env)
    logger.info(f"Switched to environment '{name}'")

def delete_environment(name: str) -> None:
    """Delete an environment"""
    logger.info(f"Deleting environment '{name}'")
    target_env = get_env_path(name)

    # Check if environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise EnvironmentNotFoundError(name)

    # Check if it's currently active
    current = get_current_environment()
    if current == name:
        logger.error(f"Cannot delete active environment '{name}'")
        raise RuntimeError(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )

    # Check if it's the default environment
    if name == "default":
        logger.error("Cannot delete default environment")
        raise RuntimeError("Cannot delete default environment.")

    # Delete the environment
    logger.debug(f"Removing directory {target_env}")
    shutil.rmtree(target_env)
    logger.info(f"Environment '{name}' deleted")
