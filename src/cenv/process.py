# ABOUTME: Process detection for Claude Code to check if it's currently running
# ABOUTME: Uses psutil to find node processes running the claude binary
import psutil
from typing import List

def get_claude_processes() -> List[psutil.Process]:
    """Get all running Claude Code processes"""
    claude_processes = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            # Access proc.info which may raise AccessDenied
            info = proc.info
            cmdline = info.get("cmdline", [])
            if cmdline and any("claude" in str(arg).lower() for arg in cmdline):
                # Platform assumption: Claude Code runs as a node process with "bin/claude" in the command line
                # This detection logic is designed for Unix-like systems where the Claude binary is typically
                # installed in a bin directory and executed via node
                if info.get("name") == "node" and any("bin/claude" in str(arg) for arg in cmdline):
                    claude_processes.append(proc)
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            continue

    return claude_processes

def is_claude_running() -> bool:
    """Check if Claude Code is currently running"""
    return len(get_claude_processes()) > 0
