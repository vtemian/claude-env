# claude-env

**Switch between Claude Code configurations instantly.**

---

**You only get one `~/.claude` directory.**

That means one set of instructions. One settings file. One configuration for everything.

Want to try a new plugin? Hope it doesn't break your workflow. Need different settings for work projects? Better remember to change them back. Want to share your team's Claude setup? Time to write a manual.

**There has to be a better way.**

---

## What is claude-env?

Think `pyenv`, but for Claude Code. Isolated environments you can switch between instantly.

```bash
cenv use work        # Corporate coding standards, work plugins
cenv use personal    # Your personal setup, your way
cenv use experiment  # Try that new agent without fear
```

Instant switching. Complete isolation. Zero copying. Just symlinks doing the heavy lifting.

```bash
uvx claude-env --help
```

[![PyPI version](https://badge.fury.io/py/claude-env.svg)](https://badge.fury.io/py/claude-env)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/vtemian/claude-env/workflows/CI/badge.svg)](https://github.com/vtemian/claude-env/actions)
[![Code Quality: A+](https://img.shields.io/badge/code%20quality-A%2B-brightgreen)](https://github.com/vtemian/claude-env)

---

## Features

**Instant Switching** - Symlinks make switching instant. No waiting, no copying gigabytes of data.

**Complete Isolation** - Each environment is a separate world. CLAUDE.md, settings.json, agents, plugins, history - all isolated.

**Team Templates** - Clone environment configs from GitHub. Onboard new devs in one command. Publish your setup for others to use.

**Safety Built-In** - Warns when Claude is running. Validates all inputs. Atomic operations. Deleted environments go to trash, not `/dev/null`.

**Zero Config** - `cenv init` and you're done. But configurable when you need it.

---

## Installation

**Recommended: Use uvx (no installation required)**

```bash
# Run directly with uvx - no installation needed
uvx claude-env init
uvx claude-env list
uvx claude-env use work
```

**Alternative: Install with pip**

```bash
pip install claude-env
cenv init
```

**For development:**

```bash
git clone https://github.com/vtemian/claude-env.git
cd claude-env
uv pip install -e .
```

## Quick Start

```bash
# One-time setup: migrate your existing ~/.claude
uvx claude-env init

# Create environments for different contexts
uvx claude-env create work
uvx claude-env create experiment

# Switch between them instantly
uvx claude-env use work        # → Now using work
uvx claude-env use experiment  # → Now using experiment

# See what you have
uvx claude-env list
#   default
#   work
# → experiment  (← indicates active)

# Done experimenting? Clean up.
uvx claude-env delete experiment
```

That's it. Your environments are isolated, switching is instant, and you can't accidentally break your main setup.

**Tip:** If you prefer shorter commands, install with pip and use `cenv` instead of `uvx claude-env`.

---

## Real-World Use Cases

### The Side Project Developer
```bash
# Keep work and personal projects separate
uvx claude-env create work
uvx claude-env create personal

# Work projects use corporate standards
uvx claude-env use work  # Strict guidelines, team plugins

# Side projects use your personal preferences
uvx claude-env use personal  # Your style, your tools
```

### The Plugin Experimenter
```bash
# Want to try that new agent everyone's talking about?
uvx claude-env create test-new-agent
uvx claude-env use test-new-agent
# Install plugin, test it out...
# Not impressed?
uvx claude-env use default
uvx claude-env delete test-new-agent  # Moved to trash, just in case
```

### The Team Lead
```bash
# Create and share your team's configuration
uvx claude-env create team-setup
uvx claude-env use team-setup
# Configure settings, install plugins, write CLAUDE.md...

# Publish to GitHub (repo must exist)
uvx claude-env publish https://github.com/company/claude-setup

# Team members onboard in seconds:
uvx claude-env create team --from-repo https://github.com/company/claude-setup
uvx claude-env use team
# Done. Everyone has the same setup.
```

---

## Command Reference

| Command | What it does |
|---------|--------------|
| `uvx claude-env init` | One-time setup: migrates `~/.claude` to `~/.claude-envs/default/` |
| `uvx claude-env create <name>` | Create new environment (copies from default) |
| `uvx claude-env create <name> --from-repo <url>` | Create from GitHub repository |
| `uvx claude-env use <name>` | Switch to environment (warns if Claude is running) |
| `uvx claude-env use <name> --force` | Switch without warning |
| `uvx claude-env list` | Show all environments (→ marks active) |
| `uvx claude-env current` | Show active environment name |
| `uvx claude-env delete <name>` | Move environment to trash |
| `uvx claude-env publish <repo-url>` | Publish active environment to GitHub |
| `uvx claude-env trash` | List deleted environments |
| `uvx claude-env restore <backup>` | Restore from trash |

**Note:** If installed with pip, replace `uvx claude-env` with `cenv` for shorter commands.

---

## How It Works

One symlink. Multiple worlds.

```
~/.claude  →  points to whichever environment is active

~/.claude-envs/
  ├── default/          ← Your original ~/.claude (moved here during init)
  │   ├── CLAUDE.md
  │   ├── settings.json
  │   ├── agents/
  │   ├── plugins/
  │   └── ...
  │
  ├── work/             ← Team configuration
  │   ├── CLAUDE.md     (corporate guidelines)
  │   ├── settings.json (stricter settings)
  │   └── ...
  │
  └── experiment/       ← Testing ground
      └── ...
```

When you run `uvx claude-env use work`, we atomically swap the symlink. Claude Code sees a different `~/.claude` directory instantly. No copying. No waiting. Just works.

---

## Security & Safety

Built with paranoia:

- **Input validation** - Path traversal? Command injection? Not here.
- **Git safety** - Shallow clones, 5-minute timeouts, controlled operations
- **Atomic operations** - Environment switches are atomic. Never a broken state.
- **Process awareness** - Warns you if Claude is running before switching
- **Trash, not delete** - Deleted environments go to trash. Mistakes happen.

See [SECURITY.md](SECURITY.md) for the full story.

## Advanced Features

**Publish & Share** - Push your environment to GitHub for others to clone.
```bash
uvx claude-env publish https://github.com/you/claude-config
# Sensitive files (.env, credentials.json, *.key) are automatically excluded
```

**Trash & Restore** - Deleted environments go to trash with timestamps. Restore anytime.
```bash
uvx claude-env delete experiment       # Moved to trash
uvx claude-env trash                   # List backups
uvx claude-env restore experiment-...  # Changed your mind
```

**Debug Logging** - When things go wrong (they won't, but just in case):
```bash
uvx claude-env --verbose list              # Detailed output
uvx claude-env --log-file ~/debug.log init # Log to file
```

**Custom Configuration** - Environment variables or `~/.cenvrc`:
```bash
export CENV_GIT_TIMEOUT=600
export CENV_LOG_LEVEL=DEBUG
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick dev setup:**
```bash
git clone https://github.com/vtemian/claude-env.git
cd claude-env
make install  # Install with dev dependencies
make check    # Run all tests, type checking, linting
```

**Project stats:**
- 157 tests, 93% coverage
- Type-safe with `mypy --strict`
- Code quality: A+ (97/100)
- Zero linting violations

---

## Why We Built This

Because managing one Claude configuration for everything is like having one Git branch for all your projects. It works, technically. But there's a better way.

**Install claude-env. Create isolated environments. Switch fearlessly.**

```bash
uvx claude-env init
```

## License

MIT - See [LICENSE](LICENSE) for details.
