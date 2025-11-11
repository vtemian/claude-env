import pytest
from cenv.validation import (
    validate_environment_name,
    InvalidEnvironmentNameError,
    VALID_NAME_PATTERN,
)


def test_valid_environment_names():
    """Test that valid names pass validation"""
    valid_names = [
        "production",
        "staging",
        "dev",
        "my-env",
        "env_123",
        "test-env-v2",
        "a",  # Single character
        "very-long-environment-name-with-many-parts",
    ]

    for name in valid_names:
        # Should not raise
        validate_environment_name(name)


def test_invalid_characters_rejected():
    """Test that invalid characters are rejected"""
    invalid_names = [
        "../etc",
        "../../passwd",
        "env/with/slash",
        "env\\with\\backslash",
        "env with spaces",
        "env@special",
        "env!mark",
        "env#hash",
        "env$dollar",
        "env%percent",
        ".hidden",
        "env.",
    ]

    for name in invalid_names:
        with pytest.raises(InvalidEnvironmentNameError) as exc_info:
            validate_environment_name(name)

        error_msg = str(exc_info.value)
        assert name in error_msg
        assert "invalid" in error_msg.lower()


def test_reserved_names_rejected():
    """Test that reserved names are rejected"""
    reserved_names = [
        ".",
        "..",
        ".trash",
    ]

    for name in reserved_names:
        with pytest.raises(InvalidEnvironmentNameError) as exc_info:
            validate_environment_name(name)

        error_msg = str(exc_info.value)
        assert "reserved" in error_msg.lower() or "invalid" in error_msg.lower()


def test_empty_name_rejected():
    """Test that empty names are rejected"""
    with pytest.raises(InvalidEnvironmentNameError):
        validate_environment_name("")


def test_error_message_includes_pattern():
    """Test that error message explains valid pattern"""
    with pytest.raises(InvalidEnvironmentNameError) as exc_info:
        validate_environment_name("invalid name")

    error_msg = str(exc_info.value)
    # Should explain what's allowed
    assert any(char in error_msg for char in ['a-z', '0-9', '-', '_'])
