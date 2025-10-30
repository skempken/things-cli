# Things CLI

A powerful command-line interface for [Things 3](https://culturedcode.com/things/) using the Things URL scheme and JXA (JavaScript for Automation). Manage your tasks, projects, and to-dos directly from the terminal with both read and write capabilities.

## Features

- **Complete URL Scheme Support**: All Things URL commands (add, update, show, search, json)
- **Read Operations via JXA**: Query tasks, projects, areas, and tags directly from the terminal
- **Intuitive Subcommands**: Git-like CLI structure (`things add`, `things list`, etc.)
- **Batch Operations**: Import/export tasks and projects via JSON
- **Rich Output**: Beautiful terminal output with colors and formatting
- **Dry-run Mode**: Preview URLs before execution
- **Template System**: Export JSON templates for common workflows
- **JSON Output**: Machine-readable output for integration with other tools

## Requirements

- macOS (Things 3 is macOS/iOS only)
- Python 3.10+
- Things 3 app installed
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

1. Clone this repository:
```bash
git clone https://github.com/skempken/things-cli.git
cd things-cli
```

2. Install with uv:
```bash
uv pip install -e .
```

This installs the package in development mode. To use the `things` command, you have two options:
- **Recommended**: Use `uv run things` (automatically activates the virtual environment)
- **Alternative**: Activate the virtual environment with `source .venv/bin/activate`, then use `things`

All examples below use `things` for brevity, but assume you're using `uv run things` or have activated the virtual environment.

3. (Optional) Set up your auth token for update/modify operations:
```bash
export THINGS_TOKEN="your-token-here"
```

To get your auth token:
- **Mac**: Things → Settings → General → Enable Things URLs → Manage
- **iOS**: Settings → General → Things URLs

You can add this to your `~/.zshrc` or `~/.bashrc` for persistence.

## Usage

### Basic Commands

#### Add a Task

```bash
# Simple task
things add --title "Buy groceries"

# Task with details
things add \
  --title "Prepare presentation" \
  --notes "Include Q4 metrics and projections" \
  --when today \
  --tags work,important \
  --deadline 2024-03-15

# Task with checklist
things add \
  --title "Pack for trip" \
  --checklist "Passport,Tickets,Camera" \
  --when tomorrow
```

#### Create a Project

```bash
# Simple project
things add-project --title "Website Redesign"

# Project with tasks
things add-project \
  --title "Blog Migration" \
  --area Personal \
  --todos "Export old posts,Set up new platform,Import content,Test links" \
  --deadline 2024-04-01 \
  --reveal
```

#### Update Tasks

**Note**: Update commands require the `THINGS_TOKEN` environment variable.

```bash
# Update task title
things update --id TASK-UUID --title "New title"

# Add notes to existing task
things update \
  --id TASK-UUID \
  --append-notes "Additional information"

# Change deadline
things update --id TASK-UUID --deadline 2024-03-20

# Add tags
things update --id TASK-UUID --add-tags urgent,client

# Mark as completed
things update --id TASK-UUID --completed
```

To get a task ID:
- **Mac**: Control-click item → Share → Copy Link
- **iOS**: Open item → Tap → Share → Copy Link
- Extract the UUID from the copied link

#### Navigate Views

```bash
# Show Today list
things show --id today

# Show Inbox
things show --id inbox

# Show specific project (by ID)
things show --custom-id PROJECT-UUID

# Quick find by name
things show --query "Website Project"

# Filter by tags
things show --id today --filter work,urgent
```

Available built-in list IDs:
- `inbox`, `today`, `tomorrow`, `anytime`, `upcoming`, `someday`
- `logbook`, `deadlines`, `repeating`
- `all-projects`, `logged-projects`

#### Search

```bash
# Open search interface
things search

# Search with pre-filled query
things search --query "meeting notes"
```

### Read Operations (via JXA)

The CLI supports reading data from Things 3 using JavaScript for Automation (JXA). This allows you to query tasks, projects, and metadata directly from the terminal.

**Note**: Read operations require Things 3 to be running and are only available on macOS.

#### List Tasks by View

```bash
# Show today's tasks
things list today

# Show inbox
things list inbox

# Show upcoming tasks
things list upcoming

# Show anytime tasks
things list anytime

# Show someday tasks
things list someday

# Show completed tasks (logbook)
things list logbook
```

#### Filter Tasks

```bash
# Filter by tag
things list --tag work
things list --tag "1h"

# Filter by area
things list --area "Personal"

# Filter by project
things list --project "Website Redesign"
```

#### Locale Support

Things CLI supports multiple languages through the `--locale` parameter:

```bash
# Auto-detect locale from Things 3 (default)
things list today

# Use German locale (fast, no auto-detection)
things list today --locale de

# Use English locale (fast, no auto-detection)
things list today --locale en
```

**Supported locales:**
- `de` - German (Deutsch)
- `en` - English
- `auto` - Auto-detect (default)

**Note:** The `--locale` parameter only affects built-in list queries (`today`, `inbox`, etc.). When specifying a locale explicitly (e.g., `--locale de`), the CLI uses hardcoded mappings for better performance. When omitted or set to `auto`, the CLI automatically detects your Things 3 language settings.

#### Query Metadata

```bash
# List all tags
things list tags

# List all areas (with task counts)
things list areas

# List all projects (with details)
things list projects
```

#### Output Format

All `list` commands output JSON for easy parsing and integration with other tools:

```json
[
  {
    "id": "ABC123DEF456",
    "name": "Task title",
    "status": "open",
    "notes": "Task notes",
    "tagNames": "tag1, tag2",
    "dueDate": "Mon Nov 15 2025...",
    "creationDate": "Thu Oct 30 2025..."
  }
]
```

**Processing with jq:**
```bash
# Count today's tasks
things list today | jq 'length'

# Get task names only
things list today | jq '.[].name'

# Filter for tasks with specific tag
things list today | jq '.[] | select(.tagNames | contains("urgent"))'

# Export to CSV
things list today | jq -r '.[] | [.name, .status, .tagNames] | @csv'
```

### Advanced: JSON Operations

#### Import Tasks from JSON

```bash
# Import from file
things import tasks.json

# Using json command directly
things json-command --file batch-tasks.json --reveal
```

#### Export Templates

```bash
# Export task template
things export task-template.json --type task

# Export project template
things export project-template.json --type project

# Export batch template
things export batch-template.json --type batch
```

Example JSON structure:

```json
[
  {
    "type": "to-do",
    "attributes": {
      "title": "Task title",
      "notes": "Task notes",
      "when": "today",
      "tags": ["work", "important"],
      "checklist-items": [
        {"type": "checklist-item", "attributes": {"title": "Subtask 1"}},
        {"type": "checklist-item", "attributes": {"title": "Subtask 2"}}
      ]
    }
  },
  {
    "type": "project",
    "attributes": {
      "title": "Project title",
      "area": "Work",
      "items": [
        {"type": "to-do", "attributes": {"title": "First task"}},
        {"type": "heading", "attributes": {"title": "Section 1"}},
        {"type": "to-do", "attributes": {"title": "Task in section"}}
      ]
    }
  }
]
```

**Important JSON Import Limitations:**
- **Tags must already exist in Things**: The JSON import cannot create new tags. Use the `add` or `add-project` commands to create tasks with new tags, which will automatically create them.
- **Tags format**: Use an array format: `"tags": ["tag1", "tag2"]` (not a comma-separated string)
- **Rate limiting**: Maximum 250 items per import
- **Auth token required**: Set `THINGS_TOKEN` environment variable for JSON imports

### Utility Commands

#### Dry-run Mode

Preview the URL that would be executed without actually running it:

```bash
things add --title "Test task" --dry-run
```

#### Check Version

```bash
things version
```

## Common Workflows

### Daily Planning

```bash
# Review today's tasks
things show --id today

# Add tasks for today
things add --title "Morning standup" --when today --tags work
things add --title "Review PRs" --when today --tags dev
things add --title "Gym" --when evening --tags personal
```

### Project Setup

```bash
# Create project with structure
things add-project \
  --title "Mobile App Development" \
  --area Work \
  --todos "Setup environment,Design UI mockups,Implement auth,Write tests" \
  --deadline 2024-06-01 \
  --reveal
```

### Batch Import

Create a `weekly-tasks.json`:
```json
[
  {"type": "to-do", "attributes": {"title": "Team meeting", "when": "monday"}},
  {"type": "to-do", "attributes": {"title": "Code review", "when": "tuesday"}},
  {"type": "to-do", "attributes": {"title": "Deploy to staging", "when": "thursday"}}
]
```

Then import:
```bash
things import weekly-tasks.json
```

### Task Migration

```bash
# Duplicate and update task
things update \
  --id OLD-TASK-UUID \
  --duplicate \
  --title "Updated task title" \
  --when tomorrow
```

## Command Reference

### Global Options

- `--dry-run`: Preview URL without executing
- `--reveal` / `-r`: Show item after creation/update (where applicable)

### Add Command Options

```
--title, -t          Task title (required)
--notes, -n          Task notes
--when, -w           Schedule: today, tomorrow, evening, anytime, someday
--when-date          Custom date (yyyy-mm-dd)
--deadline, -d       Deadline date
--tags               Comma-separated tags
--checklist, -c      Comma-separated checklist items
--list, -l           Project or area name
--list-id            Project or area ID (UUID)
--heading            Heading name within project
--heading-id         Heading ID (UUID)
--completed          Mark as completed
--canceled           Mark as canceled
--creation-date      Creation date (ISO8601)
--completion-date    Completion date (ISO8601)
```

### Update Command Options

All options from `add`, plus:

```
--id                 Task ID (required, UUID)
--prepend-notes      Prepend text to notes
--append-notes       Append text to notes
--add-tags           Add tags (without replacing)
--prepend-checklist  Prepend checklist items
--append-checklist   Append checklist items
--duplicate          Duplicate before updating
```

**Note**: Update requires `THINGS_TOKEN` environment variable.

### Show Command Options

```
--id                 Built-in list ID (today, inbox, etc.)
--custom-id          Custom item/project/area/tag ID
--query, -q          Search by name (quick find)
--filter, -f         Filter by tags (comma-separated)
```

## Tips & Tricks

1. **Get Task IDs**: Control-click (Mac) or tap (iOS) any item → Share → Copy Link to get its UUID

2. **Clear Fields**: Use empty string to clear fields in update commands:
   ```bash
   things update --id TASK-UUID --deadline ""
   ```

3. **Rate Limiting**: Things limits to 250 items per 10 seconds for batch operations

4. **Date Formats**: Things accepts various date formats:
   - `yyyy-mm-dd` (e.g., `2024-03-15`)
   - Natural language (e.g., `today`, `tomorrow`, `in 3 days`)
   - With time: `yyyy-mm-dd@HH:MM` or ISO8601

5. **Shell Aliases**: Add to your `.zshrc`:
   ```bash
   alias t="things"
   alias ta="things add"
   alias ts="things show"
   ```

## Troubleshooting

### "THINGS_TOKEN environment variable required"

Update commands need authentication. Get your token:
1. Open Things → Settings → General
2. Enable "Things URLs"
3. Click "Manage" to view your token
4. Export it: `export THINGS_TOKEN="your-token"`

### "Error: 'open' command not found"

This CLI uses macOS's `open` command to trigger Things URLs. Ensure you're running on macOS.

### "Command sent to Things" but nothing happens

1. Ensure Things 3 is installed and running
2. Check that Things URL scheme is enabled in Things settings
3. Try the dry-run mode to see the generated URL

## Development

### Project Structure

```
things-cli/
├── things.py         # Main CLI with Typer subcommands
├── things_jxa.py     # JXA Helper Module for read operations
├── pyproject.toml    # uv project configuration
├── README.md         # User documentation
├── CLAUDE.md         # Project knowledge for AI assistants
├── LICENSE           # MIT License
├── .gitignore        # Git ignore rules
├── .env.example      # Environment variable template
└── uv.lock           # Dependency lock file
```

### Running from Source

**Recommended approach:**
```bash
# Install in development mode
uv pip install -e .

# Run with uv (automatically manages the virtual environment)
uv run things add --title "Test"
uv run things list today
```

**Alternative: Activate virtual environment**
```bash
# Install in development mode
uv pip install -e .

# Activate the virtual environment
source .venv/bin/activate

# Now use the command directly (no uv run needed)
things add --title "Test"
things list today

# Deactivate when done
deactivate
```

**Without installation:**
```bash
# Run the script directly (no installation needed)
uv run things.py add --title "Test"
uv run things.py list today
```

All examples in this README use `things` for brevity, but you should prefix with `uv run` or activate the virtual environment first.

### Contributing

Contributions are welcome! This is a personal project, but feel free to submit issues or pull requests.

## Resources

- [Things URL Scheme Documentation](https://culturedcode.com/things/support/articles/2803573/)
- [Things 3 Official Website](https://culturedcode.com/things/)
- [uv Documentation](https://github.com/astral-sh/uv)

## License

MIT License - feel free to use and modify as needed.

## Author

Sebastian Kempken
