# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path

def get_envs_dir() -> Path:
    """Get the base directory for all environments"""
    return Path.home() / ".claude-envs"

def get_env_path(name: str) -> Path:
    """Get the path for a specific environment"""
    return get_envs_dir() / name

def get_claude_dir() -> Path:
    """Get the ~/.claude directory path"""
    return Path.home() / ".claude"
