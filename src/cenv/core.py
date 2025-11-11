# ABOUTME: Core functionality for cenv environment management
# ABOUTME: Provides path utilities and environment operations
"""Core functionality for cenv"""
from pathlib import Path
from typing import List, Optional
import shutil
import threading
from cenv.process import is_claude_running
from cenv.github import clone_from_github, is_valid_github_url
from cenv.logging_config import get_logger
from cenv.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentExistsError,
    ClaudeRunningError,
    InitializationError,
    GitOperationError,
    InvalidBackupFormatError,
    SymlinkStateError,
    ActiveEnvironmentError,
    ProtectedEnvironmentError,
)
from cenv.platform_utils import check_platform_compatibility, PlatformNotSupportedError
from cenv.validation import validate_environment_name, InvalidEnvironmentNameError

logger = get_logger(__name__)

# Global lock for switch operations to ensure atomicity
_switch_lock = threading.Lock()

def get_envs_dir() -> Path:
    """Get the base directory for all environments"""
    return Path.home() / ".claude-envs"

def get_env_path(name: str) -> Path:
    """Get the path for a specific environment"""
    return get_envs_dir() / name

def get_claude_dir() -> Path:
    """Get the ~/.claude directory path"""
    return Path.home() / ".claude"

def get_trash_dir() -> Path:
    """Get the trash directory for deleted environments"""
    return get_envs_dir() / ".trash"

def list_trash() -> List[dict[str, str]]:
    """List backups in trash

    Returns:
        List of dicts with 'name', 'backup_name', 'timestamp' keys
    """
    trash_dir = get_trash_dir()

    if not trash_dir.exists():
        return []

    backups = []
    for item in trash_dir.iterdir():
        if item.is_dir():
            # Parse name: <env-name>-YYYYMMDD-HHMMSS
            parts = item.name.rsplit("-", 2)
            if len(parts) == 3:
                name = parts[0]
                timestamp = f"{parts[1]}-{parts[2]}"
                backups.append({
                    "name": name,
                    "backup_name": item.name,
                    "timestamp": timestamp,
                })

    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

def restore_from_trash(backup_name: str) -> str:
    """Restore an environment from trash

    Args:
        backup_name: Full backup directory name (e.g., 'myenv-20251111-143022')

    Returns:
        Name of restored environment

    Raises:
        EnvironmentNotFoundError: If backup doesn't exist
        EnvironmentExistsError: If environment already exists
    """
    trash_dir = get_trash_dir()
    backup_path = trash_dir / backup_name

    if not backup_path.exists():
        raise EnvironmentNotFoundError(backup_name)

    # Extract original name
    parts = backup_name.rsplit("-", 2)
    if len(parts) != 3:
        raise InvalidBackupFormatError(backup_name)

    name = parts[0]
    target_path = get_env_path(name)

    if target_path.exists():
        raise EnvironmentExistsError(name)

    logger.info(f"Restoring '{name}' from trash backup '{backup_name}'")
    shutil.move(str(backup_path), str(target_path))
    logger.info(f"Environment '{name}' restored")

    return name

def list_environments() -> List[str]:
    """List all available environments"""
    envs_dir = get_envs_dir()

    if not envs_dir.exists():
        return []

    return [
        item.name
        for item in envs_dir.iterdir()
        if item.is_dir() and item.name != ".trash"
    ]

def get_current_environment() -> Optional[str]:
    """Get the currently active environment name"""
    claude_dir = get_claude_dir()

    if not claude_dir.is_symlink():
        return None

    target = claude_dir.resolve()
    envs_dir = get_envs_dir()

    if target.parent == envs_dir:
        return target.name

    return None

def environment_exists(name: str) -> bool:
    """Check if an environment exists"""
    return get_env_path(name).exists()

def init_environments() -> None:
    """Initialize cenv by migrating ~/.claude to ~/.claude-envs/default/"""
    # Check platform compatibility before attempting initialization
    check_platform_compatibility()

    import fcntl
    import tempfile

    logger.info("Initializing cenv")
    claude_dir = get_claude_dir()
    envs_dir = get_envs_dir()
    default_env = get_env_path("default")

    # Use lock file to prevent concurrent initialization
    lock_file_path = Path(tempfile.gettempdir()) / "cenv-init.lock"
    lock_file = None

    try:
        lock_file = open(lock_file_path, "w")
        # Try to acquire exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise InitializationError(
                "Another cenv initialization is in progress. Please wait."
            )

        # Check if ~/.claude is already a symlink
        if claude_dir.is_symlink():
            logger.error("~/.claude is already a symlink")
            raise InitializationError("~/.claude is already a symlink. Cannot initialize.")

        # Check if already initialized
        if envs_dir.exists():
            logger.error("cenv already initialized")
            raise InitializationError("cenv already initialized. ~/.claude-envs exists.")

        # Create backup if claude_dir exists
        backup_dir = None
        if claude_dir.exists() and not claude_dir.is_symlink():
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup_dir = claude_dir.parent / f".claude.backup.{timestamp}"
            logger.info(f"Creating backup at {backup_dir}")
            shutil.copytree(claude_dir, backup_dir)

        try:
            # Create envs directory
            logger.debug(f"Creating envs directory at {envs_dir}")
            envs_dir.mkdir(parents=True, exist_ok=True)

            # Move ~/.claude to default environment
            if claude_dir.exists():
                logger.info(f"Moving {claude_dir} to {default_env}")
                shutil.move(str(claude_dir), str(default_env))
            else:
                # Create empty default environment
                logger.info(f"Creating empty default environment at {default_env}")
                default_env.mkdir(parents=True, exist_ok=True)

            # Create symlink
            logger.info(f"Creating symlink {claude_dir} -> {default_env}")
            claude_dir.symlink_to(default_env)

            # Clean up backup on success
            if backup_dir and backup_dir.exists():
                logger.debug(f"Removing backup at {backup_dir}")
                shutil.rmtree(backup_dir)

            logger.info("Initialization complete")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            # Restore from backup if anything failed
            if backup_dir and backup_dir.exists():
                logger.info(f"Restoring from backup at {backup_dir}")
                # Clean up any partial state
                if claude_dir.exists():
                    if claude_dir.is_symlink():
                        claude_dir.unlink()
                    else:
                        shutil.rmtree(claude_dir)
                if default_env.exists():
                    shutil.rmtree(default_env)
                if envs_dir.exists() and not any(envs_dir.iterdir()):
                    envs_dir.rmdir()
                # Restore original .claude
                shutil.move(str(backup_dir), str(claude_dir))
            raise InitializationError(f"Initialization failed: {e}. Configuration restored from backup.")

    finally:
        # Release lock and clean up
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                lock_file_path.unlink(missing_ok=True)
            except Exception:
                pass

