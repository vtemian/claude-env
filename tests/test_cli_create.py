# ABOUTME: Tests for CLI create command
# ABOUTME: Verifies create command handles both default and GitHub repo sources
import pytest
from click.testing import CliRunner
from cenv.cli import cli
from cenv.exceptions import EnvironmentExistsError
from unittest.mock import patch

def test_create_command_creates_from_default():
    """Test that 'cenv create work' creates from default"""
    runner = CliRunner()

    with patch("cenv.cli.create_environment") as mock_create:
        result = runner.invoke(cli, ["create", "work"])

        assert result.exit_code == 0
        mock_create.assert_called_once_with("work", source="default")
        assert "Created" in result.output

def test_create_command_creates_from_github_url():
    """Test that 'cenv create work --from-repo URL' clones from GitHub"""
    runner = CliRunner()

    with patch("cenv.cli.create_environment") as mock_create:
        result = runner.invoke(cli, ["create", "work", "--from-repo", "https://github.com/user/repo"])

        assert result.exit_code == 0
        mock_create.assert_called_once_with("work", source="https://github.com/user/repo")

def test_create_command_shows_error_if_exists():
    """Test that create shows error if environment exists"""
    runner = CliRunner()

    with patch("cenv.cli.create_environment", side_effect=EnvironmentExistsError("work")):
        result = runner.invoke(cli, ["create", "work"])

        assert result.exit_code == 1
        assert "Error" in result.output
