# ABOUTME: Test suite for CLI use command functionality
# ABOUTME: Tests environment switching via CLI with confirmation prompts and --force flag
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cenv.cli import cli
from cenv.exceptions import EnvironmentNotFoundError


def test_use_command_switches_environment():
    """Test that 'cenv use work' switches to work environment"""
    runner = CliRunner()

    with patch("cenv.cli.is_claude_running", return_value=False):
        with patch("cenv.cli.switch_environment") as mock_switch:
            result = runner.invoke(cli, ["use", "work"])

            assert result.exit_code == 0
            mock_switch.assert_called_once_with("work", force=False)
            assert "Switched" in result.output

def test_use_command_prompts_if_claude_running():
    """Test that use prompts for confirmation if Claude is running"""
    runner = CliRunner()

    with patch("cenv.cli.is_claude_running", return_value=True):
        with patch("cenv.cli.switch_environment") as mock_switch:
            # User confirms with 'y'
            result = runner.invoke(cli, ["use", "work"], input="y\n")

            assert result.exit_code == 0
            mock_switch.assert_called_once_with("work", force=True)
            assert "Claude is running" in result.output

def test_use_command_cancels_if_user_declines():
    """Test that use cancels if user declines confirmation"""
    runner = CliRunner()

    with patch("cenv.cli.is_claude_running", return_value=True):
        with patch("cenv.cli.switch_environment") as mock_switch:
            # User declines with 'n'
            result = runner.invoke(cli, ["use", "work"], input="n\n")

            assert result.exit_code == 0
            mock_switch.assert_not_called()
            assert "Cancelled" in result.output

def test_use_command_with_force_flag_skips_prompt():
    """Test that --force flag skips confirmation prompt"""
    runner = CliRunner()

    with patch("cenv.cli.is_claude_running", return_value=True):
        with patch("cenv.cli.switch_environment") as mock_switch:
            result = runner.invoke(cli, ["use", "work", "--force"])

            assert result.exit_code == 0
            mock_switch.assert_called_once_with("work", force=True)
            # Should not prompt
            assert "Claude is running" not in result.output

def test_use_command_shows_error_if_env_not_exists():
    """Test that use shows error if environment doesn't exist"""
    runner = CliRunner()

    with patch("cenv.cli.is_claude_running", return_value=False):
        with patch("cenv.cli.switch_environment", side_effect=EnvironmentNotFoundError("nonexistent")):
            result = runner.invoke(cli, ["use", "nonexistent"])

            assert result.exit_code == 1
            assert "Error" in result.output
