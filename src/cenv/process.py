# ABOUTME: Process detection for Claude Code to check if it's currently running
# ABOUTME: Uses psutil to find node processes running the claude binary
"""Process detection for Claude Code

This module provides best-effort detection of running Claude Code processes.

LIMITATIONS:
  • Detection is heuristic-based and may not catch all cases
  • Assumes Claude runs as a node process with "bin/claude" in command line
  • May not detect Claude running in Docker, VM, or remote session
  • May not detect Claude installed in non-standard locations
  • Windows detection is not implemented

RECOMMENDATIONS:
  • Users should manually verify Claude is not running before critical operations
  • Use --force flag to bypass detection when you're certain Claude is not running
  • Check for .claude.lock file as additional signal (future enhancement)

The detection prioritizes false negatives over false positives:
  • If uncertain, assumes Claude is NOT running (allows operation)
  • Better to allow operation than unnecessarily block user
"""
from typing import List

import psutil

from cenv.logging_config import get_logger

__all__ = [
    'is_claude_running',
    'get_claude_processes',
]

logger = get_logger(__name__)


def get_claude_processes() -> list[psutil.Process]:
    """Get all running Claude Code processes (best-effort detection)

    Returns:
        List of processes that appear to be Claude Code
        Empty list if detection fails or no processes found

    Note:
        This is heuristic-based detection with known limitations.
        May not detect all Claude installations.
    """
    claude_processes = []

    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                # Access proc.info which may raise AccessDenied
                info = proc.info
                cmdline = info.get("cmdline", [])

                if not cmdline:
                    continue

                # Check if "claude" appears in command line
                if not any("claude" in str(arg).lower() for arg in cmdline):
                    continue

                # Heuristic: Claude Code typically runs as node process
                # This may not catch all installations (electron apps, binaries, etc.)
                if info.get("name") == "node" and any("bin/claude" in str(arg) for arg in cmdline):
                    logger.debug(f"Found potential Claude process: PID {proc.pid}")
                    claude_processes.append(proc)

            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                # Can't access this process - skip it
                # AccessDenied is common for system processes
                continue

    except Exception as e:
        # Log error but don't crash - return empty list
        logger.warning(f"Process detection failed: {e}")
        return []

    return claude_processes


def is_claude_running() -> bool:
    """Check if Claude Code is currently running (best-effort)

    Returns:
        True if Claude appears to be running
        False if Claude is not detected or detection fails

    Note:
        This is best-effort detection with known limitations.
        When uncertain, returns False (fail-safe - allows operation).
        Users should manually verify for critical operations.
        Use --force flag to bypass detection.
    """
    try:
        processes = get_claude_processes()
        is_running = len(processes) > 0

        if is_running:
            logger.info(f"Detected {len(processes)} Claude process(es) running")

        return is_running

    except Exception as e:
        # If detection fails, assume Claude is NOT running
        # Better to allow operation than unnecessarily block user
        logger.warning(f"Process detection error (assuming not running): {e}")
        return False
