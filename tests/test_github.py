# ABOUTME: Tests for GitHub repository cloning functionality
# ABOUTME: Validates URL validation and git clone subprocess calls
import pytest
from pathlib import Path
from cenv.github import clone_from_github, is_valid_github_url
from unittest.mock import patch, MagicMock
import tempfile
import shutil

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
    mock_run.return_value = MagicMock(returncode=0)

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        clone_from_github("https://github.com/user/repo", target)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "git" in call_args[0][0]
        assert "clone" in call_args[0][0]
        assert "https://github.com/user/repo" in call_args[0][0]

@patch("subprocess.run")
def test_clone_from_github_raises_on_git_error(mock_run):
    """Test that clone raises error if git clone fails"""
    mock_run.return_value = MagicMock(returncode=1, stderr="error")

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        with pytest.raises(RuntimeError, match="Failed to clone"):
            clone_from_github("https://github.com/user/repo", target)

@patch("subprocess.run")
def test_clone_from_github_removes_git_directory(mock_run):
    """Test that clone removes .git directory after cloning"""
    mock_run.return_value = MagicMock(returncode=0)

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-env"
        target.mkdir()
        git_dir = target / ".git"
        git_dir.mkdir()

        with patch("cenv.github.Path.exists", return_value=True):
            with patch("shutil.rmtree") as mock_rmtree:
                clone_from_github("https://github.com/user/repo", target)
                # Check that rmtree was called (for .git directory)
                assert mock_rmtree.called
