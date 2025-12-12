# ABOUTME: Tests for CLI publish command
# ABOUTME: Verifies publish command calls core function and formats output
from unittest.mock import patch

from typer.testing import CliRunner

from cenv.cli import cli
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
