# ABOUTME: Integration tests for full cenv workflow
# ABOUTME: Tests complete user journeys from init through delete
import pytest
from click.testing import CliRunner
from cenv.cli import cli
from pathlib import Path
import tempfile
from unittest.mock import patch

@pytest.fixture
def isolated_home(monkeypatch, tmp_path):
    """Create isolated home directory for testing"""
    home = tmp_path / "home"
    home.mkdir()

    # Create initial ~/.claude
    claude_dir = home / ".claude"
    claude_dir.mkdir()
    (claude_dir / "CLAUDE.md").write_text("# Original")
    (claude_dir / "settings.json").write_text('{"test": true}')

    monkeypatch.setattr("cenv.core.Path.home", lambda: home)

    return home

def test_full_workflow_init_create_use_delete(isolated_home):
    """Test complete workflow: init → create → use → delete"""
    runner = CliRunner()

    with patch("cenv.process.is_claude_running", return_value=False):
        # Step 1: Initialize
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert (isolated_home / ".claude-envs" / "default").exists()
        assert (isolated_home / ".claude").is_symlink()

        # Step 2: Create work environment
        result = runner.invoke(cli, ["create", "work"])
        assert result.exit_code == 0
        assert (isolated_home / ".claude-envs" / "work").exists()

        # Step 3: List environments
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "default" in result.output
        assert "work" in result.output

        # Step 4: Check current (should be default)
        result = runner.invoke(cli, ["current"])
        assert result.exit_code == 0
        assert "default" in result.output

        # Step 5: Switch to work
        result = runner.invoke(cli, ["use", "work"])
        assert result.exit_code == 0
        assert (isolated_home / ".claude").resolve() == (isolated_home / ".claude-envs" / "work")

        # Step 6: Check current (should be work)
        result = runner.invoke(cli, ["current"])
        assert result.exit_code == 0
        assert "work" in result.output

        # Step 7: Switch back to default
        result = runner.invoke(cli, ["use", "default"])
        assert result.exit_code == 0

        # Step 8: Delete work environment
        result = runner.invoke(cli, ["delete", "work", "--force"])
        assert result.exit_code == 0
        assert not (isolated_home / ".claude-envs" / "work").exists()

def test_error_handling_workflow(isolated_home):
    """Test error handling in various scenarios"""
    runner = CliRunner()

    # Cannot create before init
    result = runner.invoke(cli, ["create", "work"])
    assert result.exit_code == 1
    assert "not initialized" in result.output

    # Initialize
    with patch("cenv.process.is_claude_running", return_value=False):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0

    # Cannot init twice
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 1
    assert "already a symlink" in result.output

    # Cannot use non-existent environment
    with patch("cenv.process.is_claude_running", return_value=False):
        result = runner.invoke(cli, ["use", "nonexistent"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    # Cannot delete default environment (need to switch away first)
    with patch("cenv.process.is_claude_running", return_value=False):
        # Create and switch to work environment
        result = runner.invoke(cli, ["create", "work"])
        assert result.exit_code == 0
        result = runner.invoke(cli, ["use", "work"])
        assert result.exit_code == 0

    # Now try to delete default
    result = runner.invoke(cli, ["delete", "default", "--force"])
    assert result.exit_code == 1
    assert "Cannot delete default" in result.output
