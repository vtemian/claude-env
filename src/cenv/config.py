# ABOUTME: Configuration management for cenv
# ABOUTME: Loads settings from environment variables and config files
"""Configuration management for cenv"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

__all__ = [
    'Config',
    'load_config',
    'get_config',
]


# Default configuration values
DEFAULT_GIT_TIMEOUT = 300  # 5 minutes
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TRASH_DIR_NAME = ".trash"
DEFAULT_LOCK_FILE_NAME = "cenv-init.lock"


@dataclass
class Config:
    """Configuration for cenv operations"""

    # Git operation timeout in seconds
    git_timeout: int = DEFAULT_GIT_TIMEOUT

    # Logging level
    log_level: str = DEFAULT_LOG_LEVEL

    # Directory names (usually shouldn't be changed)
    trash_dir_name: str = DEFAULT_TRASH_DIR_NAME
    lock_file_name: str = DEFAULT_LOCK_FILE_NAME


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from environment and optional config file

    Args:
        config_file: Optional path to config file

    Returns:
        Config object with merged settings

    Configuration precedence (highest to lowest):
        1. Environment variables (CENV_*)
        2. Config file (~/.cenvrc or specified file)
        3. Defaults

    Environment variables:
        CENV_GIT_TIMEOUT: Git operation timeout in seconds (default: 300)
        CENV_LOG_LEVEL: Logging level (default: INFO)

    Config file format (~/.cenvrc):
        git_timeout = 600
        log_level = DEBUG
    """
    config = Config()

    # Load from config file if it exists
    if config_file is None:
        config_file = Path.home() / ".cenvrc"

    if config_file.exists():
        try:
            content = config_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == 'git_timeout':
                        try:
                            config.git_timeout = int(value)
                        except ValueError:
                            pass  # Use default
                    elif key == 'log_level':
                        config.log_level = value.upper()
        except Exception:
            # If config file is malformed, use defaults
            pass

    # Environment variables override config file
    if 'CENV_GIT_TIMEOUT' in os.environ:
        try:
            config.git_timeout = int(os.environ['CENV_GIT_TIMEOUT'])
        except ValueError:
            pass  # Use default

    if 'CENV_LOG_LEVEL' in os.environ:
        config.log_level = os.environ['CENV_LOG_LEVEL'].upper()

    return config


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance (singleton)

    Returns:
        Global Config instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
