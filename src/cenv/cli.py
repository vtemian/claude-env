# ABOUTME: CLI interface for cenv using Click framework
# ABOUTME: Provides commands for init, create, use, list, current, and delete
import click
import logging
from pathlib import Path
from cenv.core import (
    init_environments,
    create_environment,
    switch_environment,
    delete_environment,
    list_environments,
    get_current_environment,
)
from cenv.process import is_claude_running
from cenv.logging_config import setup_logging
from cenv.exceptions import CenvError


@click.group()
@click.version_option()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Write logs to file"
)
def cli(verbose: bool, log_file: Path):
    """cenv - Claude environment manager

    Manage isolated Claude Code configurations like pyenv manages Python versions.
    """
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level, log_file=log_file)

@cli.command()
def init():
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    try:
        init_environments()
        click.echo("✓ Initialized cenv successfully!")
        click.echo("  ~/.claude → ~/.claude-envs/default/")
        click.echo("\nUse 'cenv create <name>' to create new environments.")
    except CenvError as e:
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
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

@cli.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def use(name: str, force: bool):
    """Switch to a different environment"""
    try:
        # Check if Claude is running
        if is_claude_running() and not force:
            click.echo("⚠️  Claude is running. Switching environments may cause issues.")
            if not click.confirm("Continue anyway?"):
                click.echo("Cancelled.")
                return
            force = True

        switch_environment(name, force=force)
        click.echo(f"✓ Switched to environment '{name}'")
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

@cli.command()
def list():
    """List all environments"""
    envs = list_environments()
    current = get_current_environment()

    if not envs:
        click.echo("No environments found.")
        click.echo("Run 'cenv init' to initialize.")
        return

    click.echo("Available environments:")
    for env in sorted(envs):
        marker = " → " if env == current else "   "
        click.echo(f"{marker}{env}")

@cli.command()
def current():
    """Show the currently active environment"""
    current_env = get_current_environment()

    if current_env is None:
        click.echo("No active environment.")
        click.echo("Run 'cenv init' to initialize.")
    else:
        click.echo(current_env)

@cli.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def delete(name: str, force: bool):
    """Delete an environment"""
    try:
        if not force:
            if not click.confirm(f"Delete environment '{name}'?"):
                click.echo("Cancelled.")
                return

        delete_environment(name)
        click.echo(f"✓ Deleted environment '{name}'")
    except CenvError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
