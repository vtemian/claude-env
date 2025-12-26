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


# ============================================================================
# Placeholder Expansion Tests (Task 2)
# ============================================================================


def test_expand_placeholders_expands_claude_home():
    """Test that {{CLAUDE_HOME}} is expanded to local Claude directory"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {"path": "{{CLAUDE_HOME}}/plugins/cache/foo"}
            result = expand_placeholders_to_paths(content)

    assert result == {"path": "/Users/newuser/.claude/plugins/cache/foo"}


def test_expand_placeholders_expands_user_home():
    """Test that {{USER_HOME}} is expanded to local home directory"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {"path": "{{USER_HOME}}/projects/myproject"}
            result = expand_placeholders_to_paths(content)

    assert result == {"path": "/Users/newuser/projects/myproject"}


def test_expand_placeholders_handles_both_in_same_string():
    """Test that both placeholders in same string are expanded"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/home/user/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/home/user")):
            content = {"cmd": "cp {{CLAUDE_HOME}}/a {{USER_HOME}}/b"}
            result = expand_placeholders_to_paths(content)

    assert result == {"cmd": "cp /home/user/.claude/a /home/user/b"}


def test_expand_placeholders_handles_nested_objects():
    """Test that nested JSON objects are traversed during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {"level1": {"level2": {"path": "{{CLAUDE_HOME}}/deep/path"}}}
            result = expand_placeholders_to_paths(content)

    assert result["level1"]["level2"]["path"] == "/Users/newuser/.claude/deep/path"


def test_expand_placeholders_handles_arrays():
    """Test that arrays are processed during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {
                "paths": ["{{CLAUDE_HOME}}/path1", "{{USER_HOME}}/path2", "not-a-placeholder"]
            }
            result = expand_placeholders_to_paths(content)

    assert result["paths"] == [
        "/Users/newuser/.claude/path1",
        "/Users/newuser/path2",
        "not-a-placeholder",
    ]


def test_expand_placeholders_preserves_non_string_values():
    """Test that numbers, booleans, null are unchanged during expansion"""
    from cenv.path_portability import expand_placeholders_to_paths

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            content = {
                "count": 42,
                "enabled": True,
                "nothing": None,
                "path": "{{CLAUDE_HOME}}/file",
            }
            result = expand_placeholders_to_paths(content)

    assert result["count"] == 42
    assert result["enabled"] is True
    assert result["nothing"] is None
    assert result["path"] == "/Users/newuser/.claude/file"


# ============================================================================
# File Processing Tests (Task 3)
# ============================================================================

import json


def test_process_json_files_for_publish_transforms_files(tmp_path):
    """Test that JSON files are transformed with placeholders on publish"""
    from cenv.path_portability import process_json_files_for_publish

    # Create test JSON file
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"path": "/Users/vlad/.claude/plugins"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            warnings = process_json_files_for_publish(tmp_path)

    # Verify file was transformed
    result = json.loads(json_file.read_text())
    assert result == {"path": "{{CLAUDE_HOME}}/plugins"}
    assert warnings == []


def test_process_json_files_for_publish_handles_nested_dirs(tmp_path):
    """Test that JSON files in subdirectories are processed"""
    from cenv.path_portability import process_json_files_for_publish

    # Create nested JSON file
    subdir = tmp_path / "plugins"
    subdir.mkdir()
    json_file = subdir / "config.json"
    json_file.write_text(json.dumps({"installPath": "/Users/vlad/.claude/cache"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            process_json_files_for_publish(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"installPath": "{{CLAUDE_HOME}}/cache"}


def test_process_json_files_for_publish_skips_non_json(tmp_path):
    """Test that non-JSON files are not modified"""
    from cenv.path_portability import process_json_files_for_publish

    # Create non-JSON file with path-like content
    md_file = tmp_path / "README.md"
    original_content = "Path: /Users/vlad/.claude/plugins"
    md_file.write_text(original_content)

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            process_json_files_for_publish(tmp_path)

    # Verify file was NOT modified
    assert md_file.read_text() == original_content


def test_process_json_files_for_publish_collects_warnings(tmp_path):
    """Test that warnings from all files are collected"""
    from cenv.path_portability import process_json_files_for_publish

    # Create JSON file with unsubstitutable path
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"tool": "/usr/local/bin/node"}))

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            warnings = process_json_files_for_publish(tmp_path)

    assert len(warnings) == 1
    assert "settings.json" in warnings[0]
    assert "/usr/local/bin/node" in warnings[0]


def test_process_json_files_for_publish_handles_malformed_json(tmp_path, caplog):
    """Test that malformed JSON files are skipped with warning"""
    from cenv.path_portability import process_json_files_for_publish

    # Create malformed JSON file
    json_file = tmp_path / "broken.json"
    json_file.write_text("{ not valid json }")

    with patch("cenv.path_portability._get_claude_home", return_value=Path("/Users/vlad/.claude")):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/vlad")):
            # Should not raise
            warnings = process_json_files_for_publish(tmp_path)

    # File should be unchanged
    assert json_file.read_text() == "{ not valid json }"


def test_process_json_files_for_import_expands_placeholders(tmp_path):
    """Test that JSON files have placeholders expanded on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create JSON file with placeholders
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps({"path": "{{CLAUDE_HOME}}/plugins"}))

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            process_json_files_for_import(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"path": "/Users/newuser/.claude/plugins"}


def test_process_json_files_for_import_handles_nested_dirs(tmp_path):
    """Test that JSON files in subdirectories are processed on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create nested JSON file
    subdir = tmp_path / "plugins"
    subdir.mkdir()
    json_file = subdir / "config.json"
    json_file.write_text(json.dumps({"installPath": "{{CLAUDE_HOME}}/cache"}))

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            process_json_files_for_import(tmp_path)

    result = json.loads(json_file.read_text())
    assert result == {"installPath": "/Users/newuser/.claude/cache"}


def test_process_json_files_for_import_handles_malformed_json(tmp_path):
    """Test that malformed JSON files are skipped on import"""
    from cenv.path_portability import process_json_files_for_import

    # Create malformed JSON file
    json_file = tmp_path / "broken.json"
    json_file.write_text("{ not valid json }")

    with patch(
        "cenv.path_portability._get_claude_home", return_value=Path("/Users/newuser/.claude")
    ):
        with patch("cenv.path_portability._get_user_home", return_value=Path("/Users/newuser")):
            # Should not raise
            process_json_files_for_import(tmp_path)

    # File should be unchanged
    assert json_file.read_text() == "{ not valid json }"
