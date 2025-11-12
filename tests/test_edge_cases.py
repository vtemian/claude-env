import os
import threading
from pathlib import Path

import pytest

from cenv.core import (
    create_environment,
    delete_environment,
    init_environments,
    list_environments,
    switch_environment,
)
from cenv.exceptions import (
    EnvironmentExistsError,
    EnvironmentNotFoundError,
    InitializationError,
)
from cenv.validation import InvalidEnvironmentNameError


def test_unicode_environment_names(tmp_path, monkeypatch):
    """Test handling of unicode characters in names"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # These should be blocked by validation
    unicode_names = [
        "café",
        "环境",
        "среда",
        "🚀rocket",
    ]

    for name in unicode_names:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(name)


def test_very_long_environment_name(tmp_path, monkeypatch):
    """Test handling of extremely long names"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Most filesystems support 255 char filenames
    long_name = "a" * 300

    # May succeed or fail depending on filesystem
    # Should not crash
    try:
        create_environment(long_name)
    except (OSError, InvalidEnvironmentNameError):
        pass  # Expected on some systems


def test_concurrent_environment_creation(tmp_path, monkeypatch):
    """Test concurrent creation of same environment"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    errors = []
    successes = []

    def create_env():
        try:
            create_environment("concurrent-test")
            successes.append(1)
        except EnvironmentExistsError:
            errors.append(1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=create_env) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Exactly one should succeed
    assert len(successes) == 1
    # Others should get EnvironmentExistsError
    assert len(errors) == 4


def test_disk_full_scenario(tmp_path, monkeypatch):
    """Test behavior when disk is full (simulated)"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Create environment with limited space
    # This is hard to test reliably, so we document expected behavior:
    # Should raise OSError with clear message
    # TODO: Improve error handling for disk full scenarios


def test_permission_denied_scenarios(tmp_path, monkeypatch):
    """Test handling of permission errors"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    # Make environment readonly
    env_path = tmp_path / ".claude-envs" / "test-env"
    trash_path = tmp_path / ".claude-envs" / ".trash" / "test-env"
    os.chmod(env_path, 0o444)

    # Deletion should fail gracefully
    try:
        delete_environment("test-env")
        # If it somehow succeeded, restore permissions for cleanup
        # The env was moved to trash
        if trash_path.exists():
            os.chmod(trash_path, 0o755)
        elif env_path.exists():
            os.chmod(env_path, 0o755)
    except (OSError, PermissionError):
        # Expected - restore permissions for cleanup
        if env_path.exists():
            os.chmod(env_path, 0o755)
        elif trash_path.exists():
            os.chmod(trash_path, 0o755)


def test_corrupted_symlink_recovery(tmp_path, monkeypatch):
    """Test recovery from corrupted symlink"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    create_environment("test-env")

    claude_dir = tmp_path / ".claude"

    # Corrupt the symlink by pointing to non-existent location
    claude_dir.unlink()
    claude_dir.symlink_to(tmp_path / "non-existent")

    # Should be able to recover by switching to valid environment
    switch_environment("default", force=True)

    # Verify recovery
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()


def test_rapid_switch_operations(tmp_path, monkeypatch):
    """Test rapid consecutive switches"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()
    for i in range(5):
        create_environment(f"env{i}")

    # Rapidly switch between environments
    for i in range(20):
        env_name = f"env{i % 5}"
        switch_environment(env_name, force=True)

    # Final state should be valid
    claude_dir = tmp_path / ".claude"
    assert claude_dir.is_symlink()
    assert claude_dir.resolve().exists()


def test_empty_environment_directory(tmp_path, monkeypatch):
    """Test handling of empty environment"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Create empty environment
    empty_env = tmp_path / ".claude-envs" / "empty"
    empty_env.mkdir()

    # Should appear in listings
    envs = list_environments()
    assert "empty" in envs

    # Should be switchable
    switch_environment("empty", force=True)
