# cenv Usage Guide

## Complete Workflow Example

### Initial Setup

```bash
# 1. Initialize cenv
$ cenv init
✓ Initialized cenv successfully!
  ~/.claude → ~/.claude-envs/default/

Use 'cenv create <name>' to create new environments.

# 2. Check what you have
$ cenv list
Available environments:
 → default

$ cenv current
default
```

### Creating Environments

```bash
# Create work environment (copies from default)
$ cenv create work
✓ Created environment 'work' from default

# Create from GitHub template
$ cenv create client-project --from-repo https://github.com/company/claude-client-setup
✓ Created environment 'client-project' from https://github.com/company/claude-client-setup

# List all environments
$ cenv list
Available environments:
   client-project
 → default
   work
```

### Switching Environments

```bash
# Switch to work environment
$ cenv use work
✓ Switched to environment 'work'

# Verify current environment
$ cenv current
work

# If Claude is running, you'll be prompted
$ cenv use personal
⚠️  Claude is running. Switching environments may cause issues.
Continue anyway? [y/N]: y
✓ Switched to environment 'personal'

# Skip the prompt with --force
$ cenv use work --force
✓ Switched to environment 'work'
```

### Managing Environments

```bash
# Delete an environment
$ cenv delete experiment
Delete environment 'experiment'? [y/N]: y
✓ Deleted environment 'experiment'

# Force delete without confirmation
$ cenv delete experiment --force
✓ Deleted environment 'experiment'

# Cannot delete default or active environment
$ cenv delete default
Error: Cannot delete default environment.

$ cenv current
work
$ cenv delete work
Error: Environment 'work' is currently active. Switch to another environment first.
```

## Advanced Usage

### GitHub Repository Templates

Create a repository with your Claude configuration:

```
my-claude-setup/
  ├── CLAUDE.md
  ├── settings.json
  ├── agents/
  │   └── custom-agent.md
  └── plugins/
      └── config.json
```

Share with your team:

```bash
cenv create team-setup --from-repo https://github.com/yourteam/claude-team-setup
```

### Environment Organization

**Strategy 1: By Project**
```bash
cenv create client-a
cenv create client-b
cenv create internal
```

**Strategy 2: By Role**
```bash
cenv create development  # Coding-focused plugins
cenv create writing      # Writing-focused agents
cenv create research     # Research tools
```

**Strategy 3: By Experiment**
```bash
cenv create stable       # Known good configuration
cenv create testing      # Try new things
```

## Troubleshooting

### "Claude is running" Warning

If you see this warning, either:
1. Exit Claude completely, then switch
2. Use `--force` flag (may cause issues with running session)

### Cannot Switch Environments

Check that `~/.claude` is a symlink:
```bash
ls -la ~/.claude
```

Should show: `~/.claude -> /Users/you/.claude-envs/default`

### Environment Missing After Switch

Verify environments exist:
```bash
ls ~/.claude-envs/
```

Check current symlink target:
```bash
readlink ~/.claude
```

### Reset to Default

If something goes wrong:
```bash
# Switch back to default
cenv use default --force

# Or manually:
rm ~/.claude
ln -s ~/.claude-envs/default ~/.claude
```
