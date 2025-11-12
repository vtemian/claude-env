# ABOUTME: Tests for environment switching functionality
# ABOUTME: Verifies symlink management, process detection, and safety checks
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from cenv.core import create_environment, init_environments, switch_environment
from cenv.exceptions import ClaudeRunningError, EnvironmentNotFoundError


@pytest.fixture
def multi_env_setup(monkeypatch, tmp_path):
    """Setup with multiple environments"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()

    for env_name in ["default", "work", "personal"]:
        env_dir = envs_dir / env_name
        env_dir.mkdir()
        (env_dir / "CLAUDE.md").write_text(f"# {env_name}")

    claude_dir = tmp_path / ".claude"
    claude_dir.symlink_to(envs_dir / "default")

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)
    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_dir)

    return {"envs": envs_dir, "claude": claude_dir}

def test_switch_environment_updates_symlink(multi_env_setup):
    """Test that switching updates ~/.claude symlink"""
    with patch("cenv.core.is_claude_running", return_value=False):
        switch_environment("work", force=True)

    assert multi_env_setup["claude"].resolve() == multi_env_setup["envs"] / "work"

def test_switch_environment_raises_if_not_exists(multi_env_setup):
    """Test that switching to non-existent env raises error"""
    with patch("cenv.core.is_claude_running", return_value=False):
        with pytest.raises(EnvironmentNotFoundError, match="does not exist"):
            switch_environment("nonexistent", force=True)

def test_switch_environment_raises_if_claude_running_without_force(multi_env_setup):
    """Test that switching raises if Claude running and force=False"""
    with patch("cenv.core.is_claude_running", return_value=True):
        with pytest.raises(ClaudeRunningError, match="Claude"):
            switch_environment("work", force=False)

def test_switch_environment_succeeds_if_claude_running_with_force(multi_env_setup):
    """Test that switching works if Claude running but force=True"""
    with patch("cenv.core.is_claude_running", return_value=True):
        switch_environment("work", force=True)

    assert multi_env_setup["claude"].resolve() == multi_env_setup["envs"] / "work"

def test_switch_environment_removes_existing_symlink(multi_env_setup):
    """Test that switching removes old symlink correctly"""
    with patch("cenv.core.is_claude_running", return_value=False):
        switch_environment("work", force=True)
        assert multi_env_setup["claude"].resolve() == multi_env_setup["envs"] / "work"

        switch_environment("personal", force=True)
        assert multi_env_setup["claude"].resolve() == multi_env_setup["envs"] / "personal"


def test_switch_is_atomic(tmp_path, monkeypatch):
    """Test that switch operation is atomic - no intermediate broken state"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    # Setup
    init_environments()
    create_environment("test-env")

    # Track symlink state at every moment
    states = []

    def monitor_symlink():
        """Monitor thread that checks symlink state"""
        claude_dir = tmp_path / ".claude"
        for _ in range(100):
            if claude_dir.exists():
                if claude_dir.is_symlink():
                    target = claude_dir.resolve()
                    states.append(("valid", target.name))
                else:
                    states.append(("broken", "not-symlink"))
            else:
                states.append(("broken", "missing"))
            # Small sleep to catch any intermediate state
            import time
            time.sleep(0.001)

    # Start monitoring in background
    monitor = threading.Thread(target=monitor_symlink, daemon=True)
    monitor.start()

    # Perform switch
    with patch("cenv.core.is_claude_running", return_value=False):
        switch_environment("test-env")

    monitor.join(timeout=2)

    # Verify: ALL states should be valid (no broken intermediate state)
    broken_states = [s for s in states if s[0] == "broken"]
    assert len(broken_states) == 0, f"Found broken intermediate states: {broken_states}"


def test_switch_handles_concurrent_operations(tmp_path, monkeypatch):
    """Test that concurrent switches don't corrupt state"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    # Setup multiple environments
    init_environments()
    for i in range(3):
        create_environment(f"env{i}")

    errors = []

    def switch_env(name):
        try:
            with patch("cenv.core.is_claude_running", return_value=False):
                switch_environment(name, force=True)
        except Exception as e:
            errors.append(e)

    # Launch concurrent switches
    threads = [
        threading.Thread(target=switch_env, args=(f"env{i}",))
        for i in range(3)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should complete without errors
    assert len(errors) == 0, f"Got errors: {errors}"

    # Final state should be valid
    claude_dir = tmp_path / ".claude"
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()
