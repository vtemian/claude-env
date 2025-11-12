"""Tests for CONTRIBUTING.md file."""
from pathlib import Path


def test_contributing_file_exists():
    """Test that CONTRIBUTING.md file exists in project root."""
    project_root = Path(__file__).parent.parent
    contributing_path = project_root / "CONTRIBUTING.md"
    assert contributing_path.exists(), "CONTRIBUTING.md file must exist in project root"


def test_contributing_file_content():
    """Test that CONTRIBUTING.md file contains required sections."""
    project_root = Path(__file__).parent.parent
    contributing_path = project_root / "CONTRIBUTING.md"

    content = contributing_path.read_text()

    # Check for key sections
    assert "# Contributing to cenv" in content, "CONTRIBUTING.md must have title"
    assert "Code of Conduct" in content, "CONTRIBUTING.md must reference Code of Conduct"
    assert "Development Setup" in content, "CONTRIBUTING.md must have Development Setup section"
    assert "Running Tests" in content, "CONTRIBUTING.md must have Running Tests section"
    assert "Type Checking" in content, "CONTRIBUTING.md must have Type Checking section"
    assert "Code Style" in content, "CONTRIBUTING.md must have Code Style section"
    assert "Testing Guidelines" in content, "CONTRIBUTING.md must have Testing Guidelines section"
    assert "Commit Messages" in content, "CONTRIBUTING.md must have Commit Messages section"
    assert "Design Principles" in content, "CONTRIBUTING.md must have Design Principles section"
    assert "Pull Request Process" in content, "CONTRIBUTING.md must have PR Process section"
    assert "pytest" in content, "CONTRIBUTING.md must mention pytest"
    assert "mypy" in content, "CONTRIBUTING.md must mention mypy"
    assert "Conventional Commits" in content, "CONTRIBUTING.md must reference Conventional Commits"
