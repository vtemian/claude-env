# claude-env

**Switch between Claude Code configurations instantly. Share yours with the community.**

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

**Try someone's config in seconds:**
```bash
uvx claude-env create tdd --from-repo https://github.com/user/claude-tdd-config
uvx claude-env use tdd
```

---

## Why?

You only get one `~/.claude` directory. One set of instructions, one settings file, one configuration for everything.

claude-env gives you isolated environments you can switch between instantly. Publish your setup, share it with others, and try community configs with a single command. Think `pyenv` meets `dotfiles`, but for Claude Code.

---

## Features

- **Instant Switching** - Symlinks make switching instant. No copying.
- **Complete Isolation** - CLAUDE.md, settings, plugins, history - all isolated.
- **Share & Discover** - Publish your config to GitHub. Try others with one command.
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

## Share Your Config

**Publish your setup:**
```bash
uvx claude-env publish https://github.com/you/my-claude-config
```

This pushes your CLAUDE.md, settings, commands, and plugins (minus credentials) to a repo. Share the link and anyone can try it:

```bash
uvx claude-env create my-config --from-repo https://github.com/you/my-claude-config
```

Perfect for sharing team setups, teaching workflows, or showcasing your Claude customizations.

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

169 tests, 88% coverage, type-safe with mypy --strict.

---

## License

MIT - See [LICENSE](LICENSE)
