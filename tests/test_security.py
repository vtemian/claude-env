
import pytest
from click.testing import CliRunner

from cenv.cli import cli
from cenv.core import create_environment, init_environments
from cenv.validation import InvalidEnvironmentNameError


def test_path_traversal_attack_blocked(tmp_path, monkeypatch):
    """Test that path traversal attempts are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    # Attempt path traversal
    attacks = [
        "../../etc/passwd",
        "../../../tmp/evil",
        "../../.ssh",
        "./../evil",
    ]

    for attack in attacks:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(attack)


def test_special_characters_blocked(tmp_path, monkeypatch):
    """Test that special characters are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    special_chars = [
        "env;rm -rf /",
        "env && echo evil",
        "env | cat /etc/passwd",
        "env'$(whoami)'",
        'env"$(whoami)"',
        "env`whoami`",
    ]

    for attack in special_chars:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(attack)


def test_reserved_names_blocked(tmp_path, monkeypatch):
    """Test that reserved names are blocked"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    init_environments()

    reserved = [".", "..", ".trash", ".git"]

    for name in reserved:
        with pytest.raises(InvalidEnvironmentNameError):
            create_environment(name)


def test_cli_rejects_malicious_input():
    """Test that CLI rejects malicious input"""
    runner = CliRunner()

    malicious = [
        "../../etc",
        "env; rm -rf /",
        "$(evil)",
    ]

    for attack in malicious:
        result = runner.invoke(cli, ['create', attack])
        assert result.exit_code != 0
        assert "Validation Error" in result.output or "Invalid" in result.output
