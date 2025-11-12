"""Test that exception handling doesn't swallow critical exceptions"""
import pytest
import inspect
from unittest.mock import patch
from cenv.config import load_config


def test_keyboard_interrupt_propagates_in_config():
    """Test that KeyboardInterrupt isn't swallowed during config loading"""

    # Mock file reading to raise KeyboardInterrupt
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=KeyboardInterrupt):
            # KeyboardInterrupt should propagate, not be swallowed
            with pytest.raises(KeyboardInterrupt):
                load_config()


def test_system_exit_propagates_in_config():
    """Test that SystemExit isn't swallowed during config loading"""

    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=SystemExit(1)):
            # SystemExit should propagate, not be swallowed
            with pytest.raises(SystemExit):
                load_config()


def test_config_handles_io_errors_gracefully():
    """Test that IOError in config loading is handled gracefully"""

    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=IOError("Disk error")):
            # Should not raise, should fall back to defaults
            config = load_config()
            assert config.git_timeout == 300  # Default


def test_config_handles_os_errors_gracefully():
    """Test that OSError in config loading is handled gracefully"""

    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=OSError("Permission denied")):
            # Should not raise, should fall back to defaults
            config = load_config()
            assert config.git_timeout == 300  # Default


def test_config_handles_unicode_errors_gracefully():
    """Test that UnicodeDecodeError in config loading is handled gracefully"""

    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.read_text', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            # Should not raise, should fall back to defaults
            config = load_config()
            assert config.git_timeout == 300  # Default


def test_lock_cleanup_handles_os_errors():
    """Test that lock cleanup handles OS errors gracefully"""
    # This is harder to test directly, so we document expected behavior
    # The cleanup code should catch (OSError, IOError) only
    # This test verifies the pattern exists
    from cenv.core import init_environments

    source = inspect.getsource(init_environments)

    # Verify we're catching specific exceptions, not bare except
    assert "except (OSError, IOError)" in source or "except OSError" in source, \
        "Lock cleanup should catch specific exceptions, not bare except"

    # Verify we're not using bare except Exception
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'except Exception:' in line and 'finally:' in lines[max(0, i-5):i]:
            pytest.fail(f"Found bare 'except Exception:' in finally block at line {i}")
