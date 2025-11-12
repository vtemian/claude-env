# Contributing to cenv

Thank you for considering contributing to cenv!

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone YOUR fork
git clone https://github.com/<your-username>/cenv.git
cd cenv

# 3. Add upstream remote
git remote add upstream https://github.com/vtemian/cenv.git

# 4. Install in development mode with dev dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cenv --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py -v
```

### Type Checking

```bash
# Run mypy type checker
mypy src/cenv --strict

# Should output: Success: no issues found
```

### Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters
- **Type hints**: Required for all functions
- **Docstrings**: Google style
- **f-strings**: Preferred over .format()

### Testing Guidelines

- **Test-Driven Development**: Write tests before code
- **Coverage**: Maintain >90% coverage
- **Edge cases**: Test error conditions

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `chore`: Build/tooling changes

Examples:
```
feat(cli): add --dry-run flag
fix(core): prevent race condition in switch
docs(readme): add troubleshooting section
```

### Design Principles

1. **Functional First**: Prefer functions over classes
2. **Type Safety**: Use type hints everywhere
3. **Fail Fast**: Validate early, raise clear errors
4. **Atomic Operations**: No partial state
5. **Security First**: Validate all inputs

## Pull Request Process

### Before Submitting

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following the guidelines above
4. **Run all checks**:
   ```bash
   pytest --cov=src/cenv --cov-report=term-missing
   mypy src/cenv --strict
   ```
5. **Update documentation** if you changed APIs
6. **Add tests** for new functionality

### Submitting

1. **Push to your fork**:
   ```bash
   git push origin feat/your-feature-name
   ```
2. **Create Pull Request** on GitHub
3. **Fill out PR template** with:
   - What changed
   - Why the change was needed
   - How to test it
   - Screenshots (if UI changes)

### Review Process

- Maintainers will review your PR within 48 hours
- CI must pass (tests, type checking)
- At least one approval required
- Address review feedback by pushing new commits
- Once approved, maintainers will merge

### After Merging

- Delete your feature branch
- Pull latest main
- Your contribution will appear in next release!

## Questions?

Open an issue with the question label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
