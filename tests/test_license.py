"""Tests for LICENSE file."""
from pathlib import Path


def test_license_file_exists():
    """Test that LICENSE file exists in project root."""
    project_root = Path(__file__).parent.parent
    license_path = project_root / "LICENSE"
    assert license_path.exists(), "LICENSE file must exist in project root"


def test_license_file_content():
    """Test that LICENSE file contains MIT license text."""
    project_root = Path(__file__).parent.parent
    license_path = project_root / "LICENSE"

    content = license_path.read_text()

    # Check for key MIT license elements
    assert "MIT License" in content, "LICENSE must be MIT License"
    assert "Copyright (c) 2025 cenv contributors" in content, "LICENSE must have correct copyright"
    assert "Permission is hereby granted" in content, "LICENSE must contain MIT license text"
    assert "THE SOFTWARE IS PROVIDED \"AS IS\"" in content, "LICENSE must contain warranty disclaimer"
