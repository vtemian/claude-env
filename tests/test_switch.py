# ABOUTME: Tests for environment switching functionality
# ABOUTME: Verifies symlink management, process detection, and safety checks
import pytest
from pathlib import Path
from cenv.core import switch_environment
from cenv.exceptions import EnvironmentNotFoundError, ClaudeRunningError
from unittest.mock import patch

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
