# ABOUTME: Tests for CLI publish command
# ABOUTME: Verifies publish command calls core function and formats output
from unittest.mock import patch

from typer.testing import CliRunner

from cenv.cli import cli
from cenv.exceptions import GitOperationError
from cenv.publish import PublishResult


def test_publish_command_calls_publish_environment():
    """Test that 'cenv publish' calls publish_environment"""
    runner = CliRunner()

    mock_result = PublishResult(
        success=True,
        files_published=5,
        files_excluded=2,
        excluded_files=["credentials.json", ".env"],
    )

    with patch("cenv.cli.get_current_environment", return_value="work"):
        with patch("cenv.cli.publish_environment", return_value=mock_result) as mock_publish:
            result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

            assert result.exit_code == 0
            mock_publish.assert_called_once_with("https://github.com/user/repo")
            assert "Published" in result.output


def test_publish_command_shows_excluded_count():
    """Test that publish shows count of excluded files"""
    runner = CliRunner()

    mock_result = PublishResult(
        success=True,
        files_published=3,
        files_excluded=2,
        excluded_files=["credentials.json", ".env"],
    )

    with patch("cenv.cli.publish_environment", return_value=mock_result):
        with patch("cenv.cli.get_current_environment", return_value="work"):
            result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

            assert result.exit_code == 0
            assert "Excluded 2 sensitive file(s)" in result.output


def test_publish_command_shows_error_on_failure():
    """Test that publish shows error message on git failure"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value="work"):
        with patch(
            "cenv.cli.publish_environment",
            side_effect=GitOperationError("push", "url", "Push failed"),
        ):
            result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

            assert result.exit_code == 1
            assert "Error" in result.output


def test_publish_command_shows_error_when_not_initialized():
    """Test that publish shows error when not initialized"""
    runner = CliRunner()

    with patch("cenv.cli.get_current_environment", return_value=None):
        result = runner.invoke(cli, ["publish", "https://github.com/user/repo"])

        assert result.exit_code == 1
        assert "No active environment" in result.output
