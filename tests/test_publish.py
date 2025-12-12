# ABOUTME: Tests for publish functionality
# ABOUTME: Validates sensitive file detection and git push operations
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cenv.exceptions import GitOperationError
from cenv.publish import get_files_to_publish, is_sensitive_file, publish_to_repo


def test_is_sensitive_file_detects_credentials():
    """Test that credentials files are detected as sensitive"""
    assert is_sensitive_file("credentials.json") is True
    assert is_sensitive_file("credentials.local.json") is True


def test_is_sensitive_file_detects_env_files():
    """Test that .env files are detected as sensitive"""
    assert is_sensitive_file(".env") is True
    assert is_sensitive_file(".env.local") is True
    assert is_sensitive_file(".env.production") is True


def test_is_sensitive_file_detects_key_files():
    """Test that key/pem files are detected as sensitive"""
    assert is_sensitive_file("private.key") is True
    assert is_sensitive_file("server.pem") is True


def test_is_sensitive_file_detects_secrets():
    """Test that secret-containing filenames are detected"""
    assert is_sensitive_file("secrets.json") is True
    assert is_sensitive_file("auth.json") is True
    assert is_sensitive_file("tokens.json") is True
    assert is_sensitive_file("my_api_secret.txt") is True
    assert is_sensitive_file("apikey.json") is True


def test_is_sensitive_file_allows_safe_files():
    """Test that normal config files are allowed"""
    assert is_sensitive_file("CLAUDE.md") is False
    assert is_sensitive_file("settings.json") is False
    assert is_sensitive_file("config.json") is False
    assert is_sensitive_file("README.md") is False


def test_get_files_to_publish_excludes_sensitive(tmp_path):
    """Test that sensitive files are excluded from publish list"""
    # Create test environment
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")
    (env_dir / "settings.json").write_text("{}")
    (env_dir / "credentials.json").write_text("secret")
    (env_dir / ".env").write_text("SECRET=value")

    to_publish, excluded = get_files_to_publish(env_dir)

    # Check published files
    published_names = [f.name for f in to_publish]
    assert "CLAUDE.md" in published_names
    assert "settings.json" in published_names

    # Check excluded files
    excluded_names = [f.name for f in excluded]
    assert "credentials.json" in excluded_names
    assert ".env" in excluded_names


def test_get_files_to_publish_handles_subdirectories(tmp_path):
    """Test that subdirectories are traversed"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    subdir = env_dir / "commands"
    subdir.mkdir()
    (subdir / "custom.md").write_text("# Custom")
    (subdir / "secrets.json").write_text("secret")

    to_publish, excluded = get_files_to_publish(env_dir)

    # Subdirectory files should be included/excluded appropriately
    published_names = [f.name for f in to_publish]
    excluded_names = [f.name for f in excluded]

    assert "custom.md" in published_names
    assert "secrets.json" in excluded_names


def test_get_files_to_publish_empty_directory(tmp_path):
    """Test handling of empty environment directory"""
    env_dir = tmp_path / "empty-env"
    env_dir.mkdir()

    to_publish, excluded = get_files_to_publish(env_dir)

    assert to_publish == []
    assert excluded == []


def test_publish_to_repo_rejects_invalid_url(tmp_path):
    """Test that publish raises error for invalid URL"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    with pytest.raises(GitOperationError, match="Invalid GitHub URL"):
        publish_to_repo(env_dir, "not-a-valid-url")


@patch("subprocess.run")
def test_publish_to_repo_calls_git_clone(mock_run, tmp_path):
    """Test that publish clones the target repository"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            # Create temp dir with .git
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    publish_to_repo(env_dir, "https://github.com/user/repo")

    # Verify git clone was called
    clone_calls = [c for c in mock_run.call_args_list if "clone" in c[0][0]]
    assert len(clone_calls) == 1


@patch("subprocess.run")
def test_publish_to_repo_handles_no_changes(mock_run, tmp_path):
    """Test that publish handles no-changes scenario gracefully"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        if cmd[0] == "git" and cmd[1] == "status":
            # Return empty status (no changes)
            return MagicMock(returncode=0, stdout="", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    result = publish_to_repo(env_dir, "https://github.com/user/repo")

    assert result.success is True
    assert result.files_published == 0


@patch("subprocess.run")
def test_publish_to_repo_reports_excluded_files(mock_run, tmp_path):
    """Test that publish reports excluded sensitive files"""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()
    (env_dir / "CLAUDE.md").write_text("# Config")
    (env_dir / "credentials.json").write_text("secret")
    (env_dir / ".env").write_text("SECRET=x")

    def simulate_git_ops(cmd, **kwargs):
        if cmd[0] == "git" and cmd[1] == "clone":
            temp_dir = Path(cmd[5])
            temp_dir.mkdir(parents=True)
            (temp_dir / ".git").mkdir()
        if cmd[0] == "git" and cmd[1] == "status":
            return MagicMock(returncode=0, stdout="M file", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = simulate_git_ops

    result = publish_to_repo(env_dir, "https://github.com/user/repo")

    assert result.files_excluded == 2
    assert "credentials.json" in result.excluded_files
    assert ".env" in result.excluded_files


def test_publish_environment_exported_from_core():
    """Test that publish_environment is exported from core"""
    from cenv.core import publish_environment
    assert callable(publish_environment)
