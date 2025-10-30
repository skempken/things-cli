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
