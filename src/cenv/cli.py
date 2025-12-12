# ABOUTME: CLI interface for cenv using Typer framework
# ABOUTME: Provides commands for init, create, use, list, current, delete, trash, and restore
import logging
from pathlib import Path
from typing import Annotated

import typer

from cenv.core import (
    DEFAULT_ENV_NAME,
    create_environment,
    delete_environment,
    get_current_environment,
    init_environments,
    list_environments,
    list_trash,
    restore_from_trash,
    switch_environment,
)
from cenv.exceptions import CenvError, EnvironmentNotFoundError, InitializationError
from cenv.logging_config import setup_logging
from cenv.process import is_claude_running

__all__ = ["cli"]

app = typer.Typer(
    help="cenv - Claude environment manager\n\n"
    "Manage isolated Claude Code configurations like pyenv manages Python versions."
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from importlib.metadata import version

        typer.echo(f"cenv {version('claude-env')}")
        raise typer.Exit()


def format_error_with_help(error: CenvError, context: str = "") -> str:
    """Format error message with helpful suggestions

    Args:
        error: The exception that occurred
        context: Additional context (e.g., 'use', 'create')

    Returns:
        Formatted error message with suggestions
    """
    message = f"Error: {error}\n"

    # Add context-specific help
    if isinstance(error, EnvironmentNotFoundError):
        try:
            envs = list_environments()
            current = get_current_environment()

            if envs:
                message += "\nAvailable environments:\n"
                for env in sorted(envs):
                    marker = " → " if env == current else "   "
                    message += f"{marker}{env}\n"
            else:
                message += "\nNo environments found. Run 'cenv init' to initialize.\n"

            message += "\nRun 'cenv list' to see all environments.\n"
        except Exception:  # Catch any error during help message generation
            message += "\nRun 'cenv list' to see available environments.\n"

    elif isinstance(error, InitializationError):
        if "not initialized" in str(error).lower():
            message += "\nRun 'cenv init' to initialize cenv.\n"

    return message.rstrip()


@app.callback()
def main(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
    log_file: Annotated[
        Path | None, typer.Option("--log-file", help="Write logs to file")
    ] = None,
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """cenv - Claude environment manager"""
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level, log_file=log_file)


@app.command()
def init() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    try:
        init_environments()
        typer.echo("✓ Initialized cenv successfully!")
        typer.echo("  ~/.claude → ~/.claude-envs/default/")
        typer.echo("\nUse 'cenv create <name>' to create new environments.")
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="init"), err=True)
        raise SystemExit(1)


@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the environment to create")],
    from_repo: Annotated[
        str | None, typer.Option("--from-repo", help="Clone from GitHub repository URL")
    ] = None,
) -> None:
    """Create a new environment"""
    try:
        source = from_repo if from_repo else DEFAULT_ENV_NAME
        create_environment(name, source=source)

        if from_repo:
            typer.echo(f"✓ Created environment '{name}' from {from_repo}")
        else:
            typer.echo(f"✓ Created environment '{name}' from {DEFAULT_ENV_NAME}")
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="create"), err=True)
        raise SystemExit(1)


@app.command()
def use(
    name: Annotated[str, typer.Argument(help="Name of the environment to switch to")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Switch to a different environment"""
    try:
        # Check if Claude is running
        if is_claude_running() and not force:
            typer.echo("⚠️  Claude is running. Switching environments may cause issues.")
            if not typer.confirm("Continue anyway?"):
                typer.echo("Cancelled.")
                return
            force = True

        switch_environment(name, force=force)
        typer.echo(f"✓ Switched to environment '{name}'")
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="use"), err=True)
        raise SystemExit(1)


@app.command("list")
def list_cmd() -> None:
    """List all environments"""
    envs = list_environments()
    current = get_current_environment()

    if not envs:
        typer.echo("No environments found.")
        typer.echo("Run 'cenv init' to initialize.")
        return

    typer.echo("Available environments:")
    for env in sorted(envs):
        marker = " → " if env == current else "   "
        typer.echo(f"{marker}{env}")


@app.command()
def current() -> None:
    """Show the currently active environment"""
    current_env = get_current_environment()

    if current_env is None:
        typer.echo("No active environment.")
        typer.echo("Run 'cenv init' to initialize.")
    else:
        typer.echo(current_env)


@app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Name of the environment to delete")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Delete an environment (moves to trash)"""
    try:
        if not force:
            if not typer.confirm(f"Delete environment '{name}'?"):
                typer.echo("Cancelled.")
                return

        delete_environment(name)
        typer.echo(f"✓ Deleted environment '{name}' (moved to trash)")
        typer.echo("  Use 'cenv trash' to list deleted environments")
        typer.echo("  Use 'cenv restore <backup-name>' to restore")
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="delete"), err=True)
        raise SystemExit(1)


@app.command()
def trash() -> None:
    """List deleted environments in trash"""
    backups = list_trash()

    if not backups:
        typer.echo("Trash is empty.")
        return

    typer.echo("Deleted environments (newest first):")
    for backup in backups:
        typer.echo(f"  {backup['backup_name']}")
        typer.echo(f"    Environment: {backup['name']}")
        typer.echo(f"    Deleted: {backup['timestamp']}")
        typer.echo()


@app.command()
def restore(
    backup_name: Annotated[str, typer.Argument(help="Name of the backup to restore")],
) -> None:
    """Restore an environment from trash"""
    try:
        name = restore_from_trash(backup_name)
        typer.echo(f"✓ Restored environment '{name}' from trash")
    except CenvError as e:
        typer.echo(format_error_with_help(e, context="restore"), err=True)
        raise SystemExit(1)


# Entry point for pyproject.toml scripts
cli = app
