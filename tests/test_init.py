import pytest
from pathlib import Path
from cenv.core import init_environments
from unittest.mock import patch
import shutil

@pytest.fixture
def mock_dirs(monkeypatch, tmp_path):
    """Mock home directory structure"""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "CLAUDE.md").write_text("# Test")
    (claude_dir / "settings.json").write_text("{}")

    envs_dir = tmp_path / ".claude-envs"

    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_dir)
    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    return {"claude": claude_dir, "envs": envs_dir}

def test_init_creates_envs_directory(mock_dirs):
    """Test that init creates ~/.claude-envs directory"""
    init_environments()
    assert mock_dirs["envs"].exists()
    assert mock_dirs["envs"].is_dir()

def test_init_moves_claude_to_default(mock_dirs):
    """Test that init moves ~/.claude to ~/.claude-envs/default"""
    init_environments()

    default_env = mock_dirs["envs"] / "default"
    assert default_env.exists()
    assert (default_env / "CLAUDE.md").exists()
    assert (default_env / "settings.json").exists()

def test_init_creates_symlink_to_default(mock_dirs):
    """Test that init creates symlink ~/.claude -> default"""
    init_environments()

    assert mock_dirs["claude"].is_symlink()
    assert mock_dirs["claude"].resolve() == mock_dirs["envs"] / "default"

def test_init_raises_if_already_initialized(mock_dirs):
    """Test that init raises error if already initialized"""
    init_environments()

    with pytest.raises(RuntimeError, match="already initialized"):
        init_environments()

def test_init_raises_if_claude_is_already_symlink(mock_dirs):
    """Test that init raises error if ~/.claude is already a symlink"""
    shutil.rmtree(mock_dirs["claude"])
    mock_dirs["claude"].symlink_to(mock_dirs["envs"] / "existing")

    with pytest.raises(RuntimeError, match="already a symlink"):
        init_environments()
