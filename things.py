#!/usr/bin/env python3
"""
Things CLI - Command-line interface for Things 3 using the Things URL scheme
"""

import os
import sys
import json
import subprocess
from urllib.parse import quote, urlencode
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

app = typer.Typer(
    help="Command-line interface for Things 3",
    no_args_is_help=True,
)
console = Console()


# ============================================================================
# Enums for parameter validation
# ============================================================================

class When(str, Enum):
    """Valid values for 'when' parameter"""
    today = "today"
    tomorrow = "tomorrow"
    evening = "evening"
    anytime = "anytime"
    someday = "someday"


class BuiltInList(str, Enum):
    """Built-in list IDs for show command"""
    inbox = "inbox"
    today = "today"
    anytime = "anytime"
    upcoming = "upcoming"
    someday = "someday"
    logbook = "logbook"
    tomorrow = "tomorrow"
    deadlines = "deadlines"
    repeating = "repeating"
    all_projects = "all-projects"
    logged_projects = "logged-projects"


# ============================================================================
# Helper functions
# ============================================================================

def get_auth_token() -> Optional[str]:
    """Get auth token from environment variable"""
    token = os.environ.get("THINGS_TOKEN")
    if not token:
        console.print("[yellow]Warning: THINGS_TOKEN environment variable not set[/yellow]")
        console.print("[yellow]Commands requiring authentication will fail[/yellow]")
    return token


def build_url(command: str, params: Dict[str, Any]) -> str:
    """
    Build a Things URL with proper encoding

    Args:
        command: The Things command (add, update, show, etc.)
        params: Dictionary of parameters

    Returns:
        Properly encoded Things URL
    """
    # Filter out None values
    params = {k: v for k, v in params.items() if v is not None}

    # Handle special encoding for certain parameters
    encoded_params = {}
    for key, value in params.items():
        if isinstance(value, bool):
            encoded_params[key] = str(value).lower()
        elif isinstance(value, list):
            # Join lists with newlines (encoded as %0a)
            encoded_params[key] = "\n".join(str(v) for v in value)
        else:
            encoded_params[key] = str(value)

    # Build URL
    if encoded_params:
        # Use quote_via to ensure spaces are encoded as %20, not +
        query_string = urlencode(encoded_params, safe='', quote_via=quote)
        url = f"things:///{command}?{query_string}"
    else:
        url = f"things:///{command}"

    return url


def execute_url(url: str, dry_run: bool = False) -> None:
    """
    Execute a Things URL by opening it

    Args:
        url: The Things URL to execute
        dry_run: If True, just print the URL without executing
    """
    if dry_run:
        console.print(f"[cyan]Would execute:[/cyan] {url}")
        return

    try:
        # Use 'open' command on macOS to open the URL
        subprocess.run(["open", url], check=True)
        console.print("[green]✓ Command sent to Things[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error executing command: {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[red]Error: 'open' command not found. Are you on macOS?[/red]")
        raise typer.Exit(1)


def parse_date(date_str: str) -> str:
    """
    Parse and validate date string
    Accepts: yyyy-mm-dd, natural language, or datetime formats
    """
    # For now, just return as-is. Things accepts various formats.
    # Could add validation here if needed
    return date_str


def split_items(items: Optional[str]) -> Optional[List[str]]:
    """Split comma or newline separated items into a list"""
    if not items:
        return None
    # Split by newlines or commas
    items_list = [item.strip() for item in items.replace(',', '\n').split('\n')]
    return [item for item in items_list if item]  # Filter empty strings


# ============================================================================
# Main Commands
# ============================================================================

