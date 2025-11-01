# ABOUTME: CLI interface for cenv using Click framework
# ABOUTME: Provides commands for init, create, use, list, current, and delete
import click
from cenv.core import (
    init_environments,
    create_environment,
    switch_environment,
    delete_environment,
    list_environments,
    get_current_environment,
)
from cenv.process import is_claude_running

@click.group()
@click.version_option()
def cli():
    """cenv - Claude environment manager

    Manage isolated Claude Code configurations like pyenv manages Python versions.
    """
    pass

@cli.command()
def init():
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    try:
        init_environments()
        click.echo("✓ Initialized cenv successfully!")
        click.echo("  ~/.claude → ~/.claude-envs/default/")
        click.echo("\nUse 'cenv create <name>' to create new environments.")
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

@cli.command()
@click.argument("name")
@click.option(
    "--from-repo",
    help="Clone from GitHub repository URL",
    metavar="URL",
)
def create(name: str, from_repo: str):
    """Create a new environment"""
    try:
        source = from_repo if from_repo else "default"
        create_environment(name, source=source)

        if from_repo:
            click.echo(f"✓ Created environment '{name}' from {from_repo}")
        else:
            click.echo(f"✓ Created environment '{name}' from default")
    except (RuntimeError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
