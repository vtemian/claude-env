# ABOUTME: Tests for GitHub repository cloning functionality
# ABOUTME: Validates URL validation and git clone subprocess calls
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cenv.exceptions import GitOperationError
from cenv.github import clone_from_github, is_valid_github_url


def test_is_valid_github_url_validates_https():
    """Test GitHub URL validation for HTTPS"""
    assert is_valid_github_url("https://github.com/user/repo") is True
    assert is_valid_github_url("https://github.com/user/repo.git") is True

def test_is_valid_github_url_validates_ssh():
    """Test GitHub URL validation for SSH"""
    assert is_valid_github_url("git@github.com:user/repo.git") is True

def test_is_valid_github_url_rejects_invalid():
    """Test GitHub URL validation rejects invalid URLs"""
    assert is_valid_github_url("not-a-url") is False
    assert is_valid_github_url("https://gitlab.com/user/repo") is False

@patch("subprocess.run")
def test_clone_from_github_calls_git_clone(mock_run):
    """Test that clone_from_github calls git clone"""
    def simulate_git_clone(cmd, **kwargs):
        # Simulate git clone creating the temp directory
        # cmd format: ["git", "clone", "--depth", "1", url, temp_dir]
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])  # Changed from cmd[3] to cmd[5] due to --depth 1
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        return MagicMock(returncode=0)

    mock_run.side_effect = simulate_git_clone

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        clone_from_github("https://github.com/user/repo", target)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "git" in call_args[0][0]
        assert "clone" in call_args[0][0]
        assert "https://github.com/user/repo" in call_args[0][0]

def test_clone_from_github_raises_on_invalid_url():
    """Test that clone raises GitOperationError for invalid URL"""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        with pytest.raises(GitOperationError, match="Invalid GitHub URL"):
            clone_from_github("not-a-url", target)

@patch("subprocess.run")
def test_clone_from_github_raises_on_git_error(mock_run):
    """Test that clone raises GitOperationError if git clone fails"""
    mock_run.return_value = MagicMock(returncode=1, stderr="error")

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        with pytest.raises(GitOperationError, match="clone"):
            clone_from_github("https://github.com/user/repo", target)

@patch("subprocess.run")
def test_clone_from_github_removes_git_directory(mock_run):
    """Test that clone removes .git directory after cloning"""
    def simulate_git_clone(cmd, **kwargs):
        # Simulate git clone creating the temp directory with .git
        # cmd format: ["git", "clone", "--depth", "1", url, temp_dir]
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])  # Changed from cmd[3] to cmd[5] due to --depth 1
            temp_dir.mkdir(parents=True)
            git_dir = temp_dir / ".git"
            git_dir.mkdir()
        return MagicMock(returncode=0)

    mock_run.side_effect = simulate_git_clone

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        clone_from_github("https://github.com/user/repo", target)

        # Verify .git directory was removed
        assert not (target / ".git").exists()
        # Verify target directory was created
        assert target.exists()


def test_clone_uses_timeout(tmp_path):
    """Test that git clone includes timeout parameter"""
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        clone_from_github("https://github.com/user/repo.git", target)

        # Verify timeout was passed
        call_args = mock_run.call_args
        assert call_args.kwargs.get("timeout") is not None
        assert call_args.kwargs["timeout"] > 0


def test_clone_uses_shallow_clone(tmp_path):
    """Test that git clone uses --depth 1 for shallow clone"""
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        clone_from_github("https://github.com/user/repo.git", target)

        # Verify --depth 1 was used
        call_args = mock_run.call_args
        assert "--depth" in call_args.args[0]
        assert "1" in call_args.args[0]


def test_clone_timeout_raises_error(tmp_path):
    """Test that timeout raises GitOperationError"""
    import subprocess
    target = tmp_path / "test-env"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=30)

        with pytest.raises(GitOperationError) as exc_info:
            clone_from_github("https://github.com/user/repo.git", target)

        error_msg = str(exc_info.value).lower()
        assert "timed out" in error_msg or "timeout" in error_msg
