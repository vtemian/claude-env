# ABOUTME: Tests for publish functionality
# ABOUTME: Validates sensitive file detection and git push operations
import pytest

from cenv.publish import is_sensitive_file, SENSITIVE_PATTERNS


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
