from pathlib import Path

import pytest

from cenv.core import (
    SHARED_ITEMS,
    get_claude_dir,
    get_env_path,
    get_envs_dir,
    get_shared_dir,
    setup_shared_symlinks,
    switch_environment,
)


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
        with patch.object(Path, "replace", failing_replace):
            with pytest.raises(OSError):
                switch_environment("test")

    # Verify error was logged with exception details
    assert any(
        "Switch failed" in record.message and "Simulated I/O error" in record.message
        for record in caplog.records
        if record.levelname == "ERROR"
    ), "Expected error log with exception details"


def test_get_shared_dir_returns_correct_path():
    """Test that shared directory path is ~/.claude-envs/.shared"""
    result = get_shared_dir()
    assert result == Path.home() / ".claude-envs" / ".shared"


def test_setup_shared_symlinks_moves_projects_to_shared(tmp_path, monkeypatch):
    """Test that projects directory is moved to shared and symlinked"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    shared_dir = envs_dir / ".shared"

    env_path = envs_dir / "test-env"
    env_path.mkdir()

    # Create a projects directory with content
    projects_dir = env_path / "projects"
    projects_dir.mkdir()
    (projects_dir / "myproject").mkdir()
    (projects_dir / "myproject" / "config.json").write_text("{}")

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    setup_shared_symlinks(env_path)

    # Verify projects was moved to shared
    assert (shared_dir / "projects").exists()
    assert (shared_dir / "projects" / "myproject" / "config.json").exists()

    # Verify symlink was created
    assert (env_path / "projects").is_symlink()
    assert (env_path / "projects").resolve() == shared_dir / "projects"


def test_setup_shared_symlinks_creates_symlink_to_existing_shared(tmp_path, monkeypatch):
    """Test that symlink is created when shared item already exists"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    shared_dir = envs_dir / ".shared"
    shared_dir.mkdir()

    # Create shared projects first
    shared_projects = shared_dir / "projects"
    shared_projects.mkdir()
    (shared_projects / "existing-project").mkdir()

    env_path = envs_dir / "new-env"
    env_path.mkdir()

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    setup_shared_symlinks(env_path)

    # Verify symlink was created
    assert (env_path / "projects").is_symlink()
    assert (env_path / "projects" / "existing-project").exists()


def test_setup_shared_symlinks_handles_credentials_file(tmp_path, monkeypatch):
    """Test that .credentials.json file is moved to shared and symlinked"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    shared_dir = envs_dir / ".shared"

    env_path = envs_dir / "test-env"
    env_path.mkdir()

    # Create credentials file
    creds_file = env_path / ".credentials.json"
    creds_file.write_text('{"token": "secret"}')

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    setup_shared_symlinks(env_path)

    # Verify credentials was moved to shared
    assert (shared_dir / ".credentials.json").exists()
    assert (shared_dir / ".credentials.json").read_text() == '{"token": "secret"}'

    # Verify symlink was created
    assert (env_path / ".credentials.json").is_symlink()


def test_setup_shared_symlinks_skips_nonexistent_items(tmp_path, monkeypatch):
    """Test that setup doesn't fail when shared items don't exist"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()

    env_path = envs_dir / "empty-env"
    env_path.mkdir()

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    # Should not raise
    setup_shared_symlinks(env_path)

    # No symlinks should be created
    for item in SHARED_ITEMS:
        assert not (env_path / item).exists()


def test_setup_shared_symlinks_idempotent(tmp_path, monkeypatch):
    """Test that setup can be run multiple times safely"""
    envs_dir = tmp_path / ".claude-envs"
    envs_dir.mkdir()
    shared_dir = envs_dir / ".shared"
    shared_dir.mkdir()

    # Create shared projects
    shared_projects = shared_dir / "projects"
    shared_projects.mkdir()

    env_path = envs_dir / "test-env"
    env_path.mkdir()

    monkeypatch.setattr("cenv.core.get_envs_dir", lambda: envs_dir)

    # Run twice
    setup_shared_symlinks(env_path)
    setup_shared_symlinks(env_path)

    # Should still work
    assert (env_path / "projects").is_symlink()
    assert (env_path / "projects").resolve() == shared_projects
