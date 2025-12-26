---
date: 2025-12-26
topic: "Path Portability for Config Import/Export"
status: validated
issue: https://github.com/vtemian/claude-env/issues/1
---

# Path Portability for Config Import/Export

## Problem Statement

When importing a Claude config via `cenv create --from-repo`, config files (e.g., `settings.json`, `plugins/known_marketplaces.json`) contain hardcoded absolute paths from the original user's machine. These paths don't work on the importing user's system.

Example: A config published by user A contains `/Users/userA/.claude/plugins/...`, which doesn't exist on user B's machine.

## Constraints

- Must work cross-platform (macOS, Linux, Windows)
- Must handle paths at any depth in JSON structures
- Must handle paths embedded in larger strings
- Cannot fix project paths or system paths (no way to know target location)
- Must not break existing publish/import functionality
- Transform temp copy on publish, not source environment

## Approach

Use placeholder tokens during publish, expand them during import.

**Placeholders:**
- `{{USER_HOME}}` - User's home directory (e.g., `/Users/vlad`, `C:\Users\vlad`)
- `{{CLAUDE_HOME}}` - Claude config directory (e.g., `/Users/vlad/.claude`)

**Why this approach:**
- Clean, reversible solution
- Shifts the problem to publish-time where we have full control
- No guesswork during import
- Familiar double-brace syntax (Jinja, Handlebars style)

## Architecture

Two new operations integrated into existing flows:

**Publish flow (existing `cenv publish` command):**
1. Existing: Filter sensitive files, transform plugins manifest
2. **New:** After copying to temp dir, scan all `.json` files
3. **New:** Replace absolute paths with placeholders
4. **New:** Warn about paths that couldn't be substituted
5. Existing: Push to GitHub

**Import flow (existing `cenv create --from-repo`):**
1. Existing: Clone repo, remove `.git`
2. **New:** Scan all `.json` files in cloned content
3. **New:** Expand placeholders to local paths
4. Existing: Install plugins, setup symlinks

No new commands or CLI changes - this is transparent to the user.

## Components

### New module: `src/cenv/path_portability.py`

Responsibilities:
- Detect absolute paths belonging to a user's home directory
- Replace paths with placeholders (for publish)
- Expand placeholders to local paths (for import)
- Walk JSON structures recursively
- Handle embedded paths within strings
- Report paths that couldn't be substituted

Key functions:

| Function | Purpose |
|----------|---------|
| `substitute_paths_with_placeholders` | Takes JSON content, returns transformed content + warnings |
| `expand_placeholders_to_paths` | Takes JSON content with placeholders, returns expanded content |
| `process_json_files_for_publish` | Walks directory, processes all `.json` files for publish |
| `process_json_files_for_import` | Walks directory, processes all `.json` files for import |

### Modifications to existing modules

| Module | Change |
|--------|--------|
| `publish.py` | Call `process_json_files_for_publish` after copying to temp dir |
| `github.py` | Call `process_json_files_for_import` after clone, before moving to final location |

## Data Flow

### Publish (path to placeholder)

```
User runs: cenv publish my-env --repo git@github.com:user/config.git

1. Detect current user's home: /Users/vlad
2. Detect Claude home: /Users/vlad/.claude
3. Copy environment to temp directory (existing)
4. For each .json file in temp directory:
   a. Parse JSON
   b. Walk all string values (recursive, any depth)
   c. In each string:
      - Replace /Users/vlad/.claude -> {{CLAUDE_HOME}}  (more specific first)
      - Replace /Users/vlad -> {{USER_HOME}}
   d. Collect warnings for unsubstitutable paths (e.g., /usr/local/bin/foo)
   e. Write transformed JSON back
5. Log warnings about paths that couldn't be made portable
6. Continue with existing publish flow (push to GitHub)
```

### Import (placeholder to path)

```
User runs: cenv create my-env --from-repo git@github.com:user/config.git

1. Clone repo to temp dir (existing)
2. Detect current user's home: /Users/newuser
3. Detect Claude home: /Users/newuser/.claude
4. For each .json file in cloned content:
   a. Parse JSON
   b. Walk all string values (recursive, any depth)
   c. In each string:
      - Replace {{CLAUDE_HOME}} -> /Users/newuser/.claude
      - Replace {{USER_HOME}} -> /Users/newuser
   d. Write expanded JSON back
5. Move to final location (existing)
6. Install plugins, setup symlinks (existing)
```

## Path Detection & Warning Logic

### On publish, detecting paths to substitute

1. **Claude home paths** (highest priority): Any path starting with current user's Claude directory
   - macOS/Linux: `/Users/vlad/.claude` or `/home/vlad/.claude`
   - Windows: `C:\Users\vlad\.claude` (and forward-slash variants)
   - Replaced with `{{CLAUDE_HOME}}`

2. **User home paths**: Any path starting with current user's home directory
   - Replaced with `{{USER_HOME}}`

3. **Order matters**: Replace `{{CLAUDE_HOME}}` first (more specific), then `{{USER_HOME}}`

### Paths that trigger warnings (cannot substitute)

- Absolute paths that don't start with current user's home
- Examples:
  - `/usr/local/bin/something`
  - `/opt/homebrew/...`
  - `/Users/otheruser/...`
  - `C:\Program Files\...`

### Warning output

```
Warning: The following paths could not be made portable:
  - settings.json: /usr/local/bin/custom-tool
  - plugins/foo.json: /opt/homebrew/bin/node
These paths may not exist on other machines.
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| JSON parsing error | Log warning, skip file, continue with others |
| File write error | Raise error, abort operation (partial transform is broken state) |
| Empty or missing file | Skip gracefully, no warning |
| Placeholder already present | Leave alone on publish, expand on import |
| Binary file with .json extension | JSON parse fails, skip with warning |

## Testing Strategy

### Unit tests for `path_portability.py`

**Placeholder substitution:**
- Simple string with home path to `{{USER_HOME}}`
- Simple string with Claude path to `{{CLAUDE_HOME}}`
- String with both paths, correct precedence (Claude first)
- Embedded path in larger string, partial substitution
- Path not matching home, unchanged with warning generated

**Placeholder expansion:**
- `{{USER_HOME}}` to current home directory
- `{{CLAUDE_HOME}}` to current Claude directory
- Both in same string, both expanded

**JSON structure handling:**
- Nested objects (deep paths)
- Arrays of strings
- Mixed arrays (strings and objects)
- Non-string values (numbers, booleans, null) unchanged

**Cross-platform paths:**
- Forward slashes on all platforms
- Backslashes on Windows
- Mixed separators

**Edge cases:**
- Empty JSON object
- Malformed JSON, graceful skip
- File with no paths, unchanged
- Placeholder already present, no double-substitution

### Integration tests

- **Publish flow:** Verify `.json` files in published output contain placeholders, not absolute paths
- **Import flow:** Verify `.json` files after import contain local paths, not placeholders
- **Round-trip:** Publish from user A, import as user B, verify paths are correct for user B

## Open Questions

None - all questions resolved during design.
