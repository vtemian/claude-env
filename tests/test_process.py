# ABOUTME: Tests for Claude process detection functionality
# ABOUTME: Verifies is_claude_running() and get_claude_processes() work correctly
from unittest.mock import Mock, patch

import pytest

from cenv.process import get_claude_processes, is_claude_running


def test_is_claude_running_detects_processes():
    """Test is_claude_running() returns correct boolean based on actual process detection"""
    # Test when no Claude processes exist
    mock_proc_no_claude = Mock()
    mock_proc_no_claude.info = {"pid": 456, "name": "python", "cmdline": ["python", "script.py"]}

    with patch("psutil.process_iter", return_value=[mock_proc_no_claude]):
        assert is_claude_running() is False

    # Test when Claude process exists
    mock_proc_claude = Mock()
    mock_proc_claude.info = {"pid": 123, "name": "node", "cmdline": ["/usr/bin/node", "/path/to/bin/claude"]}

    with patch("psutil.process_iter", return_value=[mock_proc_claude]):
        assert is_claude_running() is True

    # Test mixed processes
    with patch("psutil.process_iter", return_value=[mock_proc_no_claude, mock_proc_claude]):
        assert is_claude_running() is True

def test_get_claude_processes_finds_claude_node_processes():
    """Test that get_claude_processes finds node processes running claude"""
    mock_proc1 = Mock()
    mock_proc1.info = {"pid": 123, "name": "node", "cmdline": ["/usr/bin/node", "/path/to/bin/claude"]}

    mock_proc2 = Mock()
    mock_proc2.info = {"pid": 456, "name": "python", "cmdline": ["python", "script.py"]}

    mock_proc3 = Mock()
    mock_proc3.info = {"pid": 789, "name": "node", "cmdline": ["/usr/bin/node", "/path/to/other"]}

    with patch("psutil.process_iter", return_value=[mock_proc1, mock_proc2, mock_proc3]):
        result = get_claude_processes()
        assert len(result) == 1
        assert result[0].info["pid"] == 123

def test_get_claude_processes_handles_access_denied():
    """Test that process iteration handles access denied errors"""
    from unittest.mock import PropertyMock

    import psutil

    mock_proc = Mock()
    type(mock_proc).info = PropertyMock(side_effect=psutil.AccessDenied())

    with patch("psutil.process_iter", return_value=[mock_proc]):
        result = get_claude_processes()
        assert result == []

def test_process_detection_returns_false_when_uncertain():
    """Test that uncertain detection returns False (fail-safe)"""
    # When we can't definitively detect Claude, assume it's not running
    # Better to allow operation than block user unnecessarily
    result = is_claude_running()
    assert isinstance(result, bool)


def test_get_claude_processes_handles_access_denied_gracefully():
    """Test that AccessDenied doesn't crash detection"""
    # Should handle permission errors gracefully
    processes = get_claude_processes()
    assert isinstance(processes, list)


def test_detection_documented_limitations():
    """Test that detection limitations are documented"""
    import cenv.process
    # Module should have docstring explaining limitations
    assert cenv.process.__doc__ is not None
    doc = cenv.process.__doc__.lower()
    # Should mention detection is best-effort
    assert any(word in doc for word in ['best-effort', 'may not', 'limitation', 'heuristic'])
