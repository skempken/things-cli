# Things CLI Helper

A comprehensive guide for using the Things CLI - a command-line interface for Things 3.

## Quick Start

### Essential Setup

```bash
# For write operations (update, import), set your auth token:
export THINGS_TOKEN="your-token-here"

# Get token from: Things → Settings → General → Enable Things URLs → Manage
```

### Top 5 Most Used Commands

```bash
# 1. Add a task
things add --title "Complete presentation" --when today --tags work

# 2. View today's tasks
things list today

# 3. Filter tasks by tag
things list --tag urgent

# 4. Update a task (requires THINGS_TOKEN)
things update --id TASK-ID --add-tags "2h" --append-notes "Additional info"

# 5. Navigate to a view
things show --id today
```

---

## Command Categories

### Creating Tasks & Projects

#### Add a Task

```bash
# Simple task
things add --title "Buy groceries"

# Task with full details
things add \
  --title "Prepare Q4 Report" \
  --notes "Include metrics and projections" \
  --when today \
  --deadline 2024-12-15 \
  --tags "work,important" \
  --checklist "Gather data,Write draft,Review with team"

# Task for specific time
things add --title "Meeting" --when evening --tags meeting

# Task in project
things add --title "Design mockups" --list "Website Redesign"
```

#### Add a Project

```bash
# Simple project
things add-project --title "Website Redesign"

# Project with tasks
things add-project \
  --title "Blog Migration" \
  --area "Personal" \
  --todos "Export posts,Setup platform,Import content,Test links" \
  --deadline 2024-12-31 \
  --reveal

# Project with notes
things add-project \
  --title "Product Launch" \
  --notes "Q1 2025 target launch date" \
  --area "Work" \
  --tags "high-priority"
```

### Reading & Querying

#### List Tasks by View

```bash
# Built-in views
things list today      # Today's tasks
things list inbox      # Inbox items
things list upcoming   # Upcoming tasks
things list anytime    # Anytime tasks
things list someday    # Someday list
things list logbook    # Completed tasks
things list tomorrow   # Tomorrow's tasks
```

#### Filter Tasks

```bash
# By tag
things list --tag work
things list --tag "1h"

# By area
things list --area "Personal"

# By project
things list --project "Website Redesign"
```

#### Query Metadata

```bash
# List all tags
things list tags

# List all areas (with task counts)
things list areas

# List all projects (with details)
things list projects
```

#### Process JSON Output

```bash
# Count tasks
things list today | jq 'length'

# Get task names only
things list today | jq '.[].name'

# Filter by tag in output
things list today | jq '.[] | select(.tagNames | contains("urgent"))'

# Export to CSV
things list today | jq -r '.[] | [.name, .status, .tagNames] | @csv'

# Extract task IDs
things list --tag work | jq -r '.[].id'
```

### Updating Tasks & Projects

**Note**: All update commands require `THINGS_TOKEN` environment variable.

#### Update a Task

```bash
# Change title
things update --id TASK-ID --title "New title"

# Add tags (without replacing existing)
things update --id TASK-ID --add-tags "urgent,2h"

# Replace all tags
things update --id TASK-ID --tags "work,project-a"

# Append notes
things update --id TASK-ID --append-notes "Follow-up needed"

# Prepend notes
things update --id TASK-ID --prepend-notes "URGENT: "

# Change deadline
things update --id TASK-ID --deadline 2024-12-20

# Clear deadline
things update --id TASK-ID --deadline ""

# Mark as completed
things update --id TASK-ID --completed

# Move to project
things update --id TASK-ID --list "Project Name"

# Duplicate and update
things update --id TASK-ID --duplicate --title "Copy of task"
```

#### Update a Project

```bash
# Change project title
things update-project --id PROJECT-ID --title "New Name"

# Move to different area
things update-project --id PROJECT-ID --area "Work"

# Add tags to project
things update-project --id PROJECT-ID --add-tags "active,q4"
```

#### Get Task IDs

```bash
# Method 1: From Things app
# Mac: Control-click item → Share → Copy Link
# iOS: Open item → Share → Copy Link
# Extract UUID from: things:///show?id=<UUID>

# Method 2: Via CLI
things list today | jq -r '.[] | "\(.name) → \(.id)"'
```

### Navigation & Search

```bash
# Open Today view
things show --id today

# Open Inbox
things show --id inbox

# Built-in list IDs
things show --id upcoming
things show --id anytime
things show --id someday
things show --id logbook

# Quick find by name
things show --query "Project Name"

# Filter by tags
things show --id today --filter work,urgent

# Search interface
things search

# Search with pre-filled query
things search --query "meeting notes"
```

### Batch Operations

#### JSON Import/Export

```bash
# Export template
things export task-template.json --type task
things export project-template.json --type project
things export batch-template.json --type batch

# Edit template, then import
things import tasks.json

# Direct JSON command
things json-command --file batch-operations.json --reveal
```

#### JSON Structure

```json
[
  {
    "type": "to-do",
    "attributes": {
      "title": "Task title",
      "notes": "Task notes",
      "when": "today",
      "tags": ["work", "urgent"],
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
        {"type": "heading", "attributes": {"title": "Section"}},
        {"type": "to-do", "attributes": {"title": "Task in section"}}
      ]
    }
  }
]
```

