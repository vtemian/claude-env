# ABOUTME: Logging configuration for cenv
# ABOUTME: Provides centralized logging setup with file and console handlers
"""Logging configuration for cenv"""
import logging
import sys
import threading
from pathlib import Path
from typing import Optional

__all__ = [
    'setup_logging',
    'get_logger',
    'reset_logging_config',
]


_configured = False
_config_lock = threading.Lock()


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> None:
    """Configure logging for cenv (thread-safe)

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output

    Thread Safety:
        This function is thread-safe. Multiple concurrent calls will
        result in exactly one configuration being applied.
    """
    global _configured

    # Thread-safe check and configuration
    with _config_lock:
        # Check again inside lock (double-checked locking pattern)
        if _configured:
            return

        # Configure root logger for cenv
        logger = logging.getLogger("cenv")

        # Clear any existing handlers
        logger.handlers.clear()
        logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        _configured = True


def reset_logging_config() -> None:
    """Reset logging configuration (for testing purposes)

    Thread Safety:
        This function is thread-safe.
    """
    global _configured
    with _config_lock:
        _configured = False
        logger = logging.getLogger("cenv")
        logger.handlers.clear()


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Thread Safety:
        This function is thread-safe.
    """
    return logging.getLogger(f"cenv.{name}" if not name.startswith("cenv") else name)
