# CLAUDE.md - Things CLI Project Knowledge

This document contains important context about the Things CLI project for AI assistants and future development.

## Project Overview

**Things CLI** is a command-line interface for Things 3 (macOS/iOS task manager) that provides both read and write capabilities through a hybrid architecture.

- **Repository**: https://github.com/skempken/things-cli
- **Language**: Python 3.10+
- **Package Manager**: uv
- **License**: MIT
- **Author**: Sebastian Kempken

## Architecture

### Hybrid Read/Write Design

The CLI uses **two different APIs** because Things 3 has distinct capabilities:

1. **Write Operations** → Things URL Scheme
   - Create, update, delete tasks/projects
   - Requires `THINGS_TOKEN` environment variable for modifications
   - Uses `subprocess` to execute `open things:///...` URLs
   - Supports dry-run mode

2. **Read Operations** → JXA (JavaScript for Automation)
   - Query tasks, projects, areas, tags
   - Requires Things 3 to be running
   - Uses `osascript -l JavaScript`
   - Returns JSON output

**Why this architecture?**
- Things 3 AppleScript/JXA API is intentionally **read-only**
- URL Scheme is the **only way** to write data
- Neither API can do both operations

### File Structure

```
things-cli/
├── things.py          # Main CLI (643 lines)
│   ├── URL Scheme commands (add, update, show, search, json)
│   ├── JXA list command
│   ├── Import/export functionality
│   └── Typer CLI app with subcommands
│
├── things_jxa.py      # JXA Helper Module (387 lines)
│   ├── run_jxa() - Execute JXA scripts
│   ├── get_list_tasks() - Query built-in lists
│   ├── get_tasks_by_tag/area/project() - Filtering
│   └── get_all_tags/areas/projects() - Metadata
│
├── pyproject.toml     # uv project config
├── README.md          # User documentation
├── LICENSE            # MIT License
├── .gitignore         # Excludes .venv, .env, Python cache
└── CLAUDE.md          # This file
```

## Key Technical Decisions

### 1. URL Encoding Bug Fix (Commit 180afe1)

**Problem**: The `list` command function shadowed Python's built-in `list` type, causing:
```python
isinstance(value, list)  # TypeError: isinstance() arg 2 must be a type
```

**Solution**: Changed to:
```python
hasattr(value, '__iter__') and not isinstance(value, str)
```

### 2. Space Encoding (Commit ad48840)

**Problem**: Tasks showed `+` instead of spaces (e.g., "CLI+Test:+Task")

**Solution**: Added `quote_via=quote` to `urlencode()`:
```python
query_string = urlencode(encoded_params, safe='', quote_via=quote)
```

### 3. German Localization

Things 3 is localized - list names are in German:
```python
LIST_NAME_MAP = {
    "inbox": "Eingang",
    "today": "Heute",
    "tomorrow": "Morgen",
    # ...
}
```

English commands map to German list names automatically.

### 4. JSON Output

All `list` commands use `print()` instead of `console.print()` to ensure valid JSON without ANSI codes.

## Important Limitations

### Things URL Scheme Limitations

1. **Tags in JSON imports must exist** - Cannot create new tags via JSON
   - Use `things add --tags new-tag` first to create tags
   - Then use JSON import with existing tags

2. **Rate limiting**: Maximum 250 items per 10 seconds

3. **Auth token required** for:
   - `update` and `update-project` commands
   - `json-command` and `import` commands
   - Set via `THINGS_TOKEN` environment variable

### JXA Limitations

1. **Read-only** - Cannot modify any data
2. **Requires Things 3 to be running**
3. **Synchronous** - Can be slow for large datasets
4. **No pagination** - Must fetch all matching items
5. **macOS only** - JXA is not available on other platforms

## Environment Setup

### Required Environment Variables

```bash
# Required for write operations (update, json import)
export THINGS_TOKEN="your-token-here"
```

Get token from: Things → Settings → General → Enable Things URLs → Manage

### Installation

```bash
cd things-cli
uv pip install -e .
```

### Running Commands