**Important**: Tags in JSON must already exist in Things! Use `things add --tags new-tag` first.

---

## Common Workflows

### Daily Planning Routine

```bash
# 1. Check today's workload
things list today | jq 'length'
echo "You have $(things list today | jq 'length') tasks today"

# 2. Review tasks
things list today | jq -r '.[] | "- \(.name) [\(.tagNames)]"'

# 3. Add time estimates to tasks without them
things list today | jq -r '.[] | select(.tagNames | contains("h") | not) | .id' | while read id; do
  echo "Task ID: $id needs time estimate"
  # Manually decide and update:
  # things update --id "$id" --add-tags "1h"
done

# 4. Open Today view
things show --id today

# 5. Add new priority task
things add --title "New urgent task" --when today --tags urgent,work
```

### Project Setup Workflow

```bash
# 1. Create project with initial tasks
things add-project \
  --title "Mobile App Development" \
  --area "Work" \
  --todos "Setup dev environment,Design mockups,Implement auth,Write tests" \
  --deadline 2024-12-31 \
  --tags "q4,development" \
  --reveal

# 2. List project to get ID
things list projects | jq '.[] | select(.name == "Mobile App Development") | .id'

# 3. Add more detailed tasks to project
PROJECT_ID="<from-step-2>"
things add --title "Setup CI/CD pipeline" --list-id "$PROJECT_ID" --tags "devops,2h"
```

### Batch Task Import

```bash
# 1. Ensure tags exist
things list tags | grep -E "(urgent|work|personal)"

# 2. Create missing tags
things add --title "Dummy task for tag creation" --tags "urgent" --completed
things add --title "Dummy task for tag creation" --tags "work" --completed

# 3. Export template
things export import-template.json --type batch

# 4. Edit template with actual tasks
# 5. Import
things import import-template.json --reveal
```

### Weekly Review Workflow

```bash
# 1. Check completed tasks
things list logbook | jq 'length'
echo "Completed: $(things list logbook | jq 'length') tasks"

# 2. Review upcoming tasks
things list upcoming | jq -r '.[] | "[\(.dueDate // "No deadline")] \(.name)"'

# 3. Check projects
things list projects | jq -r '.[] | "\(.name): \(.taskCount) tasks"'

# 4. Review areas
things list areas | jq -r '.[] | "\(.name): \(.taskCount) tasks"'
```

### Tag Management Workflow

```bash
# 1. List all tags
things list tags > all-tags.json

# 2. Find tasks with specific tag
things list --tag "needs-review"

# 3. Bulk tag update (example: add time estimates)
things list today | jq -r '.[] | select(.tagNames | contains("h") | not) | .id' > tasks-need-time.txt

while read task_id; do
  things update --id "$task_id" --add-tags "1h" --dry-run
done < tasks-need-time.txt

# Review output, then run without --dry-run
```

---

## Parameters Reference

### Date Formats

```bash
# Predefined options (--when parameter)
--when today
--when tomorrow
--when evening
--when anytime
--when someday

# Custom dates (--when-date or --deadline)
--when-date 2024-12-25
--deadline 2024-12-31

# Natural language (for URL scheme)
"in 3 days"
"next monday"
"tomorrow at 14:00"
```

### Tag Syntax

```bash
# Single tag
--tags work

# Multiple tags (comma-separated, no spaces)
--tags "work,urgent,project-a"

# Add tags without replacing
--add-tags "2h,high-priority"
```

### Checklist Items

```bash
# Comma-separated
--checklist "Step 1,Step 2,Step 3"

# With special characters
--checklist "Buy milk,Pick up keys,Send email to @john"
```

### Special Flags

```bash
--dry-run           # Preview URL without executing
--reveal            # Show item after creation/update
--completed         # Mark as completed
--canceled          # Mark as canceled
--duplicate         # Create copy before updating (update only)

# Notes operations
--notes             # Replace notes
--append-notes      # Add to end of notes
--prepend-notes     # Add to beginning of notes
```

### List IDs (Built-in)

```bash
inbox               # Inbox
today               # Today
tomorrow            # Tomorrow
anytime             # Anytime
upcoming            # Upcoming
someday             # Someday
logbook             # Completed tasks
deadlines           # Deadlines view
repeating           # Repeating tasks
all-projects        # All Projects
logged-projects     # Logged Projects
```

---

## Troubleshooting

### "THINGS_TOKEN environment variable required"

**Cause**: Update/modify operations need authentication.

**Solution**:
```bash
# Get token from Things
# Mac: Things → Settings → General → Enable Things URLs → Manage
# iOS: Settings → General → Things URLs

# Export in shell
export THINGS_TOKEN="your-token-here"

# Or add to ~/.zshrc or ~/.bashrc for persistence
echo 'export THINGS_TOKEN="your-token-here"' >> ~/.zshrc
source ~/.zshrc
```

### "Could not connect to Things 3"

**Cause**: Things app is not running or JXA can't access it.

