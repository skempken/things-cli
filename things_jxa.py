"""
Things JXA (JavaScript for Automation) Helper Module

This module provides functions to read data from Things 3 using JXA.
Note: JXA can only READ from Things 3, not write. Use the URL scheme for write operations.
"""

import subprocess
import json
from typing import List, Dict, Optional, Any
from rich.console import Console

console = Console()

# Hardcoded locale mappings for Things 3 built-in lists
# Maps English list names to localized names for each supported language
LOCALE_MAPPINGS = {
    "de": {
        "inbox": "Eingang",
        "today": "Heute",
        "tomorrow": "Morgen",
        "anytime": "Jederzeit",
        "upcoming": "Geplant",
        "someday": "Irgendwann",
        "logbook": "Logbuch",
    },
    "en": {
        "inbox": "Inbox",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "anytime": "Anytime",
        "upcoming": "Upcoming",
        "someday": "Someday",
        "logbook": "Logbook",
    },
}

# Legacy mapping for backwards compatibility
LIST_NAME_MAP = LOCALE_MAPPINGS["de"]


def detect_list_names() -> Dict[str, str]:
    """
    Auto-detect the localized list names from Things 3.

    Queries Things 3 via JXA to get all built-in list names and creates
    a mapping from English names to the actual localized names.

    Returns:
        Dictionary mapping English list names to localized names

    Raises:
        RuntimeError: If detection fails, falls back to German locale
    """
    script = '''
    const things = Application("Things3");
    const lists = things.lists();
    const result = [];
    for (let i = 0; i < lists.length; i++) {
        result.push(lists[i].name());
    }
    JSON.stringify(result);
    '''

    try:
        output = run_jxa(script)
        list_names = json.loads(output)

        # Things 3 built-in lists are returned in a specific order
        # We map them to their English equivalents by index
        # Order: Inbox, Today, Upcoming, Anytime, Someday, Logbook (Tomorrow is virtual)
        english_keys = ["inbox", "today", "upcoming", "anytime", "someday", "logbook"]

        detected_mapping = {}
        for i, english_key in enumerate(english_keys):
            if i < len(list_names):
                detected_mapping[english_key] = list_names[i]

        # Tomorrow is not a real list in Things 3, but a filter
        # We need to detect it by checking known translations
        known_tomorrow = {
            "de": "Morgen",
            "en": "Tomorrow",
            # Add more as needed
        }

        # Try to detect Tomorrow by checking if any known translation exists
        for locale, tomorrow_name in known_tomorrow.items():
            if locale in LOCALE_MAPPINGS:
                first_list = detected_mapping.get("inbox", "")
                # If we detected Inbox correctly, use the same locale for Tomorrow
                if first_list == LOCALE_MAPPINGS[locale]["inbox"]:
                    detected_mapping["tomorrow"] = LOCALE_MAPPINGS[locale]["tomorrow"]
                    break

        # Fallback: if Tomorrow not detected, try German
        if "tomorrow" not in detected_mapping:
            detected_mapping["tomorrow"] = "Morgen"

        return detected_mapping

    except Exception as e:
        # Fallback to German locale if detection fails
        console.print(f"[yellow]Warning: Could not auto-detect locale, using German. Error: {e}[/yellow]")
        return LOCALE_MAPPINGS["de"]


