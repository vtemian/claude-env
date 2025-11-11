import pytest
from cenv.exceptions import (
    CenvError,
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
    GitOperationError,
    PlatformNotSupportedError,
    InvalidBackupFormatError,
    SymlinkStateError,
    ActiveEnvironmentError,
    ProtectedEnvironmentError,
)


def test_cenv_error_is_base_exception():
    """Test that CenvError is the base exception"""
    err = CenvError("test message")
    assert str(err) == "test message"
    assert isinstance(err, Exception)


def test_environment_not_found_error():
    """Test EnvironmentNotFoundError with environment name"""
    err = EnvironmentNotFoundError("myenv")
    assert "myenv" in str(err)
    assert isinstance(err, CenvError)


def test_environment_exists_error():
    """Test EnvironmentExistsError with environment name"""
    err = EnvironmentExistsError("myenv")
    assert "myenv" in str(err)
    assert isinstance(err, CenvError)


def test_claude_running_error():
    """Test ClaudeRunningError message"""
    err = ClaudeRunningError()
    assert "Claude" in str(err)
    assert "running" in str(err).lower()
    assert isinstance(err, CenvError)


def test_initialization_error():
    """Test InitializationError with custom message"""
    err = InitializationError("Already initialized")
    assert "Already initialized" in str(err)
    assert isinstance(err, CenvError)


def test_git_operation_error():
    """Test GitOperationError with operation details"""
    err = GitOperationError("clone", "https://github.com/user/repo", "timeout")
    assert "clone" in str(err)
    assert "timeout" in str(err)
    assert isinstance(err, CenvError)


def test_platform_not_supported_error():
    """Test PlatformNotSupportedError inherits from CenvError"""
    err = PlatformNotSupportedError("Platform not supported")
    assert "Platform not supported" in str(err)
    assert isinstance(err, CenvError)


def test_invalid_backup_format_error():
    """Test InvalidBackupFormatError with backup name"""
    err = InvalidBackupFormatError("invalid-backup")
    assert "invalid-backup" in str(err)
    assert "format" in str(err).lower()
    assert isinstance(err, CenvError)


def test_symlink_state_error():
    """Test SymlinkStateError with description"""
    err = SymlinkStateError("~/.claude exists but is not a symlink")
    assert "symlink" in str(err).lower()
    assert isinstance(err, CenvError)


def test_active_environment_error():
    """Test ActiveEnvironmentError with environment name"""
    err = ActiveEnvironmentError("production")
    assert "production" in str(err)
    assert "active" in str(err).lower()
    assert isinstance(err, CenvError)


def test_protected_environment_error():
    """Test ProtectedEnvironmentError with environment name"""
    err = ProtectedEnvironmentError("default")
    assert "default" in str(err)
    assert "protected" in str(err).lower() or "cannot" in str(err).lower()
    assert isinstance(err, CenvError)
