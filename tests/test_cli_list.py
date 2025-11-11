# ABOUTME: Tests for CLI list, current, and delete commands
# ABOUTME: Verifies output formatting and confirmation prompts
import pytest
from click.testing import CliRunner
from cenv.cli import cli
from cenv.exceptions import EnvironmentNotFoundError
from unittest.mock import patch

def test_list_command_shows_all_environments():
    """Test that 'cenv list' shows all environments"""
    runner = CliRunner()

    with patch("cenv.cli.list_environments", return_value=["default", "work", "personal"]):
        with patch("cenv.cli.get_current_environment", return_value="work"):
            result = runner.invoke(cli, ["list"])

            assert result.exit_code == 0
            assert "default" in result.output
            assert "work" in result.output
            assert "personal" in result.output
            # Current environment should be marked
            assert "*" in result.output or "→" in result.output

def test_list_command_shows_empty_message():
    """Test that list shows message when no environments exist"""
    runner = CliRunner()

    with patch("cenv.cli.list_environments", return_value=[]):
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No environments" in result.output or "cenv init" in result.output

def test_current_command_shows_active_environment():
    """Test that 'cenv current' shows active environment"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value="work"):
        result = runner.invoke(cli, ["current"])

        assert result.exit_code == 0
        assert "work" in result.output

def test_current_command_shows_not_initialized():
    """Test that current shows message when not initialized"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value=None):
        result = runner.invoke(cli, ["current"])

        assert result.exit_code == 0
        assert "not initialized" in result.output or "cenv init" in result.output

def test_delete_command_removes_environment():
    """Test that 'cenv delete work' removes environment"""
    runner = CliRunner()

    with patch("cenv.cli.delete_environment") as mock_delete:
        # User confirms with 'y'
        result = runner.invoke(cli, ["delete", "work"], input="y\n")

        assert result.exit_code == 0
        mock_delete.assert_called_once_with("work")
        assert "Deleted" in result.output

def test_delete_command_prompts_for_confirmation():
    """Test that delete prompts for confirmation"""
    runner = CliRunner()

    with patch("cenv.cli.delete_environment") as mock_delete:
        # User declines with 'n'
        result = runner.invoke(cli, ["delete", "work"], input="n\n")

        assert result.exit_code == 0
        mock_delete.assert_not_called()
        assert "Cancelled" in result.output

def test_delete_command_with_force_skips_prompt():
    """Test that --force flag skips confirmation"""
    runner = CliRunner()

    with patch("cenv.cli.delete_environment") as mock_delete:
        result = runner.invoke(cli, ["delete", "work", "--force"])

        assert result.exit_code == 0
        mock_delete.assert_called_once_with("work")

def test_delete_command_shows_error_if_not_exists():
    """Test that delete shows error if environment doesn't exist"""
    runner = CliRunner()

    with patch("cenv.cli.delete_environment", side_effect=EnvironmentNotFoundError("nonexistent")):
        result = runner.invoke(cli, ["delete", "nonexistent"], input="y\n")

        assert result.exit_code == 1
        assert "Error" in result.output
