# Security Policy

## Supported Versions

We support security updates for the latest minor release only.

| Version | Supported          | Notes                |
| ------- | ------------------ | -------------------- |
| 0.1.x   | :white_check_mark: | Current stable       |
| < 0.1   | :x:                | Pre-release versions |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them using one of these methods:

1. **GitHub Security Advisories** (preferred): Use the "Security" tab on the GitHub repository to create a private security advisory
2. **Email**: Contact the maintainers listed in the repository AUTHORS file or package metadata

Include:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

You should receive a response within 48 hours.

## Security Measures

cenv implements several security measures:

### Input Validation
- All environment names validated against strict regex
- Path traversal prevention (../, etc.)
- Reserved name blocking (., .., .trash, etc.)
- Special character rejection

### Git Operations
- URL validation for GitHub repositories
- Operation timeouts (default: 5 minutes)
- Shallow clones by default
- .git directory removal after clone

### File Operations
- Atomic symlink switching
- Thread-safe operations
- File locking for concurrent access
- Backup mechanism (trash instead of hard delete)

### Platform Safety
- Unix-only (prevents Windows-specific attacks)
- Platform checks before operations
- fcntl file locking

## Best Practices

When using cenv:

1. **Close Claude before switching**: Don't rely solely on process detection
2. **Review Git URLs**: Verify repository URLs before cloning
3. **Use --verbose**: Enable logging for audit trails
4. **Regular backups**: Trash is not a permanent backup

## Version History

- **v0.1.0**: Initial security-hardened release
  - Input validation
  - Atomic operations
  - Thread safety
  - Platform checks
