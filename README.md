# cenv - Claude Environment Manager

Manage isolated Claude Code configurations like pyenv manages Python versions. Switch between different Claude setups (work, personal, experiments) with complete isolation.

## Installation

```bash
# Using uvx (no installation required, runs on-demand from local directory)
uvx --from . cenv --help

# Once published to PyPI, you'll be able to run directly:
# uvx cenv --help

# Or install locally with uv (recommended for regular use)
git clone https://github.com/vtemian/cenv.git
cd cenv
uv pip install -e .

# Or using pip
pip install -e .
```

## Quick Start

```bash
# Initialize cenv (migrates your current ~/.claude to default environment)
cenv init

# Create a new environment for work
cenv create work

# Switch to work environment
cenv use work

# List all environments (* marks active)
cenv list

# Show current environment
cenv current

# Delete an environment
cenv delete work
```

## Features

- **Complete Isolation**: Each environment has its own CLAUDE.md, settings.json, agents, plugins
- **Symlink-based**: Fast switching with no data copying
- **Safety Checks**: Warns when Claude is running
- **GitHub Templates**: Clone environment configs from repositories
- **Shared Credentials**: API keys stored in macOS Keychain work across all environments

## Configuration

cenv can be configured via environment variables or a config file.

### Config File

Create `~/.cenvrc`:

```ini
# Git operation timeout in seconds (default: 300)
git_timeout = 600

# Logging level (default: INFO)
log_level = DEBUG
```

### Environment Variables

```bash
export CENV_GIT_TIMEOUT=600
export CENV_LOG_LEVEL=DEBUG
```

### Configuration Precedence

1. Environment variables (highest priority)
2. `~/.cenvrc` file
3. Built-in defaults (lowest priority)

### Available Options

- `CENV_GIT_TIMEOUT` / `git_timeout`: Git operation timeout in seconds (default: 300)
- `CENV_LOG_LEVEL` / `log_level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

## Commands

### `cenv init`

Initialize cenv by migrating your existing `~/.claude` to `~/.claude-envs/default/`.

```bash
cenv init
```

### `cenv create <name>`

Create a new environment. By default, copies from the `default` environment.

```bash
# Create from default
cenv create work

# Create from GitHub repository
cenv create work --from-repo https://github.com/user/claude-work-setup
```

### `cenv use <name>`

Switch to a different environment. Prompts for confirmation if Claude is running.

```bash
cenv use work

# Force switch without confirmation
cenv use work --force
```

### `cenv list`

List all available environments. Active environment is marked with `→`.

```bash
cenv list
```

### `cenv current`

Show the currently active environment.

```bash
cenv current
```

### `cenv delete <name>`

Delete an environment. Cannot delete the `default` environment or currently active environment.

```bash
cenv delete work

# Skip confirmation
cenv delete work --force
```

## How It Works

cenv uses symlinks for fast, efficient environment switching:

```
~/.claude              → symlink to active environment
~/.claude-envs/
  ├── default/         Your original setup
  ├── work/            Work configuration
  └── personal/        Personal configuration
```

Each environment contains:
- `CLAUDE.md` - Global instructions
- `settings.json` - Settings and preferences
- `agents/` - Custom agents
- `plugins/` - Installed plugins
- `history.jsonl`, `sessions/`, etc.

## Use Cases

**Work vs Personal**: Separate configurations for professional and personal use
```bash
cenv create work
cenv create personal
```

**Experimentation**: Test new plugins or settings without affecting your main setup
```bash
cenv create experiment
# Try new things...
cenv delete experiment
```

**Team Templates**: Share environment configs via GitHub
```bash
cenv create work --from-repo https://github.com/company/claude-work-template
```

## Security

- Git clone operations use shallow clones (`--depth 1`) and have a 5-minute timeout
- All operations use custom exception types for better error handling
- Comprehensive logging available with `--verbose` flag
- See [SECURITY.md](docs/SECURITY.md) for security considerations

## Logging

Enable verbose logging:

```bash
cenv --verbose list
```

Write logs to file:

```bash
cenv --log-file ~/cenv.log list
```

## Trash and Recovery

Deleted environments are moved to trash instead of permanently deleted:

```bash
# Delete an environment (moves to trash)
cenv delete myenv

# List deleted environments
cenv trash

# Restore from trash
cenv restore myenv-20251111-143022
```

## Development

```bash
# Install with dev dependencies
make install

# Run tests
make test

# Run type checking
make typecheck

# Clean build artifacts
make clean
```

## License

MIT
