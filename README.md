# claude-env

**Switch between Claude Code configurations instantly.**

[![PyPI version](https://badge.fury.io/py/claude-env.svg)](https://badge.fury.io/py/claude-env)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/vtemian/claude-env/workflows/CI/badge.svg)](https://github.com/vtemian/claude-env/actions)

---

## Quick Start

```bash
uvx claude-env init              # One-time setup
uvx claude-env create work       # Create environment
uvx claude-env use work          # Switch to it
```

---

## Why?

You only get one `~/.claude` directory. One set of instructions, one settings file, one configuration for everything.

claude-env gives you isolated environments you can switch between instantly. Think `pyenv`, but for Claude Code.

---

## Features

- **Instant Switching** - Symlinks make switching instant. No copying.
- **Complete Isolation** - CLAUDE.md, settings, plugins, history - all isolated.
- **Team Templates** - Clone configs from GitHub. Onboard in one command.
- **Safety Built-In** - Warns when Claude is running. Deleted environments go to trash.

---

## How It Works

```
~/.claude  →  symlink to active environment

~/.claude-envs/
  ├── default/      ← Original ~/.claude (moved during init)
  ├── work/         ← Team configuration
  └── experiment/   ← Testing ground
```

`uvx claude-env use work` atomically swaps the symlink. Claude sees a different `~/.claude` instantly.

---

## Commands

| Command | Description |
|---------|-------------|
| `init` | Migrate `~/.claude` to `~/.claude-envs/default/` |
| `create <name>` | Create new environment |
| `create <name> --from-repo <url>` | Create from GitHub repo |
| `use <name>` | Switch to environment |
| `list` | Show all environments |
| `current` | Show active environment |
| `delete <name>` | Move to trash |
| `publish <repo-url>` | Push to GitHub |
| `trash` | List deleted environments |
| `restore <name>` | Restore from trash |

**Tip:** Install with `pip install claude-env` to use `cenv` instead of `uvx claude-env`.

---

## Development

```bash
git clone https://github.com/vtemian/claude-env.git
cd claude-env
make install && make check
```

157 tests, 93% coverage, type-safe with mypy --strict.

---

## License

MIT - See [LICENSE](LICENSE)
