# claude-env

**Share your Claude Code setup. Try anyone's in one command.**

[![PyPI version](https://badge.fury.io/py/claude-env.svg)](https://badge.fury.io/py/claude-env)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/vtemian/claude-env/workflows/CI/badge.svg)](https://github.com/vtemian/claude-env/actions)

---

## Try Someone's Config

```bash
uvx claude-env init
uvx claude-env create tdd --from-repo https://github.com/user/claude-tdd-config
uvx claude-env use tdd
```

That's it. You're now running their CLAUDE.md, settings, commands, and plugins.

---

## Share Your Config

```bash
uvx claude-env publish https://github.com/you/my-claude-config
```

Pushes your setup to a repo (credentials excluded). Share the link - anyone can try it instantly.

---

## Why?

People spend hours crafting Claude Code configs - custom instructions, slash commands, MCP servers, plugins. But there's no easy way to share them or try what others have built.

claude-env makes configs portable. Publish yours, try others, switch between setups instantly.

---

## How It Works

```
~/.claude  →  symlink to active environment

~/.claude-envs/
  ├── default/      ← Your original config
  ├── tdd/          ← Someone's TDD workflow
  └── data-science/ ← Another community config
```

Switching is instant - just swaps a symlink.

---

## Commands

| Command | Description |
|---------|-------------|
| `init` | One-time setup |
| `create <name> --from-repo <url>` | Try someone's config |
| `use <name>` | Switch to environment |
| `publish <repo-url>` | Share your config |
| `create <name>` | Create empty environment |
| `list` | Show all environments |
| `current` | Show active environment |
| `delete <name>` | Move to trash |
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
