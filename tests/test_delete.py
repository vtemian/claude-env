# ABOUTME: Tests for environment deletion functionality
# ABOUTME: Verifies deletion safety checks and directory removal
import pytest
from pathlib import Path
from cenv.core import (
    delete_environment,
    get_trash_dir,
    restore_from_trash,
    list_trash,
    init_environments,
    create_environment,
)
from cenv.exceptions import (
    EnvironmentNotFoundError,
    ActiveEnvironmentError,
    ProtectedEnvironmentError,
)
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
    with pytest.raises(ActiveEnvironmentError):
        delete_environment("default")

def test_delete_environment_raises_if_default(multi_env_setup):
    """Test that deleting default environment raises error"""
    with patch("cenv.core.get_current_environment", return_value="work"):
        with pytest.raises(ProtectedEnvironmentError):
            delete_environment("default")

def test_get_trash_dir_returns_correct_path():
    """Test that trash directory is ~/.claude-envs/.trash"""
    result = get_trash_dir()
    assert result == Path.home() / ".claude-envs" / ".trash"

def test_delete_creates_backup_in_trash(tmp_path, monkeypatch):
    """Test that delete creates timestamped backup in trash"""
    # Setup
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Delete should create backup
    delete_environment("test-env")

    trash_dir = get_trash_dir()
    assert trash_dir.exists()

    # Should have one backup with timestamp
    backups = list(trash_dir.iterdir())
    assert len(backups) == 1
    assert backups[0].name.startswith("test-env-")

def test_list_trash_returns_backups(tmp_path, monkeypatch):
    """Test listing trash backups"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")
    delete_environment("test-env")

    backups = list_trash()
    assert len(backups) == 1
    assert backups[0]["name"] == "test-env"
    assert "timestamp" in backups[0]

def test_restore_from_trash(tmp_path, monkeypatch):
    """Test restoring environment from trash"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Create a marker file
    test_file = tmp_path / ".claude-envs" / "test-env" / "marker.txt"
    test_file.write_text("test content")

    delete_environment("test-env")

    # Environment should be gone
    env_path = tmp_path / ".claude-envs" / "test-env"
    assert not env_path.exists()

    # Get backup name
    backups = list_trash()
    backup_name = backups[0]["backup_name"]

    # Restore
    restore_from_trash(backup_name)

    # Should be restored
    assert env_path.exists()
    restored_file = env_path / "marker.txt"
    assert restored_file.exists()
    assert restored_file.read_text() == "test content"
