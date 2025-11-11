# ABOUTME: Input validation for environment names and parameters
# ABOUTME: Prevents path traversal and injection attacks
"""Input validation utilities for cenv"""
import re
from cenv.exceptions import CenvError


class InvalidEnvironmentNameError(CenvError):
    """Raised when environment name is invalid"""
    pass


# Valid environment name pattern: alphanumeric, hyphens, underscores
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Reserved names that cannot be used
RESERVED_NAMES = {'.', '..', '.trash', '.git', '.backup'}


def validate_environment_name(name: str) -> None:
    """Validate environment name for security and correctness

    Args:
        name: Environment name to validate

    Raises:
        InvalidEnvironmentNameError: If name is invalid

    Valid names:
        - Must contain only: letters (a-z, A-Z), digits (0-9), hyphens (-), underscores (_)
        - Cannot be empty
        - Cannot be a reserved name (., .., .trash, etc.)
        - No path separators (/, \\)
        - No special characters

    Examples:
        Valid: "production", "staging-v2", "dev_env", "test123"
        Invalid: "../etc", "env with spaces", ".hidden", ".."
    """
    if not name:
        raise InvalidEnvironmentNameError(
            "Environment name cannot be empty"
        )

    if name in RESERVED_NAMES:
        raise InvalidEnvironmentNameError(
            f"Environment name '{name}' is reserved and cannot be used.\n"
            f"Reserved names: {', '.join(sorted(RESERVED_NAMES))}"
        )

    if not VALID_NAME_PATTERN.match(name):
        raise InvalidEnvironmentNameError(
            f"Invalid environment name: '{name}'\n\n"
            f"Environment names must contain only:\n"
            f"  • Letters (a-z, A-Z)\n"
            f"  • Digits (0-9)\n"
            f"  • Hyphens (-)\n"
            f"  • Underscores (_)\n\n"
            f"Examples of valid names:\n"
            f"  • production\n"
            f"  • staging-v2\n"
            f"  • dev_env\n"
            f"  • test123"
        )
