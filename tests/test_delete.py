# ABOUTME: Tests for environment deletion functionality
# ABOUTME: Verifies deletion safety checks and directory removal
import pytest
from cenv.core import delete_environment
from cenv.exceptions import EnvironmentNotFoundError
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

def test_delete_environment_removes_directory(multi_env_setup):
    """Test that deleting removes the environment directory"""
    delete_environment("work")

    assert not (multi_env_setup["envs"] / "work").exists()
    assert (multi_env_setup["envs"] / "default").exists()
    assert (multi_env_setup["envs"] / "personal").exists()

def test_delete_environment_raises_if_not_exists(multi_env_setup):
    """Test that deleting non-existent env raises error"""
    with pytest.raises(EnvironmentNotFoundError, match="does not exist"):
        delete_environment("nonexistent")

def test_delete_environment_raises_if_currently_active(multi_env_setup):
    """Test that deleting active environment raises error"""
    with pytest.raises(RuntimeError, match="currently active"):
        delete_environment("default")

def test_delete_environment_raises_if_default(multi_env_setup):
    """Test that deleting default environment raises error"""
    with patch("cenv.core.get_current_environment", return_value="work"):
        with pytest.raises(RuntimeError, match="Cannot delete default"):
            delete_environment("default")
