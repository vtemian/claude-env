# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Explicit `__all__` exports in all modules
- Thread-safe configuration singleton
- Exception handling tests

### Fixed
- MyPy strict mode type checking errors
- Race condition in config singleton
- Bare except clauses swallowing critical exceptions

## [0.1.0] - 2025-11-11

### Added
- Initial release
- Environment management commands: init, create, use, list, current, delete
- GitHub repository cloning support
- Trash/restore functionality
- Platform compatibility checks
- Input validation for security
- Atomic environment switching operations
- Thread-safe logging
- Comprehensive test suite (122 tests, 91% coverage)
- Configuration system (environment variables and config file)

### Security
- Path traversal prevention
- Command injection prevention
- Reserved name validation
- Git operation timeouts

[Unreleased]: https://github.com/vtemian/cenv/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/vtemian/cenv/releases/tag/v0.1.0
