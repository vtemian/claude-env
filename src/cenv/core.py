# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional
import shutil

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

    # Check if already initialized
    if envs_dir.exists():
        raise RuntimeError("cenv already initialized. ~/.claude-envs exists.")

    # Check if ~/.claude is already a symlink
    if claude_dir.is_symlink():
        raise RuntimeError("~/.claude is already a symlink. Cannot initialize.")

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
