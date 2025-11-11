import pytest
from pathlib import Path
from cenv.core import init_environments
from cenv.exceptions import InitializationError
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

    # After successful init, ~/.claude is a symlink, so that error takes precedence
    with pytest.raises(InitializationError, match="already a symlink"):
        init_environments()

def test_init_raises_if_claude_is_already_symlink(mock_dirs):
    """Test that init raises error if ~/.claude is already a symlink"""
    shutil.rmtree(mock_dirs["claude"])
    mock_dirs["claude"].symlink_to(mock_dirs["envs"] / "existing")

    with pytest.raises(InitializationError, match="already a symlink"):
        init_environments()

def test_init_restores_backup_on_failure(mock_dirs):
    """Test that init restores original ~/.claude if operation fails"""
    original_content = (mock_dirs["claude"] / "CLAUDE.md").read_text()

    # Mock symlink_to to fail
    with patch("pathlib.Path.symlink_to", side_effect=OSError("Simulated failure")):
        with pytest.raises(InitializationError, match="Initialization failed"):
            init_environments()

    # Verify ~/.claude was restored
    assert mock_dirs["claude"].exists()
    assert not mock_dirs["claude"].is_symlink()
    assert (mock_dirs["claude"] / "CLAUDE.md").exists()
    assert (mock_dirs["claude"] / "CLAUDE.md").read_text() == original_content

    # Verify envs_dir was cleaned up or never fully created
    # (depending on where the failure occurred)
    if mock_dirs["envs"].exists():
        assert not (mock_dirs["envs"] / "default").exists()

def test_concurrent_init_only_one_succeeds(tmp_path, monkeypatch):
    """Test that concurrent initialization is safe"""
    import threading
    import time

    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    # Create a .claude directory to initialize from
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "test.txt").write_text("test")

    results = []

    def init_thread():
        try:
            init_environments()
            results.append("success")
        except InitializationError:
            results.append("failed")
        except Exception as e:
            results.append(f"error: {type(e).__name__}")

    # Launch multiple threads trying to init
    threads = [threading.Thread(target=init_thread) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Only one should succeed, the rest should fail with InitializationError
    success_count = results.count("success")
    failed_count = results.count("failed")

    assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
    assert failed_count >= 3, f"Expected at least 3 failures (got {failed_count}). Results: {results}"
    assert success_count + failed_count >= 4, f"Expected mostly successes and failures. Results: {results}"
