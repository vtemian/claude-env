# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional

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
