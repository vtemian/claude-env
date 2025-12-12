from typer.testing import CliRunner

from cenv.cli import cli


def test_environment_not_found_suggests_alternatives(tmp_path, monkeypatch):
    """Test that 'not found' errors suggest available environments"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    runner = CliRunner()

    # Initialize
    runner.invoke(cli, ["init"])

    # Try to use non-existent environment
    result = runner.invoke(cli, ["use", "nonexistent"])

    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
    # Should suggest running list command
    assert "cenv list" in result.output or "available" in result.output.lower()


def test_uninit_error_suggests_init_command():
    """Test that uninitialized error suggests init command"""
    runner = CliRunner()

    result = runner.invoke(cli, ["list"])

    assert "init" in result.output.lower()
    assert "cenv init" in result.output


def test_error_includes_available_environments(tmp_path, monkeypatch):
    """Test that error message lists available environments"""
    monkeypatch.setattr("cenv.core.Path.home", lambda: tmp_path)

    runner = CliRunner()

    # Initialize and create some environments
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["create", "staging"])
    runner.invoke(cli, ["create", "production"])

    # Try to use non-existent environment
    result = runner.invoke(cli, ["use", "nonexistent"])

    assert result.exit_code == 1
    # Should list available environments
    assert "default" in result.output
    assert "staging" in result.output
    assert "production" in result.output
