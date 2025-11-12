# ABOUTME: Custom exception hierarchy for cenv
# ABOUTME: Provides specific exception types for better error handling
"""Custom exceptions for cenv"""

__all__ = [
    'CenvError',
    'EnvironmentNotFoundError',
    'EnvironmentExistsError',
    'ClaudeRunningError',
    'InitializationError',
    'GitOperationError',
    'PlatformNotSupportedError',
    'InvalidBackupFormatError',
    'SymlinkStateError',
    'ActiveEnvironmentError',
    'ProtectedEnvironmentError',
]


class CenvError(Exception):
    """Base exception for all cenv errors"""
    pass


class EnvironmentNotFoundError(CenvError):
    """Raised when an environment does not exist"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Environment '{name}' does not exist")


class EnvironmentExistsError(CenvError):
    """Raised when trying to create an environment that already exists"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Environment '{name}' already exists")


class ClaudeRunningError(CenvError):
    """Raised when Claude Code is running and operation requires it to be stopped"""
    def __init__(self) -> None:
        super().__init__(
            "Claude Code is currently running. "
            "Please exit Claude before performing this operation."
        )


class InitializationError(CenvError):
    """Raised when initialization fails or cenv is not initialized"""
    pass


class GitOperationError(CenvError):
    """Raised when git operations fail"""
    def __init__(self, operation: str, url: str, reason: str):
        self.operation = operation
        self.url = url
        self.reason = reason
        super().__init__(
            f"Git {operation} failed for {url}: {reason}"
        )


class PlatformNotSupportedError(CenvError):
    """Raised when cenv is run on an unsupported platform"""
    pass


class InvalidBackupFormatError(CenvError):
    """Raised when backup name format is invalid"""
    def __init__(self, backup_name: str):
        self.backup_name = backup_name
        super().__init__(
            f"Invalid backup name format: {backup_name}\n"
            f"Expected format: <env-name>-YYYYMMDD-HHMMSS"
        )


class SymlinkStateError(CenvError):
    """Raised when symlink is in unexpected state"""
    pass


class ActiveEnvironmentError(CenvError):
    """Raised when attempting to delete active environment"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Environment '{name}' is currently active. "
            "Switch to another environment first."
        )


class ProtectedEnvironmentError(CenvError):
    """Raised when attempting to delete protected environment"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Cannot delete protected environment '{name}'. "
            f"The '{name}' environment is required for cenv to function."
        )
