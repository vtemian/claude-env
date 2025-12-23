# Architecture

## Overview

**cenv** (claude-env) is a CLI tool for managing isolated Claude Code configurations, similar to how pyenv manages Python versions. It allows users to switch between different Claude Code setups, share configurations via GitHub, and maintain separate environments for different workflows.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI Framework | Typer |
| Process Detection | psutil |
| Build System | Hatchling (PEP 517) |
| Package Manager | uv |
| Type Checking | mypy (strict mode) |
| Linting | ruff |
| Testing | pytest + pytest-cov |
| CI/CD | GitHub Actions |

## Directory Structure

```
cenv/
├── src/cenv/                    # Source code (src-layout)
│   ├── __init__.py              # Package exports, version
│   ├── cli.py                   # Typer CLI commands
│   ├── core.py                  # Core business logic
│   ├── config.py                # Configuration management
│   ├── exceptions.py            # Exception hierarchy
│   ├── validation.py            # Input validation
│   ├── github.py                # GitHub integration
│   ├── publish.py               # Publish command logic
│   ├── process.py               # Process detection (Claude running?)
│   ├── platform_utils.py        # Cross-platform utilities
│   └── logging_config.py        # Logging setup
│
├── tests/                       # Test suite (30 files)
│   ├── test_cli_*.py            # CLI command tests
│   ├── test_core.py             # Core logic tests
│   └── test_*.py                # Other unit/integration tests
│
├── docs/                        # Documentation
│   ├── usage.md                 # User guide
│   └── plans/                   # Development plans (historical)
│
├── .github/workflows/           # CI/CD
│   ├── ci.yml                   # Tests, type-check, lint
│   └── publish.yml              # PyPI publishing
│
├── pyproject.toml               # Project config (deps, tools)
├── Makefile                     # Dev commands
└── uv.lock                      # Dependency lock
```

## Core Components

### CLI Layer (`cli.py`)

Entry point for all user commands. Uses Typer for argument parsing and help generation.

| Command | Function | Description |
|---------|----------|-------------|
| `init` | `init()` | Migrate ~/.claude to managed structure |
| `create` | `create()` | Create new environment |
| `use` | `use()` | Switch active environment |
| `list` | `list_cmd()` | Show all environments |
| `current` | `current()` | Show active environment |
| `delete` | `delete()` | Move environment to trash |
| `trash` | `trash()` | List deleted environments |
| `restore` | `restore()` | Restore from trash |
| `publish` | `publish()` | Push to GitHub repo |

### Core Logic (`core.py`)

Business logic for environment management. Key operations:

- **Path utilities**: `get_envs_dir()`, `get_env_path()`, `get_claude_dir()`
- **Environment ops**: `init_environments()`, `create_environment()`, `switch_environment()`, `delete_environment()`
- **Trash management**: `list_trash()`, `restore_from_trash()`
- **Shared items**: `setup_shared_symlinks()` - shares `projects/` and `.credentials.json` across envs

### Exception Hierarchy (`exceptions.py`)

```
CenvError (base)
├── EnvironmentNotFoundError
├── EnvironmentExistsError
├── ClaudeRunningError
├── InitializationError
├── GitOperationError
├── PlatformNotSupportedError
├── InvalidBackupFormatError
├── SymlinkStateError
├── ActiveEnvironmentError
└── ProtectedEnvironmentError
```

### Validation (`validation.py`)

Security-focused input validation:
- Environment names: alphanumeric, hyphens, underscores only
- Reserved names blocked: `.`, `..`, `.trash`, `.git`, `.backup`
- Prevents path traversal attacks

### Configuration (`config.py`)

Thread-safe singleton configuration:
- Loads from `~/.cenvrc` file
- Environment variable overrides (`CENV_*`)
- Settings: `git_timeout`, `log_level`

## Data Flow

### Initialization (`cenv init`)

```
~/.claude (existing)
    │
    ├── [backup created]
    │
    └── move to ~/.claude-envs/default/
                    │
                    └── symlink ~/.claude → ~/.claude-envs/default/
```

### Environment Switch (`cenv use <name>`)

```
1. Validate name
2. Check Claude not running (or --force)
3. Acquire switch lock
4. Create temp symlink: ~/.claude.tmp → ~/.claude-envs/<name>
5. Atomic rename: ~/.claude.tmp → ~/.claude
6. Release lock
```

The atomic rename ensures no intermediate broken state.

### Shared Items

Certain items are shared across all environments via symlinks:

```
~/.claude-envs/
├── .shared/
│   ├── projects/           # Shared across all envs
│   └── .credentials.json   # OAuth credentials
├── default/
│   ├── projects → ../.shared/projects
│   └── .credentials.json → ../.shared/.credentials.json
└── work/
    ├── projects → ../.shared/projects
    └── .credentials.json → ../.shared/.credentials.json
```

## External Integrations

### GitHub (`github.py`)

- Clone repositories for `--from-repo` option
- Validate GitHub URLs
- Handle authentication via git credential helpers

### Publish (`publish.py`)

- Push environment to GitHub repository
- Exclude sensitive files (credentials, tokens)
- Install plugins from manifest on clone

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CENV_GIT_TIMEOUT` | 300 | Git operation timeout (seconds) |
| `CENV_LOG_LEVEL` | INFO | Logging level |

### Config File (`~/.cenvrc`)

```ini
git_timeout = 600
log_level = DEBUG
```

### Tool Configuration (`pyproject.toml`)

- **ruff**: Line length 100, Python 3.10+, E/F/I/W/UP rules
- **mypy**: Strict mode, all type checks enabled
- **pytest**: Coverage reporting to XML

## Build & Deploy

### Development

```bash
make install      # Install with dev dependencies
make test         # Run tests
make test-cov     # Run tests with coverage
make typecheck    # Run mypy
make lint         # Run ruff
make check        # All checks (lint + typecheck + test-cov)
make format       # Auto-fix lint issues
make clean        # Remove build artifacts
```

### CI Pipeline

1. **test**: pytest on Ubuntu/macOS, Python 3.10-3.12
2. **type-check**: mypy strict on Python 3.10
3. **lint**: ruff check with GitHub output format

### Publishing

- Triggered on GitHub releases/tags
- Uses PyPI trusted publishing
- Package name: `claude-env`
- Entry points: `cenv`, `claude-env`

## Key Design Decisions

1. **src-layout**: Isolates package from project root, prevents import confusion
2. **Atomic symlink switch**: Uses temp link + rename for safe environment switching
3. **Trash instead of delete**: Environments moved to `.trash/` with timestamps
4. **Shared items**: Projects and credentials shared to avoid duplication
5. **Thread-safe operations**: Locks for switch and config initialization
6. **Strict typing**: mypy strict mode for all source code
