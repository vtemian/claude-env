# ABOUTME: Tests for publish functionality
# ABOUTME: Validates sensitive file detection and git push operations
import pytest
from pathlib import Path

from cenv.publish import is_sensitive_file, SENSITIVE_PATTERNS, get_files_to_publish


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
