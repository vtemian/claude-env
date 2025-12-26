# ABOUTME: Tests for path portability functionality
# ABOUTME: Validates path substitution and expansion for config import/export
from pathlib import Path
from unittest.mock import patch

import pytest


def test_substitute_paths_replaces_claude_home():
    """Test that Claude home paths are replaced with {{CLAUDE_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/.claude/plugins/cache/foo"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{CLAUDE_HOME}}/plugins/cache/foo"}
    assert warnings == []


def test_substitute_paths_replaces_user_home():
    """Test that user home paths are replaced with {{USER_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/projects/myproject"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{USER_HOME}}/projects/myproject"}
    assert warnings == []


def test_substitute_paths_claude_home_takes_precedence():
    """Test that {{CLAUDE_HOME}} is substituted before {{USER_HOME}}"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "/Users/vlad/.claude/settings.json"}
            result, warnings = substitute_paths_with_placeholders(content)

    # Should be {{CLAUDE_HOME}}, not {{USER_HOME}}/.claude
    assert result == {"path": "{{CLAUDE_HOME}}/settings.json"}
    assert warnings == []


def test_substitute_paths_warns_on_unsubstitutable_paths():
    """Test that paths outside home directory generate warnings"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"tool": "/usr/local/bin/custom-tool"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"tool": "/usr/local/bin/custom-tool"}
    assert len(warnings) == 1
    assert "/usr/local/bin/custom-tool" in warnings[0]


def test_substitute_paths_handles_nested_objects():
    """Test that nested JSON objects are traversed"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"level1": {"level2": {"path": "/Users/vlad/.claude/deep/path"}}}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["level1"]["level2"]["path"] == "{{CLAUDE_HOME}}/deep/path"


def test_substitute_paths_handles_arrays():
    """Test that arrays of strings are processed"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"paths": ["/Users/vlad/.claude/path1", "/Users/vlad/path2", "not-a-path"]}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["paths"] == ["{{CLAUDE_HOME}}/path1", "{{USER_HOME}}/path2", "not-a-path"]


def test_substitute_paths_preserves_non_string_values():
    """Test that numbers, booleans, null are unchanged"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {
                "count": 42,
                "enabled": True,
                "nothing": None,
                "path": "/Users/vlad/.claude/file",
            }
            result, warnings = substitute_paths_with_placeholders(content)

    assert result["count"] == 42
    assert result["enabled"] is True
    assert result["nothing"] is None
    assert result["path"] == "{{CLAUDE_HOME}}/file"


def test_substitute_paths_handles_embedded_paths():
    """Test that paths embedded in larger strings are substituted"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"command": "node /Users/vlad/.claude/scripts/run.js --verbose"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"command": "node {{CLAUDE_HOME}}/scripts/run.js --verbose"}


def test_substitute_paths_no_double_substitution():
    """Test that existing placeholders are not double-substituted"""
    from cenv.path_portability import substitute_paths_with_placeholders

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            content = {"path": "{{CLAUDE_HOME}}/already/substituted"}
            result, warnings = substitute_paths_with_placeholders(content)

    assert result == {"path": "{{CLAUDE_HOME}}/already/substituted"}
    assert warnings == []
