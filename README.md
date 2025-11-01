# cenv - Claude Environment Manager

Manage isolated Claude Code configurations like pyenv manages Python versions. Switch between different Claude setups (work, personal, experiments) with complete isolation.

## Installation

```bash
# Using uv (recommended)
git clone https://github.com/yourusername/cenv.git
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

## Development

```bash
# Install with dev dependencies
make install

# Run tests
make test

# Clean build artifacts
make clean
```

## License

MIT
