from pathlib import Path

import pytest

from cenv.core import get_claude_dir, get_env_path, get_envs_dir, switch_environment


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

def test_switch_environment_logs_error_on_failure(tmp_path, caplog, monkeypatch):
    """Test that switch_environment logs detailed error when cleanup is needed."""
    import logging
    from unittest.mock import patch

    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()

    # Create environments
    default_env = envs_dir / "default"
    default_env.mkdir()

    test_env = envs_dir / "test"
    test_env.mkdir()

    # Create active symlink
    claude_dir = tmp_path / ".claude"
    claude_dir.symlink_to(default_env)

    # Mock paths
    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)
    monkeypatch.setattr("cenv.core.get_claude_dir", lambda: claude_dir)

    # Mock Path.replace to raise error after symlink is created

    def failing_replace(self, target):
        # Simulate failure during atomic replace
        raise OSError("Simulated I/O error during replace")

    # Capture logs
    with caplog.at_level(logging.ERROR):
        with patch.object(Path, 'replace', failing_replace):
            with pytest.raises(OSError):
                switch_environment("test")

    # Verify error was logged with exception details
    assert any(
        "Switch failed" in record.message and "Simulated I/O error" in record.message
        for record in caplog.records
        if record.levelname == "ERROR"
    ), "Expected error log with exception details"
