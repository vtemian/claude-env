from unittest.mock import patch

import pytest

from cenv.core import create_environment
from cenv.exceptions import (
    EnvironmentExistsError,
    EnvironmentNotFoundError,
    GitOperationError,
    InitializationError,
)


@pytest.fixture
def initialized_envs(monkeypatch, tmp_path):
    """Setup initialized environment structure"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()

    default_env = envs_dir / "default"
    default_env.mkdir()
    (default_env / "CLAUDE.md").write_text("# Default")
    (default_env / "settings.json").write_text('{"test": true}')
    agents_dir = default_env / "agents"
    agents_dir.mkdir()
    (agents_dir / "test.md").write_text("# Agent")

    claude_dir = tmp_path / ".claude"
    claude_dir.symlink_to(default_env)

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)
    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_dir)

    return {"envs": envs_dir, "claude": claude_dir, "default": default_env}

def test_create_environment_copies_from_default(initialized_envs):
    """Test creating environment copies from default"""
    create_environment("work")

    work_env = initialized_envs["envs"] / "work"
    assert work_env.exists()
    assert (work_env / "CLAUDE.md").read_text() == "# Default"
    assert (work_env / "settings.json").read_text() == '{"test": true}'
    assert (work_env / "agents" / "test.md").exists()

def test_create_environment_raises_if_exists(initialized_envs):
    """Test that creating existing environment raises error"""
    create_environment("work")

    with pytest.raises(EnvironmentExistsError, match="already exists"):
        create_environment("work")

def test_create_environment_raises_if_not_initialized(monkeypatch, tmp_path):
    """Test that create raises if not initialized"""
    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: tmp_path / ".claude-envs")

    with pytest.raises(InitializationError, match="not initialized"):
        create_environment("work")

def test_create_environment_raises_if_default_missing(initialized_envs):
    """Test that create raises if default environment doesn't exist"""
    import shutil
    shutil.rmtree(initialized_envs["envs"] / "default")

    with pytest.raises(EnvironmentNotFoundError, match="default"):
        create_environment("work")

def test_create_environment_from_github_url(initialized_envs):
    """Test creating environment from GitHub repository"""
    with patch("cenv.core.clone_from_github") as mock_clone:
        with patch("cenv.core.is_valid_github_url", return_value=True):
            create_environment("work", source="https://github.com/user/repo")

            work_env = initialized_envs["envs"] / "work"
            mock_clone.assert_called_once_with("https://github.com/user/repo", work_env)

def test_create_environment_validates_github_url(initialized_envs):
    """Test that invalid GitHub URL raises error"""
    with patch("cenv.core.is_valid_github_url", return_value=False):
        with pytest.raises(GitOperationError, match="Invalid GitHub URL format"):
            create_environment("work", source="https://not-a-valid-github-url.com")
