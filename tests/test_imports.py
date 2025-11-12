"""Test that all public exceptions are importable and usable."""
import pytest


def test_exception_imports_from_cenv():
    """Test that public exceptions can be imported from main package."""
    from cenv.exceptions import (
        ActiveEnvironmentError,
        CenvError,
        ClaudeRunningError,
        EnvironmentExistsError,
        EnvironmentNotFoundError,
        GitOperationError,
        InitializationError,
        InvalidBackupFormatError,
        PlatformNotSupportedError,
        ProtectedEnvironmentError,
        SymlinkStateError,
    )

    # Verify they're all Exception subclasses
    assert issubclass(CenvError, Exception)
    assert issubclass(EnvironmentNotFoundError, CenvError)
    assert issubclass(EnvironmentExistsError, CenvError)
    assert issubclass(ClaudeRunningError, CenvError)
    assert issubclass(InitializationError, CenvError)
    assert issubclass(GitOperationError, CenvError)
    assert issubclass(PlatformNotSupportedError, CenvError)
    assert issubclass(InvalidBackupFormatError, CenvError)
    assert issubclass(SymlinkStateError, CenvError)
    assert issubclass(ActiveEnvironmentError, CenvError)
    assert issubclass(ProtectedEnvironmentError, CenvError)


def test_validation_exceptions_importable():
    """Test that validation exceptions are importable."""
    from cenv.validation import InvalidEnvironmentNameError

    assert issubclass(InvalidEnvironmentNameError, Exception)


def test_platform_exceptions_importable():
    """Test that platform exceptions are importable."""
    from cenv.platform_utils import PlatformNotSupportedError

    assert issubclass(PlatformNotSupportedError, Exception)