@app.command()
def add(
    title: str = typer.Option(..., "--title", "-t", help="Title of the task"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes (max 10,000 chars)"),
    when: Optional[When] = typer.Option(None, "--when", "-w", help="When to schedule the task"),
    when_date: Optional[str] = typer.Option(None, "--when-date", help="Custom date (yyyy-mm-dd)"),
    deadline: Optional[str] = typer.Option(None, "--deadline", "-d", help="Deadline date"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    checklist: Optional[str] = typer.Option(None, "--checklist", "-c", help="Comma-separated checklist items"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Project or area name"),
    list_id: Optional[str] = typer.Option(None, "--list-id", help="Project or area ID"),
    heading: Optional[str] = typer.Option(None, "--heading", help="Heading name within project"),
    heading_id: Optional[str] = typer.Option(None, "--heading-id", help="Heading ID within project"),
    completed: bool = typer.Option(False, "--completed", help="Mark as completed"),
    canceled: bool = typer.Option(False, "--canceled", help="Mark as canceled"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show the task after creation"),
    creation_date: Optional[str] = typer.Option(None, "--creation-date", help="Creation date (ISO8601)"),
    completion_date: Optional[str] = typer.Option(None, "--completion-date", help="Completion date (ISO8601)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Create a new task in Things"""

    params = {
        "title": title,
        "notes": notes,
        "when": when.value if when else when_date,
        "deadline": deadline,
        "tags": tags,
        "checklist-items": "\n".join(split_items(checklist)) if checklist else None,
        "list": list_name,
        "list-id": list_id,
        "heading": heading,
        "heading-id": heading_id,
        "completed": completed if completed else None,
        "canceled": canceled if canceled else None,
        "reveal": reveal if reveal else None,
        "creation-date": creation_date,
        "completion-date": completion_date,
    }

    url = build_url("add", params)
    execute_url(url, dry_run)


@app.command("add-project")
def add_project(
    title: str = typer.Option(..., "--title", "-t", help="Title of the project"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes"),
    when: Optional[When] = typer.Option(None, "--when", "-w", help="When to schedule"),
    when_date: Optional[str] = typer.Option(None, "--when-date", help="Custom date (yyyy-mm-dd)"),
    deadline: Optional[str] = typer.Option(None, "--deadline", "-d", help="Deadline date"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Area name"),
    area_id: Optional[str] = typer.Option(None, "--area-id", help="Area ID"),
    todos: Optional[str] = typer.Option(None, "--todos", help="Comma-separated todo items"),
    completed: bool = typer.Option(False, "--completed", help="Mark as completed"),
    canceled: bool = typer.Option(False, "--canceled", help="Mark as canceled"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show the project after creation"),
    creation_date: Optional[str] = typer.Option(None, "--creation-date", help="Creation date (ISO8601)"),
    completion_date: Optional[str] = typer.Option(None, "--completion-date", help="Completion date (ISO8601)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Create a new project in Things"""

    params = {
        "title": title,
        "notes": notes,
        "when": when.value if when else when_date,
        "deadline": deadline,
        "tags": tags,
        "area": area,
        "area-id": area_id,
        "to-dos": "\n".join(split_items(todos)) if todos else None,
        "completed": completed if completed else None,
        "canceled": canceled if canceled else None,
        "reveal": reveal if reveal else None,
        "creation-date": creation_date,
        "completion-date": completion_date,
    }

    url = build_url("add-project", params)
    execute_url(url, dry_run)


@app.command()
def update(
    task_id: str = typer.Option(..., "--id", help="Task ID (UUID)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Replace notes"),
    prepend_notes: Optional[str] = typer.Option(None, "--prepend-notes", help="Prepend to notes"),
    append_notes: Optional[str] = typer.Option(None, "--append-notes", help="Append to notes"),
    when: Optional[When] = typer.Option(None, "--when", "-w", help="When to schedule"),
    when_date: Optional[str] = typer.Option(None, "--when-date", help="Custom date (yyyy-mm-dd)"),
    deadline: Optional[str] = typer.Option(None, "--deadline", "-d", help="Deadline (empty string to clear)"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Replace tags (comma-separated)"),
    add_tags: Optional[str] = typer.Option(None, "--add-tags", help="Add tags (comma-separated)"),
    checklist: Optional[str] = typer.Option(None, "--checklist", help="Replace checklist items"),
    prepend_checklist: Optional[str] = typer.Option(None, "--prepend-checklist", help="Prepend checklist items"),
    append_checklist: Optional[str] = typer.Option(None, "--append-checklist", help="Append checklist items"),
    list_name: Optional[str] = typer.Option(None, "--list", help="Move to project/area"),
    list_id: Optional[str] = typer.Option(None, "--list-id", help="Move to project/area ID"),
    heading: Optional[str] = typer.Option(None, "--heading", help="Move to heading"),
    heading_id: Optional[str] = typer.Option(None, "--heading-id", help="Move to heading ID"),
    completed: bool = typer.Option(False, "--completed", help="Mark as completed"),
    canceled: bool = typer.Option(False, "--canceled", help="Mark as canceled"),
    duplicate: bool = typer.Option(False, "--duplicate", help="Duplicate before updating"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show the task after update"),
    creation_date: Optional[str] = typer.Option(None, "--creation-date", help="Creation date (ISO8601)"),
    completion_date: Optional[str] = typer.Option(None, "--completion-date", help="Completion date (ISO8601)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Update an existing task in Things (requires auth token)"""

    auth_token = get_auth_token()
    if not auth_token and not dry_run:
        console.print("[red]Error: THINGS_TOKEN environment variable required for update command[/red]")
        raise typer.Exit(1)

    params = {
        "id": task_id,
        "auth-token": auth_token,
        "title": title,
        "notes": notes,
        "prepend-notes": prepend_notes,
        "append-notes": append_notes,
        "when": when.value if when else when_date,
        "deadline": deadline,
        "tags": tags,
        "add-tags": add_tags,
        "checklist-items": "\n".join(split_items(checklist)) if checklist else None,
        "prepend-checklist-items": "\n".join(split_items(prepend_checklist)) if prepend_checklist else None,
        "append-checklist-items": "\n".join(split_items(append_checklist)) if append_checklist else None,
        "list": list_name,
        "list-id": list_id,
        "heading": heading,
        "heading-id": heading_id,
        "completed": completed if completed else None,
        "canceled": canceled if canceled else None,
        "duplicate": duplicate if duplicate else None,
        "reveal": reveal if reveal else None,
        "creation-date": creation_date,
        "completion-date": completion_date,
    }

    url = build_url("update", params)
    execute_url(url, dry_run)


@app.command("update-project")
def update_project(
    project_id: str = typer.Option(..., "--id", help="Project ID (UUID)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Replace notes"),
    prepend_notes: Optional[str] = typer.Option(None, "--prepend-notes", help="Prepend to notes"),
    append_notes: Optional[str] = typer.Option(None, "--append-notes", help="Append to notes"),
    when: Optional[When] = typer.Option(None, "--when", "-w", help="When to schedule"),
    when_date: Optional[str] = typer.Option(None, "--when-date", help="Custom date (yyyy-mm-dd)"),
    deadline: Optional[str] = typer.Option(None, "--deadline", "-d", help="Deadline"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Replace tags (comma-separated)"),
    add_tags: Optional[str] = typer.Option(None, "--add-tags", help="Add tags (comma-separated)"),
    area: Optional[str] = typer.Option(None, "--area", help="Move to area"),
    area_id: Optional[str] = typer.Option(None, "--area-id", help="Move to area ID"),
    completed: bool = typer.Option(False, "--completed", help="Mark as completed"),
    canceled: bool = typer.Option(False, "--canceled", help="Mark as canceled"),
    duplicate: bool = typer.Option(False, "--duplicate", help="Duplicate before updating"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show the project after update"),
    creation_date: Optional[str] = typer.Option(None, "--creation-date", help="Creation date (ISO8601)"),
    completion_date: Optional[str] = typer.Option(None, "--completion-date", help="Completion date (ISO8601)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Update an existing project in Things (requires auth token)"""

    auth_token = get_auth_token()
    if not auth_token and not dry_run:
        console.print("[red]Error: THINGS_TOKEN environment variable required for update-project command[/red]")
        raise typer.Exit(1)

    params = {
        "id": project_id,
        "auth-token": auth_token,
        "title": title,
        "notes": notes,
        "prepend-notes": prepend_notes,
        "append-notes": append_notes,
        "when": when.value if when else when_date,
        "deadline": deadline,
        "tags": tags,
        "add-tags": add_tags,
        "area": area,
        "area-id": area_id,
        "completed": completed if completed else None,
        "canceled": canceled if canceled else None,
        "duplicate": duplicate if duplicate else None,
        "reveal": reveal if reveal else None,
        "creation-date": creation_date,
        "completion-date": completion_date,
    }

    url = build_url("update-project", params)
    execute_url(url, dry_run)


@app.command()
def show(
    list_id: Optional[BuiltInList] = typer.Option(None, "--id", help="Built-in list ID"),
    custom_id: Optional[str] = typer.Option(None, "--custom-id", help="Custom item/project/area/tag ID"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search by name (quick find)"),
    filter_tags: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter by tags (comma-separated)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Navigate to a specific view in Things"""

    # Determine which ID to use
    item_id = None
    if list_id:
        item_id = list_id.value
    elif custom_id:
        item_id = custom_id

    params = {
        "id": item_id,
        "query": query,
        "filter": filter_tags,
    }

    url = build_url("show", params)
    execute_url(url, dry_run)


@app.command()
def search(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Open Things search interface with optional pre-filled query"""

    params = {
        "query": query,
    }

    url = build_url("search", params)
    execute_url(url, dry_run)


@app.command()
def version(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Check Things version information"""

    url = build_url("version", {})
    execute_url(url, dry_run)
    console.print("[yellow]Note: Version info will be shown in Things app[/yellow]")


@app.command()
def json_command(
    data: Optional[str] = typer.Option(None, "--data", "-d", help="JSON array as string"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to JSON file"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show items after creation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Execute a JSON-based command for batch operations (requires auth token)"""

    auth_token = get_auth_token()
    if not auth_token and not dry_run:
        console.print("[red]Error: THINGS_TOKEN environment variable required for json command[/red]")
        raise typer.Exit(1)

    # Load JSON data
    json_data = None
    if file:
        try:
            with open(file, 'r') as f:
                json_data = json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {file}[/red]")
            raise typer.Exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON file: {e}[/red]")
            raise typer.Exit(1)
    elif data:
        try:
            json_data = json.loads(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON data: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]Error: Either --data or --file must be provided[/red]")
        raise typer.Exit(1)

    # Validate it's a list
    if not isinstance(json_data, list):
        console.print("[red]Error: JSON data must be an array[/red]")
        raise typer.Exit(1)

    # Check rate limit (max 250 items)
    if len(json_data) > 250:
        console.print("[red]Error: Maximum 250 items allowed per request[/red]")
        raise typer.Exit(1)

    params = {
        "data": json.dumps(json_data),
        "auth-token": auth_token,
        "reveal": reveal if reveal else None,
    }

    url = build_url("json", params)
    execute_url(url, dry_run)


# ============================================================================
# Import/Export Commands
# ============================================================================

@app.command("import")
def import_json(
    file: str = typer.Argument(..., help="Path to JSON file to import"),
    reveal: bool = typer.Option(False, "--reveal", "-r", help="Show items after import"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show URL without executing"),
):
    """Import tasks and projects from a JSON file"""

    # This is essentially an alias for json-command with --file
    json_command(data=None, file=file, reveal=reveal, dry_run=dry_run)


@app.command("export")
def export_template(
    output: str = typer.Argument(..., help="Output file path"),
    template_type: str = typer.Option("task", "--type", "-t", help="Template type: task, project, or batch"),
):
    """Export a JSON template for creating tasks/projects"""

    templates = {
        "task": [
            {
                "type": "to-do",
                "attributes": {
                    "title": "Example Task",
                    "notes": "Task notes here",
                    "when": "today",
                    "tags": ["existing-tag1", "existing-tag2"],
                    "checklist-items": [
                        {"type": "checklist-item", "attributes": {"title": "Subtask 1"}},
                        {"type": "checklist-item", "attributes": {"title": "Subtask 2"}}
                    ]
                }
            }
        ],
        "project": [
            {
                "type": "project",
                "attributes": {
                    "title": "Example Project",
                    "notes": "Project notes",
                    "tags": ["existing-tag"],
                    "items": [
                        {"type": "to-do", "attributes": {"title": "First task"}},
                        {"type": "heading", "attributes": {"title": "Section 1"}},
                        {"type": "to-do", "attributes": {"title": "Task in section"}},
                    ]
                }
            }
        ],
        "batch": [
            {
                "type": "to-do",
                "attributes": {
                    "title": "Task 1",
                    "when": "today"
                }
            },
            {
                "type": "to-do",
                "attributes": {
                    "title": "Task 2",
                    "when": "tomorrow"
                }
            },
            {
                "type": "project",
                "attributes": {
                    "title": "Project with tasks",
                    "items": [
                        {"type": "to-do", "attributes": {"title": "Subtask 1"}},
                        {"type": "to-do", "attributes": {"title": "Subtask 2"}}
                    ]
                }
            }
        ]
    }

    if template_type not in templates:
        console.print(f"[red]Error: Unknown template type '{template_type}'[/red]")
        console.print(f"[yellow]Available types: {', '.join(templates.keys())}[/yellow]")
        raise typer.Exit(1)

    try:
        with open(output, 'w') as f:
            json.dump(templates[template_type], f, indent=2)
        console.print(f"[green]✓ Template exported to {output}[/green]")
    except IOError as e:
        console.print(f"[red]Error writing file: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Read/List Commands (via JXA)
# ============================================================================

try:
    import things_jxa
    JXA_AVAILABLE = True
except ImportError:
    JXA_AVAILABLE = False


@app.command()
def list(
    view: Optional[str] = typer.Argument(None, help="List view: today, inbox, upcoming, anytime, someday, logbook, tags, areas, projects"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    area: Optional[str] = typer.Option(None, "--area", help="Filter by area"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project"),
):
    """List tasks and metadata from Things 3 (read-only, requires JXA)"""

    if not JXA_AVAILABLE:
        console.print("[red]Error: things_jxa module not found[/red]")
        console.print("[yellow]The list command requires the things_jxa.py module[/yellow]")
        raise typer.Exit(1)

    try:
        # Metadata queries
        if view == "tags":
            tags = things_jxa.get_all_tags()
            print(json.dumps(tags, indent=2, ensure_ascii=False))
            return

        if view == "areas":
            areas = things_jxa.get_all_areas()
            print(json.dumps(areas, indent=2, ensure_ascii=False))
            return

        if view == "projects":
            projects = things_jxa.get_all_projects()
            print(json.dumps(projects, indent=2, ensure_ascii=False))
            return

        # Task queries
        tasks = []

        if view and view in ["today", "inbox", "upcoming", "anytime", "someday", "logbook", "tomorrow"]:
            # Built-in list view
            tasks = things_jxa.get_list_tasks(view)
        elif tag:
            # Filter by tag
            tasks = things_jxa.get_tasks_by_tag(tag)
        elif area:
            # Filter by area
            tasks = things_jxa.get_tasks_by_area(area)
        elif project:
            # Filter by project
            tasks = things_jxa.get_tasks_by_project(project)
        else:
            # No filter specified - show help
            console.print("[yellow]Please specify a view or filter:[/yellow]")
            console.print("  Views: today, inbox, upcoming, anytime, someday, logbook")
            console.print("  Metadata: tags, areas, projects")
            console.print("  Filters: --tag, --area, --project")
            console.print("\nExamples:")
            console.print("  things list today")
            console.print("  things list --tag work")
            console.print("  things list --area Personal")
            raise typer.Exit(1)

        # Output as JSON
        print(json.dumps(tasks, indent=2, ensure_ascii=False))

    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    app()
