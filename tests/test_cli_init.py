# ABOUTME: Tests for CLI init command
# ABOUTME: Verifies init command calls core init_environments and handles errors
import pytest
from click.testing import CliRunner
from cenv.cli import cli
from unittest.mock import patch

def test_init_command_calls_init_environments():
    """Test that 'cenv init' calls init_environments"""
    runner = CliRunner()

    with patch("cenv.cli.init_environments") as mock_init:
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        mock_init.assert_called_once()
        assert "Initialized" in result.output

def test_init_command_shows_error_if_already_initialized():
    """Test that init shows error if already initialized"""
    runner = CliRunner()

    with patch("cenv.cli.init_environments", side_effect=RuntimeError("already initialized")):
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 1
        assert "Error" in result.output
