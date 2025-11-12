from click.testing import CliRunner

from cenv.cli import cli


def test_create_rejects_invalid_names():
    """Test that create command rejects invalid names"""
    runner = CliRunner()

    invalid_names = ["../etc", "env with spaces", "env/slash"]

    for name in invalid_names:
        result = runner.invoke(cli, ['create', name])
        assert result.exit_code == 1
        assert "Validation Error" in result.output or "Invalid" in result.output or "invalid" in result.output


def test_use_rejects_invalid_names():
    """Test that use command rejects invalid names"""
    runner = CliRunner()

    result = runner.invoke(cli, ['use', '../evil'])
    assert result.exit_code == 1
    assert "Validation Error" in result.output or "Invalid" in result.output or "invalid" in result.output


def test_delete_rejects_invalid_names():
    """Test that delete command rejects invalid names"""
    runner = CliRunner()

    result = runner.invoke(cli, ['delete', '--force', '../evil'])
    assert result.exit_code == 1
    assert "Validation Error" in result.output or "Invalid" in result.output or "invalid" in result.output
