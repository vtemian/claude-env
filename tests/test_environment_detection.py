from pathlib import Path
from cenv.core import list_environments, get_current_environment, environment_exists
import tempfile
import pytest

@pytest.fixture
def mock_envs_dir(monkeypatch, tmp_path):
    """Create a temporary envs directory for testing"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)
    return envs_dir

def test_list_environments_returns_empty_when_no_envs(mock_envs_dir):
    """Test listing environments when none exist"""
    result = list_environments()
    assert result == []

def test_list_environments_returns_all_directories(mock_envs_dir):
    """Test listing returns all environment directories"""
    (mock_envs_dir / "work").mkdir()
    (mock_envs_dir / "personal").mkdir()
    (mock_envs_dir / "default").mkdir()

    result = sorted(list_environments())
    assert result == ["default", "personal", "work"]

def test_list_environments_ignores_files(mock_envs_dir):
    """Test that files are ignored, only directories counted"""
    (mock_envs_dir / "work").mkdir()
    (mock_envs_dir / "readme.txt").touch()

    result = list_environments()
    assert result == ["work"]

def test_get_current_environment_when_symlink_exists(monkeypatch, tmp_path):
    """Test detecting current environment from symlink"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    work_dir = envs_dir / "work"
    work_dir.mkdir()

    claude_link = tmp_path / ".claude"
    claude_link.symlink_to(work_dir)

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)
    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_link)

    result = get_current_environment()
    assert result == "work"

def test_get_current_environment_returns_none_when_no_symlink(monkeypatch, tmp_path):
    """Test returns None when ~/.claude is not a symlink"""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_dir)

    result = get_current_environment()
    assert result is None

def test_environment_exists_returns_true_when_exists(mock_envs_dir):
    """Test environment existence check"""
    (mock_envs_dir / "work").mkdir()

    assert environment_exists("work") is True

def test_environment_exists_returns_false_when_not_exists(mock_envs_dir):
    """Test environment existence check for missing env"""
    assert environment_exists("nonexistent") is False
