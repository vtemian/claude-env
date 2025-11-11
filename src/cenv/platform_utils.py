# ABOUTME: Platform compatibility detection and validation
# ABOUTME: Ensures cenv runs only on supported platforms
"""Platform compatibility utilities for cenv"""
import platform


class PlatformNotSupportedError(Exception):
    """Raised when cenv is run on an unsupported platform"""
    pass


def check_platform_compatibility() -> None:
    """Check if current platform is supported by cenv

    Raises:
        PlatformNotSupportedError: If platform is not supported
    """
    system = platform.system()

    # Supported platforms: Unix-like systems with fcntl
    supported = ['Linux', 'Darwin', 'FreeBSD', 'OpenBSD', 'SunOS']

    if system not in supported:
        raise PlatformNotSupportedError(
            f"cenv does not support {system}.\n\n"
            f"cenv requires file locking features available on Unix-like systems.\n\n"
            f"Supported platforms: {', '.join(supported)}\n\n"
            f"Workarounds:\n"
            f"  • Windows users: Use WSL2 (Windows Subsystem for Linux)\n"
            f"  • Install a Linux distribution or use macOS\n\n"
            f"For more information, see: https://github.com/yourusername/cenv#platform-support"
        )