def create_environment(name: str, source: str = "default") -> None:
    """Create a new environment by copying from source environment or GitHub URL"""
    # Validate environment name for security
    validate_environment_name(name)

    logger.info(f"Creating environment '{name}' from '{source}'")
    envs_dir = get_envs_dir()

    # Check if initialized
    if not envs_dir.exists():
        logger.error("cenv not initialized")
        raise InitializationError("cenv not initialized. Run 'cenv init' first.")

    # Check if environment already exists
    target_env = get_env_path(name)
    if target_env.exists():
        logger.error(f"Environment '{name}' already exists")
        raise EnvironmentExistsError(name)

    # Check if source is a GitHub URL
    if source.startswith("https://") or source.startswith("git@"):
        if not is_valid_github_url(source):
            logger.error(f"Invalid GitHub URL: {source}")
            raise GitOperationError("validation", source, "Invalid GitHub URL format")

        logger.info(f"Cloning from GitHub: {source}")
        clone_from_github(source, target_env)
    else:
        # Source is an environment name
        source_env = get_env_path(source)
        if not source_env.exists():
            logger.error(f"Source environment '{source}' not found")
            raise EnvironmentNotFoundError(source)

        # Copy source to target
        logger.debug(f"Copying {source_env} to {target_env}")
        shutil.copytree(source_env, target_env, symlinks=True)

    logger.info(f"Environment '{name}' created successfully")

def switch_environment(name: str, force: bool = False) -> None:
    """Switch to a different environment using atomic rename

    This operation is thread-safe and atomic - no intermediate broken state
    will be visible to concurrent readers.
    """
    # Validate environment name
    validate_environment_name(name)

    logger.info(f"Switching to environment '{name}' (force={force})")
    target_env = get_env_path(name)

    # Check if target environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise EnvironmentNotFoundError(name)

    # Check if Claude is running
    if is_claude_running() and not force:
        logger.warning("Claude is running, refusing to switch without force=True")
        raise ClaudeRunningError()

    # Use lock to prevent concurrent switches from interfering
    with _switch_lock:
        claude_dir = get_claude_dir()

        # Verify current state is valid or missing
        if claude_dir.exists() and not claude_dir.is_symlink():
            logger.error(f"{claude_dir} exists but is not a symlink")
            raise SymlinkStateError("~/.claude exists but is not a symlink. Cannot switch.")

        # Create temporary symlink with atomic rename
        # This ensures no intermediate broken state
        temp_link = claude_dir.parent / ".claude.tmp"

        try:
            # Remove temp link if it exists from previous failed operation
            if temp_link.exists():
                temp_link.unlink()

            # Create new symlink with temporary name
            logger.debug(f"Creating temporary symlink {temp_link} -> {target_env}")
            temp_link.symlink_to(target_env)

            # Atomic rename: this is the critical operation
            # On Unix, this is atomic - either old or new link exists, never neither
            logger.debug(f"Atomically replacing {claude_dir} with temporary symlink")
            temp_link.replace(claude_dir)

            logger.info(f"Switched to environment '{name}'")

        except Exception as e:
            # Clean up temporary symlink on error
            if temp_link.exists():
                logger.debug(f"Cleaning up temporary symlink after error")
                temp_link.unlink()
            raise

def delete_environment(name: str) -> None:
    """Delete an environment (moves to trash)"""
    # Validate environment name
    validate_environment_name(name)

    logger.info(f"Deleting environment '{name}'")
    target_env = get_env_path(name)

    # Check if environment exists
    if not target_env.exists():
        logger.error(f"Environment '{name}' does not exist")
        raise EnvironmentNotFoundError(name)

    # Check if it's currently active
    current = get_current_environment()
    if current == name:
        logger.error(f"Cannot delete active environment '{name}'")
        raise ActiveEnvironmentError(name)

    # Check if it's the default environment
    if name == "default":
        logger.error("Cannot delete default environment")
        raise ProtectedEnvironmentError(name)

    # Create trash directory if it doesn't exist
    trash_dir = get_trash_dir()
    trash_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup name
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_name = f"{name}-{timestamp}"
    backup_path = trash_dir / backup_name

    # Move to trash instead of deleting
    logger.info(f"Moving '{name}' to trash as '{backup_name}'")
    shutil.move(str(target_env), str(backup_path))
    logger.info(f"Environment '{name}' moved to trash (backup: {backup_name})")