```bash
# Via uv (recommended during development)
uv run things.py <command>

# After installation
things <command>
```

## Common Development Workflows

### Testing Write Operations

Always use `--dry-run` first:
```bash
uv run things.py add --title "Test Task" --dry-run
# Check URL, then run without --dry-run
```

### Testing Read Operations

```bash
# JXA operations are read-only, safe to run anytime
uv run things.py list today
uv run things.py list tags
```

### Complete Workflow Example

```bash
# 1. Query available tags
uv run things.py list tags | grep "time"

# 2. Get today's tasks
uv run things.py list today > tasks.json

# 3. Update a task with tag
uv run things.py update --id <UUID> --add-tags "1h"

# 4. Verify update
uv run things.py list today
```

## Testing Checklist

### Write Operations (URL Scheme)
- [ ] `things add --title "Test" --dry-run` - Shows correct URL
- [ ] `things add --title "Test"` - Creates task in Things
- [ ] `things add-project` - Creates project
- [ ] `things update` - Updates existing task (requires token)
- [ ] `things show --id today` - Opens Today view
- [ ] `things search` - Opens search
- [ ] Spaces encoded as `%20`, not `+`

### Read Operations (JXA)
- [ ] `things list today` - Returns valid JSON
- [ ] `things list tags` - Lists all tags
- [ ] `things list areas` - Lists areas with counts
- [ ] `things list projects` - Lists projects
- [ ] `things list --tag work` - Filters by tag
- [ ] `things list --area Personal` - Filters by area

### JSON Operations
- [ ] `things export test.json --type task` - Creates template
- [ ] `things import test.json` - Imports tasks (requires token)
- [ ] JSON with existing tags works
- [ ] JSON with new tags fails (expected)

## Known Issues & Gotchas

### 1. List Name Collision

The `list` command function can shadow Python's `list` type in some contexts. Always use fully qualified names or hasattr checks.

### 2. Tag Creation

**URL Scheme**: Can create new tags automatically
```bash
things add --title "Test" --tags "new-tag"  # Creates "new-tag"
```

**JSON Import**: Cannot create new tags
```bash
things import tasks.json  # Fails if tags don't exist
```

### 3. Date Formats

Things accepts multiple date formats:
- `yyyy-mm-dd` (e.g., `2024-12-31`)
- Natural language (e.g., `today`, `tomorrow`, `in 3 days`)
- With time: `yyyy-mm-dd@HH:MM`

### 4. Task IDs

To get task UUIDs:
- **Mac**: Control-click → Share → Copy Link
- **iOS**: Open item → Share → Copy Link
- Extract UUID from `things:///show?id=<UUID>`

## Development Workflow

This project follows a structured issue-to-merge workflow for all feature development and bug fixes.

### Workflow Overview

```
1. Issue Creation → 2. Feature Branch → 3. Development → 4. Push & PR → 5. Merge & Close
```

### 1. Issue Creation & Discussion

**Before starting any work**, create a GitHub issue to:
- Document the problem or feature request
- Discuss implementation approaches
- Get alignment on the solution
- Track progress publicly

**Creating an issue:**

```bash
# Using GitHub CLI
gh issue create \
  --title "Support non-German Things 3 localizations in JXA operations" \
  --body "Description of problem and proposed solutions..."

# Or via web interface
# https://github.com/skempken/things-cli/issues/new
```

**Issue template structure:**
- **Problem**: Clear description of the issue
- **Impact**: Who is affected and how
- **Proposed Solutions**: Multiple approaches with pros/cons
- **Implementation Details**: Code locations, technical strategy
- **Acceptance Criteria**: Definition of done
- **References**: Related docs, code, issues

