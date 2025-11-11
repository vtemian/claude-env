import platform
import pytest
from unittest.mock import patch
from cenv.platform_utils import check_platform_compatibility, PlatformNotSupportedError


def test_unix_platforms_are_supported():
    """Test that Unix-like platforms are supported"""
    for system in ['Linux', 'Darwin', 'FreeBSD']:
        with patch('platform.system', return_value=system):
            # Should not raise
            check_platform_compatibility()


def test_windows_raises_clear_error():
    """Test that Windows raises helpful error message"""
    with patch('platform.system', return_value='Windows'):
        with pytest.raises(PlatformNotSupportedError) as exc_info:
            check_platform_compatibility()

        error_msg = str(exc_info.value)
        assert "Windows" in error_msg
        assert "WSL" in error_msg or "Unix" in error_msg


def test_error_includes_workaround_suggestions():
    """Test that error message is helpful"""
    with patch('platform.system', return_value='Windows'):
        with pytest.raises(PlatformNotSupportedError) as exc_info:
            check_platform_compatibility()

        error_msg = str(exc_info.value)
        # Should suggest alternatives
        assert any(word in error_msg for word in ['WSL2', 'Linux', 'macOS'])
