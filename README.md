# claude-env

**Share your Claude Code setup. Try anyone's in one command.**

[![PyPI version](https://badge.fury.io/py/claude-env.svg)](https://badge.fury.io/py/claude-env)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/vtemian/claude-env/workflows/CI/badge.svg)](https://github.com/vtemian/claude-env/actions)

## Try Someone's Config

```bash
uvx claude-env init
uvx claude-env create tdd --from-repo https://github.com/user/claude-tdd-config
uvx claude-env use tdd
```


https://github.com/user-attachments/assets/88a14c52-0672-4dca-a60b-7f8211418d73


## Share Your Config

```bash
uvx claude-env publish https://github.com/you/my-claude-config
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | One-time setup |
| `create <name> --from-repo <url>` | Try someone's config |
| `publish <repo-url>` | Share your config |
| `use <name>` | Switch environment |
| `list` | Show environments |
| `delete <name>` | Remove environment |

## License

MIT
