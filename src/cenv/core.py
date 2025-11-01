# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional
import shutil
from cenv.process import is_claude_running

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
    claude_dir = get_claude_dir()
    envs_dir = get_envs_dir()
    default_env = get_env_path("default")

    # Check if ~/.claude is already a symlink
    if claude_dir.is_symlink():
        raise RuntimeError("~/.claude is already a symlink. Cannot initialize.")

    # Check if already initialized
    if envs_dir.exists():
        raise RuntimeError("cenv already initialized. ~/.claude-envs exists.")

    # Create backup if claude_dir exists
    backup_dir = None
    if claude_dir.exists() and not claude_dir.is_symlink():
        backup_dir = claude_dir.parent / ".claude.backup"
        shutil.copytree(claude_dir, backup_dir)

    try:
        # Create envs directory
        envs_dir.mkdir(parents=True, exist_ok=True)

        # Move ~/.claude to default environment
        if claude_dir.exists():
            shutil.move(str(claude_dir), str(default_env))
        else:
            # Create empty default environment
            default_env.mkdir(parents=True, exist_ok=True)

        # Create symlink
        claude_dir.symlink_to(default_env)

        # Clean up backup on success
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)

    except Exception as e:
        # Restore from backup if anything failed
        if backup_dir and backup_dir.exists():
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
        raise RuntimeError(f"Initialization failed: {e}. Configuration restored from backup.")

def create_environment(name: str, source: str = "default") -> None:
    """Create a new environment by copying from source environment"""
    envs_dir = get_envs_dir()

    # Check if initialized
    if not envs_dir.exists():
        raise RuntimeError("cenv not initialized. Run 'cenv init' first.")

    # Check if environment already exists
    target_env = get_env_path(name)
    if target_env.exists():
        raise RuntimeError(f"Environment '{name}' already exists.")

    # Check if source environment exists
    source_env = get_env_path(source)
    if not source_env.exists():
        raise RuntimeError(f"{source} environment not found.")

    # Copy source to target
    shutil.copytree(source_env, target_env, symlinks=True)

def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment"""
    target_env = get_env_path(name)

    # Check if target environment exists
    if not target_env.exists():
        raise RuntimeError(f"Environment '{name}' does not exist.")

    # Check if Claude is running
    if is_claude_running() and not force:
        raise RuntimeError(
            "Claude is running. Please exit Claude first or use force=True."
        )

    claude_dir = get_claude_dir()

    # Remove existing symlink
    if claude_dir.is_symlink():
        claude_dir.unlink()
    elif claude_dir.exists():
        raise RuntimeError("~/.claude exists but is not a symlink. Cannot switch.")

    # Create new symlink
    claude_dir.symlink_to(target_env)

def delete_environment(name: str) -> None:
    """Delete an environment"""
    target_env = get_env_path(name)

    # Check if environment exists
    if not target_env.exists():
        raise RuntimeError(f"Environment '{name}' does not exist.")

    # Check if it's currently active
    current = get_current_environment()
    if current == name:
        raise RuntimeError(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )

    # Check if it's the default environment
    if name == "default":
        raise RuntimeError("Cannot delete default environment.")

    # Delete the environment
    shutil.rmtree(target_env)