def run_jxa(script: str) -> str:
    """
    Execute a JXA (JavaScript for Automation) script and return the output.

    Args:
        script: The JXA script to execute

    Returns:
        The script output as a string

    Raises:
        RuntimeError: If the script execution fails
    """
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "Things3" in error_msg or "Application" in error_msg:
                raise RuntimeError(
                    "Could not connect to Things 3. "
                    "Make sure Things 3 is installed and running."
                )
            raise RuntimeError(f"JXA script failed: {error_msg}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise RuntimeError("JXA script timed out after 30 seconds")
    except FileNotFoundError:
        raise RuntimeError("osascript command not found. Are you on macOS?")


def get_list_tasks(list_name: str, locale: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all tasks from a built-in list.

    Args:
        list_name: Name of the list (inbox, today, tomorrow, anytime, upcoming, someday, logbook)
        locale: Optional locale code (e.g., 'de', 'en'). If None or 'auto', auto-detects locale.

    Returns:
        List of task dictionaries
    """
    # Determine the mapping to use based on locale parameter
    if locale and locale != "auto" and locale in LOCALE_MAPPINGS:
        # Use hardcoded mapping for specified locale (fast)
        name_mapping = LOCALE_MAPPINGS[locale]
    elif locale is None or locale == "auto":
        # Auto-detect locale from Things 3 (slower, but automatic)
        name_mapping = detect_list_names()
    else:
        # Unknown locale, fall back to auto-detection
        name_mapping = detect_list_names()

    # Translate English list name to localized name
    localized_name = name_mapping.get(list_name.lower(), list_name)

    script = f'''
    const things = Application("Things3");
    const lists = things.lists();
    let targetList = null;
    for (let i = 0; i < lists.length; i++) {{
        if (lists[i].name() === "{localized_name}") {{
            targetList = lists[i];
            break;
        }}
    }}
    if (!targetList) {{
        throw new Error("List not found: {localized_name}");
    }}

    const tasks = targetList.toDos();
    const result = [];
    for (let i = 0; i < tasks.length; i++) {{
        const t = tasks[i];
        result.push({{
            id: t.id(),
            name: t.name(),
            status: t.status(),
            notes: t.notes() || "",
            tagNames: t.tagNames() || "",
            dueDate: t.dueDate() ? t.dueDate().toString() : null,
            creationDate: t.creationDate() ? t.creationDate().toString() : null
        }});
    }}
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Get all tasks (to-dos) from Things 3.

    Returns:
        List of task dictionaries
    """
    script = '''
    const things = Application("Things3");
    const tasks = things.toDos();
    const result = [];
    for (let i = 0; i < tasks.length; i++) {
        const t = tasks[i];
        result.push({
            id: t.id(),
            name: t.name(),
            status: t.status(),
            notes: t.notes() || "",
            tagNames: t.tagNames() || "",
            dueDate: t.dueDate() ? t.dueDate().toString() : null,
            creationDate: t.creationDate() ? t.creationDate().toString() : null
        });
    }
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_tasks_by_tag(tag_name: str) -> List[Dict[str, Any]]:
    """
    Get all tasks with a specific tag.

    Args:
        tag_name: Name of the tag to filter by

    Returns:
        List of task dictionaries
    """
    script = f'''
    const things = Application("Things3");
    const allTasks = things.toDos();
    const result = [];
    for (let i = 0; i < allTasks.length; i++) {{
        const t = allTasks[i];
        const tags = t.tagNames() || "";
        if (tags.includes("{tag_name}")) {{
            result.push({{
                id: t.id(),
                name: t.name(),
                status: t.status(),
                notes: t.notes() || "",
                tagNames: tags,
                dueDate: t.dueDate() ? t.dueDate().toString() : null,
                creationDate: t.creationDate() ? t.creationDate().toString() : null
            }});
        }}
    }}
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_tasks_by_area(area_name: str) -> List[Dict[str, Any]]:
    """
    Get all tasks in a specific area.

    Args:
        area_name: Name of the area

    Returns:
        List of task dictionaries
    """
    script = f'''
    const things = Application("Things3");
    const areas = things.areas();
    let targetArea = null;
    for (let i = 0; i < areas.length; i++) {{
        if (areas[i].name() === "{area_name}") {{
            targetArea = areas[i];
            break;
        }}
    }}
    if (!targetArea) {{
        throw new Error("Area not found: {area_name}");
    }}

    const tasks = targetArea.toDos();
    const result = [];
    for (let i = 0; i < tasks.length; i++) {{
        const t = tasks[i];
        result.push({{
            id: t.id(),
            name: t.name(),
            status: t.status(),
            notes: t.notes() || "",
            tagNames: t.tagNames() || "",
            dueDate: t.dueDate() ? t.dueDate().toString() : null,
            creationDate: t.creationDate() ? t.creationDate().toString() : null
        }});
    }}
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_tasks_by_project(project_name: str) -> List[Dict[str, Any]]:
    """
    Get all tasks in a specific project.

    Args:
        project_name: Name of the project

    Returns:
        List of task dictionaries
    """
    script = f'''
    const things = Application("Things3");
    const projects = things.projects();
    let targetProject = null;
    for (let i = 0; i < projects.length; i++) {{
        if (projects[i].name() === "{project_name}") {{
            targetProject = projects[i];
            break;
        }}
    }}
    if (!targetProject) {{
        throw new Error("Project not found: {project_name}");
    }}

    const tasks = targetProject.toDos();
    const result = [];
    for (let i = 0; i < tasks.length; i++) {{
        const t = tasks[i];
        result.push({{
            id: t.id(),
            name: t.name(),
            status: t.status(),
            notes: t.notes() || "",
            tagNames: t.tagNames() || "",
            dueDate: t.dueDate() ? t.dueDate().toString() : null,
            creationDate: t.creationDate() ? t.creationDate().toString() : null
        }});
    }}
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_all_tags() -> List[str]:
    """
    Get all tag names from Things 3.

    Returns:
        List of tag names
    """
    script = '''
    const things = Application("Things3");
    const tags = things.tags();
    const result = [];
    for (let i = 0; i < tags.length; i++) {
        result.push(tags[i].name());
    }
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_all_areas() -> List[Dict[str, Any]]:
    """
    Get all areas from Things 3.

    Returns:
        List of area dictionaries with name and task count
    """
    script = '''
    const things = Application("Things3");
    const areas = things.areas();
    const result = [];
    for (let i = 0; i < areas.length; i++) {
        const area = areas[i];
        result.push({
            name: area.name(),
            taskCount: area.toDos().length
        });
    }
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)


def get_all_projects() -> List[Dict[str, Any]]:
    """
    Get all projects from Things 3.

    Returns:
        List of project dictionaries
    """
    script = '''
    const things = Application("Things3");
    const projects = things.projects();
    const result = [];
    for (let i = 0; i < projects.length; i++) {
        const p = projects[i];
        result.push({
            id: p.id(),
            name: p.name(),
            status: p.status(),
            notes: p.notes() || "",
            taskCount: p.toDos().length,
            dueDate: p.dueDate() ? p.dueDate().toString() : null
        });
    }
    JSON.stringify(result);
    '''

    output = run_jxa(script)
    return json.loads(output)