**Solution**:
```bash
# 1. Make sure Things is installed
ls /Applications/Things3.app

# 2. Start Things
open -a Things3

# 3. Test connection
osascript -l JavaScript -e 'Application("Things3").name()'
# Should output: Things
```

### "List not found" or Empty Results

**Cause**: Things is localized, list names might be in German.

**Solution**: The CLI automatically maps English → German:
- today → Heute
- inbox → Eingang
- tomorrow → Morgen
- etc.

If still failing:
```bash
# Check actual list names
osascript -l JavaScript -e '
const things = Application("Things3");
const lists = things.lists();
for (let i = 0; i < lists.length; i++) {
    console.log(lists[i].name());
}
'
```

### JSON Import Fails - "Tag not found"

**Cause**: Tags must exist in Things before importing JSON.

**Solution**:
```bash
# 1. Check existing tags
things list tags | grep "tag-name"

# 2. Create missing tags first
things add --title "Create tag" --tags "missing-tag" --completed

# 3. Then import
things import tasks.json
```

### Rate Limiting / "Too many requests"

**Cause**: Things URL scheme limits to 250 items per 10 seconds.

**Solution**:
```bash
# Split large imports into batches
split -l 200 large-import.json batch-

# Import with delays
for file in batch-*; do
  things import "$file"
  echo "Waiting 10 seconds..."
  sleep 10
done
```

### URL Shows + Instead of Spaces

**Cause**: Fixed in current version (commit 180afe1).

**Solution**: Update to latest version:
```bash
git pull
uv pip install -e .
```

### "Invalid JSON" Errors

**Cause**: JSON syntax errors or encoding issues.

**Solution**:
```bash
# Validate JSON
python3 -m json.tool < your-file.json

# Check for common issues
# - Trailing commas
# - Unescaped quotes
# - Missing brackets
```

---

## Power User Tips

### Shell Aliases

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias t="things"
alias ta="things add"
alias tl="things list"
alias tu="things update"
alias ts="things show"

# Smart aliases
alias tt="things list today"
alias tw="things list --tag work"
alias tp="things list projects"
```

### jq Master Commands

```bash
# Task count by tag
things list today | jq 'group_by(.tagNames) | map({tag: .[0].tagNames, count: length})'

# Tasks without deadlines
things list upcoming | jq '.[] | select(.dueDate == null) | .name'

# Overdue tasks (simplistic check)
things list today | jq '.[] | select(.dueDate != null)'

# Export for reporting
things list logbook | jq -r '.[] | [.name, .completionDate, .tagNames] | @csv' > completed.csv

# Task grouping by area (from project data)
things list projects | jq 'group_by(.area) | map({area: .[0].area, projects: map(.name)})'
```

### Advanced Workflows

```bash
# Bulk reschedule tasks
things list anytime | jq -r '.[].id' | while read id; do
  things update --id "$id" --when tomorrow
done

# Clone project structure
PROJECT_ID="source-project-id"
things list --project "Source Project" | jq -r '.[] | .name' | while read task_name; do
  things add --title "$task_name" --list "New Project"
done

# Archive completed tasks to file
things list logbook | jq '.' > "archive-$(date +%Y-%m).json"
```

### Integration with Other Tools

```bash
# Export to Markdown
things list today | jq -r '.[] | "- [ ] \(.name)"' > today.md

# Create tasks from text file
while IFS= read -r line; do
  things add --title "$line" --when today
done < tasks.txt

# Sync with external system
curl https://api.example.com/tasks | jq '.[]' | while read -r task; do
  title=$(echo "$task" | jq -r '.title')
  things add --title "$title" --when today
done
```

### Performance Optimization

```bash
# Cache frequently used queries
things list tags > ~/.things-cli-cache/tags.json
things list areas > ~/.things-cli-cache/areas.json

# Batch operations instead of loops
# Bad:
for id in $(things list today | jq -r '.[].id'); do
  things update --id "$id" --add-tags "urgent"
done

# Good:
things list today | jq -r '.[].id' > ids.txt
# Review all IDs first, then:
xargs -I {} things update --id {} --add-tags "urgent" < ids.txt
```

---

### Known Limitations

**Cannot do via CLI:**
- Delete tasks/projects (URL scheme doesn't support it)
- Get x-callback-url responses (would require more complex setup)
- Real-time monitoring (no webhook/event API)
- Cross-platform (Things is macOS/iOS only)

**Rate Limits:**
- 250 items per 10 seconds (URL scheme)
- No limit on read operations (JXA)

**Tag Management:**
- Tags can only be created via `add` or `add-project`
- JSON import requires tags to exist
- Use `things add --tags new-tag --completed` to create tags

---

## Quick Reference Card

### Create
```bash
things add --title "..." --when today --tags "..."
things add-project --title "..." --todos "..." --area "..."
```

### Read
```bash
things list today
things list --tag work
things list tags/areas/projects
```

### Update
```bash
things update --id ID --add-tags "..."
things update --id ID --append-notes "..."
```

### Navigate
```bash
things show --id today
things search --query "..."
```

### Batch
```bash
things export template.json --type task
things import tasks.json
```

### Test
```bash
things <command> --dry-run
```