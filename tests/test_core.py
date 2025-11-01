from pathlib import Path
from cenv.core import get_envs_dir, get_env_path, get_claude_dir

def test_get_envs_dir_returns_correct_path():
    """Test that envs directory path is ~/.claude-envs"""
    result = get_envs_dir()
    assert result == Path.home() / ".claude-envs"

def test_get_env_path_returns_correct_path():
    """Test that environment path is ~/.claude-envs/<name>"""
    result = get_env_path("work")
    assert result == Path.home() / ".claude-envs" / "work"

def test_get_claude_dir_returns_correct_path():
    """Test that claude dir is ~/.claude"""
    result = get_claude_dir()
    assert result == Path.home() / ".claude"
