# Security Considerations

## Git Clone Operations

- **Timeout**: All git clone operations have a 5-minute timeout to prevent hanging
- **Shallow Clone**: Uses `--depth 1` to minimize data transfer and disk usage
- **URL Validation**: GitHub URLs are validated with regex before cloning

## File Operations

- **Atomic Operations**: Initialization uses file locks to prevent race conditions
- **Backup System**: Deleted environments are moved to trash, not permanently deleted
- **Symlink Validation**: All symlink operations validate paths

## Logging

- Sensitive information is not logged
- Log files may contain file paths and environment names
- Use `--log-file` carefully in shared environments

## Best Practices

1. Always use HTTPS URLs for git clone operations
2. Review environment contents before switching
3. Use `--verbose` flag when debugging issues
4. Keep cenv updated to latest version
5. Backup important configurations separately

## Reporting Security Issues

Please report security vulnerabilities by opening a GitHub issue at:
https://github.com/vtemian/cenv/issues

For sensitive security issues that should not be disclosed publicly, please use GitHub's private vulnerability reporting feature if available, or contact the maintainers directly through GitHub.