**Example**: See [Issue #1](https://github.com/skempken/things-cli/issues/1) for localization

### 2. Feature Branch Development

**Never commit directly to `main`**. Always work on a feature branch:

```bash
# Create and switch to feature branch
git checkout -b feature/issue-1-localization

# Or for bug fixes
git checkout -b fix/issue-2-error-handling

# Or for documentation
git checkout -b docs/update-readme
```

**Branch naming conventions:**
- `feature/<issue-number>-<short-description>` - New features
- `fix/<issue-number>-<short-description>` - Bug fixes
- `docs/<description>` - Documentation only
- `refactor/<description>` - Code refactoring
- `test/<description>` - Test additions/fixes

**Examples:**
- `feature/1-localization-support`
- `fix/3-url-encoding-spaces`
- `docs/api-examples`
- `refactor/jxa-error-handling`

### 3. Development & Commits

Work on your feature branch, making commits as you go:

```bash
# Make changes
vim things_jxa.py

# Test your changes
uv run things.py list today

# Stage and commit
git add things_jxa.py
git commit -m "feat: add locale auto-detection for JXA lists

Detect Things 3 locale by querying list names via JXA.
Falls back to English if detection fails.
Caches result in ~/.things-cli/locale.cache

Fixes #1

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Commit message format**: See [Git Workflow](#git-workflow) section below

**Important**:
- Keep commits atomic (one logical change per commit)
- Write descriptive commit messages
- Reference the issue number with `Fixes #N` or `Relates to #N`
- Test your changes before committing
- Use `--dry-run` flags where available

### 4. Push & Pull Request

When your feature is complete and tested:

```bash
# Push feature branch to remote
git push -u origin feature/1-localization-support

# Create pull request using GitHub CLI
gh pr create \
  --title "feat: Add locale auto-detection for JXA operations" \
  --body "## Summary
- Auto-detect Things 3 locale from list names
- Cache detected locale in ~/.things-cli/locale.cache
- Fallback to English if detection fails
- Backwards compatible with existing German setup

## Changes
- Modified \`things_jxa.py\` to detect locale dynamically
- Added caching mechanism for performance
- Updated tests for multiple locales
- Documented locale behavior in README

## Testing
- [x] Tested with English Things 3
- [x] Tested with German Things 3
- [x] Verified cache creation and reuse
- [x] All existing tests pass

Closes #1

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Or via web interface
open https://github.com/skempken/things-cli/compare/feature/1-localization-support
```

**Pull Request Guidelines:**
- Reference the original issue with `Closes #N` or `Fixes #N`
- Provide clear summary of changes
- Include testing checklist
- Add screenshots/examples if UI changes
- Request review if working with collaborators

### 5. Merge & Issue Closure

After review and CI passes:

```bash
# Merge via GitHub CLI (squash merge recommended for clean history)
gh pr merge --squash --delete-branch

# Or use GitHub web interface
# Merge pull request → Squash and merge → Delete branch
```

**The issue will close automatically** if your PR/commit message included:
- `Closes #N`
- `Fixes #N`
- `Resolves #N`

**Post-merge cleanup:**

```bash
# Switch back to main
git checkout main

# Pull latest changes
git pull origin main

# Delete local feature branch (if not already done)
git branch -d feature/1-localization-support
```

### Workflow Best Practices

**DO:**
- ✅ Create issue before starting work
- ✅ Use descriptive branch names with issue numbers
- ✅ Make small, focused commits
- ✅ Test thoroughly before pushing
- ✅ Reference issues in commits and PRs
- ✅ Delete branches after merging
- ✅ Keep PRs focused on one issue

**DON'T:**
- ❌ Commit directly to `main`
- ❌ Work without an issue (for non-trivial changes)
- ❌ Create PRs with unrelated changes
- ❌ Skip testing
- ❌ Leave stale branches
- ❌ Forget to reference the issue number

### Quick Reference

```bash
# Full workflow example
gh issue create --title "..." --body "..."           # 1. Create issue (#N)
git checkout -b feature/N-description                 # 2. Create branch
# ... make changes, test ...
git add . && git commit -m "feat: ... Fixes #N"      # 3. Commit
git push -u origin feature/N-description             # 4. Push
gh pr create --title "..." --body "... Closes #N"    # 5. Create PR
gh pr merge --squash --delete-branch                  # 6. Merge & close
git checkout main && git pull                         # 7. Update main
```

### Emergency Hotfixes

For critical bugs in production:

```bash
# Create hotfix branch from main
git checkout -b hotfix/critical-bug main

# Fix, test, commit
git add . && git commit -m "fix: critical bug..."

# Push and create PR immediately
git push -u origin hotfix/critical-bug
gh pr create --title "HOTFIX: ..." --body "..."

# Fast-track review and merge
gh pr merge --squash --delete-branch
```

## Git Workflow

### Commit Messages

Follow conventional commits with Claude Code footer:

```
<type>: <description>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Important Commits

- `ad48840` - Initial commit
- `103b695` - Add MIT License
- `dc0c584` - Add read operations via JXA
- `180afe1` - Fix isinstance bug in build_url

## Future Enhancement Ideas

### Completed Features
- ✅ URL Scheme write operations (add, update, show, search, json)
- ✅ JXA read operations (list, query, filter)
- ✅ JSON import/export
- ✅ Dry-run mode
- ✅ Rich terminal output

### Potential Future Features
- [ ] `--format table` for Rich table output (currently only JSON)
- [ ] `--format plain` for simple text lists
- [ ] Advanced filters: `--overdue`, `--created-after`, `--completed-today`
- [ ] Sorting: `--sort-by due_date`
- [ ] Pagination: `--limit 10`, `--offset 20`
- [ ] Batch update operations (update multiple tasks at once)
- [ ] Configuration file support (`~/.things-cli/config.yaml`)
- [ ] Shell completion (bash, zsh, fish)
- [ ] Task templates (YAML/TOML files for common task structures)

### Not Possible (API Limitations)
- ❌ Delete operations (Things URL Scheme doesn't support it)
- ❌ Bulk operations without rate limits (250 items/10s max)
- ❌ Real-time sync monitoring (no webhook/event API)
- ❌ Cross-platform support (Things is macOS/iOS only)

## Dependencies

```toml
[project.dependencies]
typer = ">=0.12.0"  # CLI framework
rich = ">=13.0.0"   # Terminal formatting
```

Both are well-maintained and stable. No known compatibility issues.

## Security Considerations

1. **Auth Token**: Never commit `THINGS_TOKEN` to git
   - Added to `.gitignore` as `.env`
   - Stored in environment variable only

2. **Task IDs**: UUIDs are not secret but are user-specific
   - Safe to show in examples/docs
   - But don't expose personal task content

3. **JXA Scripts**: Executed with user privileges
   - No elevated permissions needed
   - Scripts are inline, not from external files

## Debugging Tips

### URL Scheme Issues

```bash
# Use dry-run to see generated URL
things add --title "Test" --dry-run

# Check URL encoding
python3 -c "from urllib.parse import quote; print(quote('test string'))"
```

### JXA Issues

```bash
# Test JXA directly
osascript -l JavaScript -e 'Application("Things3").name()'

# Check Things is running
ps aux | grep Things

# Test Python import
python3 -c "import things_jxa; print(things_jxa.get_all_tags())"
```

### Import Errors

```bash
# Validate JSON
python3 -m json.tool < file.json

# Check for non-existent tags
things list tags | grep "tag-name"
```

## Performance Notes

- **JXA calls**: ~100-500ms per query (depends on data size)
- **URL Scheme**: Near-instant (opens URL handler)
- **Large lists**: JXA can take 1-2 seconds for 100+ items
- **Batch imports**: Limited to 250 items, takes ~1 second

## Testing with Real Data

The project was tested with:
- 4 tasks in Today
- 65 tasks in Upcoming
- 74 tags (including priority, time, location, person tags)
- 8 areas
- 25 projects

All operations worked correctly with German-localized Things 3.

## Support & Resources

- **Things URL Scheme Docs**: https://culturedcode.com/things/support/articles/2803573/
- **JXA Guide**: Search Apple's official JXA docs
- **uv Documentation**: https://github.com/astral-sh/uv
- **GitHub Issues**: https://github.com/skempken/things-cli/issues

## Last Updated

- Date: 2025-10-30
- Last Commit: 180afe1
- Things CLI Version: 0.1.0
- Tested with: Things 3 on macOS (German localization)
- Documentation: Added comprehensive Development Workflow section
