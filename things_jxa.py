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

# Mapping of English list names to German (Things 3 is localized)
LIST_NAME_MAP = {
    "inbox": "Eingang",
    "today": "Heute",
    "tomorrow": "Morgen",
    "anytime": "Jederzeit",
    "upcoming": "Geplant",
    "someday": "Irgendwann",
    "logbook": "Logbuch",
}


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


def get_list_tasks(list_name: str) -> List[Dict[str, Any]]:
    """
    Get all tasks from a built-in list.

    Args:
        list_name: Name of the list (inbox, today, tomorrow, anytime, upcoming, someday, logbook)

    Returns:
        List of task dictionaries
    """
    # Translate English list name to German
    german_name = LIST_NAME_MAP.get(list_name.lower(), list_name)

    script = f'''
    const things = Application("Things3");
    const lists = things.lists();
    let targetList = null;
    for (let i = 0; i < lists.length; i++) {{
        if (lists[i].name() === "{german_name}") {{
            targetList = lists[i];
            break;
        }}
    }}
    if (!targetList) {{
        throw new Error("List not found: {german_name}");
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
