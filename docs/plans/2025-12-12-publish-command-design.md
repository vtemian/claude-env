# Publish Command Design

## Overview

Add a `cenv publish <repo-url>` command to share Claude configs so others can use them with `cenv create --from-repo`.

## Use Case

Users want to share their Claude configuration publicly (or with a team). The publish command pushes the currently active environment to a GitHub repository that others can then clone.

## Command Interface

```
cenv publish <repo-url>
```

**Arguments:**
- `repo-url`: GitHub repository URL (HTTPS or SSH format)

**Behavior:**
- Publishes the currently active environment
- Target repository must already exist (user creates it first)
- Uses regular git push (fails on conflicts - user resolves manually)
- Automatically excludes sensitive files

## Flow

1. Validate the repo URL (same patterns as `--from-repo`: GitHub HTTPS or SSH)
2. Get the currently active environment
3. Scan for sensitive files and exclude them
4. Clone the target repo to a temp directory
5. Copy environment files (minus sensitive ones) into the clone
6. Commit with message "Update Claude config via cenv publish"
7. Push to remote (regular push, fails on conflicts)
8. Clean up temp directory

## Sensitive File Handling

**Default exclusions** (files that will never be published):
- `credentials.json`, `credentials.*.json`
- `.env`, `.env.*`
- `*.key`, `*.pem`
- `secrets.json`, `secrets.*.json`
- `auth.json`, `tokens.json`
- Any file containing `secret`, `token`, `password`, `apikey` in the name

**Implementation:**
- Define patterns in a `SENSITIVE_PATTERNS` constant
- Scan environment directory before copying
- Log excluded files at DEBUG level (visible with `--verbose`)
- No override option - manual git for edge cases

## Git Operations

**Clone target repo:**
- Clone to temp directory using shallow clone (`--depth 1`)
- Use configured `git_timeout` from config
- Clear error on clone failure

**Prepare commit:**
- Clear existing files in clone (except `.git/`)
- Copy environment files, skipping sensitive ones
- Use `shutil.copytree` with `ignore` parameter

**Commit and push:**
- `git add -A` to stage all changes
- `git commit -m "Update Claude config via cenv publish"`
- `git push origin HEAD` (regular push, no force)

## Error Handling

| Scenario | Error Message |
|----------|---------------|
| Clone fails | "Repository not found or access denied" |
| Nothing to commit | "No changes to publish" |
| Push conflict | "Push failed - remote has changes not present locally" |
| Push auth fails | "Authentication failed - check your git credentials" |
| Not initialized | "cenv not initialized. Run 'cenv init' first." |
| No active env | "No active environment to publish" |

## Output

**Success:**
```
✓ Published environment 'work' to https://github.com/user/claude-config
  Excluded 2 sensitive files (use --verbose to see details)
```

**Success with verbose:**
```
✓ Published environment 'work' to https://github.com/user/claude-config
  Excluded sensitive files:
    - credentials.json
    - .env.local
```

## Code Structure

**New files:**
- `src/cenv/publish.py` - Core publish logic

**Modified files:**
- `src/cenv/cli.py` - Add `publish` command
- `src/cenv/core.py` - Export `publish_environment`

**Key functions in `publish.py`:**
```python
SENSITIVE_PATTERNS: set[str]
def is_sensitive_file(filename: str) -> bool
def get_files_to_publish(env_path: Path) -> tuple[list[Path], list[Path]]
def publish_to_repo(env_path: Path, repo_url: str) -> PublishResult
```

## Testing

**Unit tests (`tests/test_publish.py`):**
- `test_sensitive_file_detection`
- `test_publish_excludes_sensitive_files`
- `test_publish_fails_on_invalid_url`
- `test_publish_fails_when_not_initialized`
- `test_publish_empty_environment`
- `test_publish_nothing_to_commit`

**CLI tests (`tests/test_cli_publish.py`):**
- `test_publish_command_calls_publish_environment`
- `test_publish_shows_excluded_files_count`

## Out of Scope (YAGNI)

- Auto-create repos (requires GitHub API/tokens)
- Force push option
- Publish specific environment (`--env` flag)
- Override sensitive file exclusions
- Commit message customization

## Dependencies

No new dependencies - uses existing git subprocess calls.
