import os
import re
import glob
import difflib

from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from swi.utils.config import NOTEPAD
from langgraph.types import  interrupt



from enum import Enum
class FILE(Enum):
    READFILE = "get_file_content"
    WRITEFILE = "write_file_tool"
    GET_FOLDER_STRUCTURE = "folder_structure" 
    EDIT_TOOL = "edit_tool"
    NOTEPAD = "note_pad"


@tool
async def get_file_content(path: str) -> str:
    """
    Read file(s) from a given path or glob pattern.

    Args:
        path (str): Absolute path OR glob pattern (e.g., '*.txt', 'src/**/*.py')

    Returns:
            str: Concatenated file content(s) or error,
    """
    cwd = os.getcwd()
    writer = get_stream_writer()

    writer(f"Reading file(s) from: {path}")

    # Case 1: Single file (no glob pattern)
    if not re.search(r'\*', path):
        try:
            abs_path = os.path.join(cwd, path.lstrip("/"))
            writer(f"Reading file: {abs_path}")
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            writer(f"Error {e} in reading file")
            return "No file available"

    # Case 2: Glob pattern
    try:
        abs_pattern = os.path.join(cwd, path.lstrip("/"))
        matched_files = glob.glob(abs_pattern, recursive=True)

        writer(f"Matched Files: {matched_files}")
        if not matched_files:
            return f"No file for {path} pattern"

        contents = []
        for file_path in matched_files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    contents.append(f"--- {file_path} ---\n\n{file_content}\n\n")
                except Exception as e:
                    err_msg = f"--- {file_path} ---\n\n[Error reading file: {e}]\n\n"
                    writer(err_msg)
                    contents.append(err_msg)

        return "".join(contents) if contents else ""

    except Exception as e:
        return f"Error: {e}"



@tool
async def write_file_tool(code: str, path: str) -> str:
    """
    Write code to the given file path (relative to current working directory).

    Args:
        code (str): Code/content to write to file
        path (str): File path (absolute or relative)

    Returns:
            str:  Success or error message,
        
    """
    writer = get_stream_writer()
    cwd = os.getcwd()

    # Validation
    if not path:
        msg = "Cannot write: No file path provided"
        writer(msg)
        return msg

    if not code:
        msg = "Cannot write: No code provided"
        writer(msg)
        return msg

    try:
        # Normalize path (relative to cwd if not absolute)
        abs_path = path if os.path.isabs(path) else os.path.join(cwd, path.lstrip("/"))

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        # Write file
        human_response = interrupt(f"Permission to Write {path}")
        if not human_response.lower().find("y"):
            return "User says not to read the file"
        
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(code)

        msg = f"File written successfully → {abs_path}"
        writer(msg)
        return msg

    except PermissionError as e:
        msg = f"Permission denied while writing to {path}: {e}"
        writer(msg)
        return msg

    except IsADirectoryError as e:
        msg = f"Expected file path but got directory: {path}: {e}"
        writer(msg)
        return msg

    except Exception as e:
        msg = f"Unexpected error while writing {path}: {e}"
        writer(msg)
        return msg


@tool
def edit_file(path: str, old_string: str, new_string: str, number_of_replacements: int = 1) -> str:
    """
    Edit a file by replacing occurrences of a string.

    Args:
        path (str): File path (absolute or relative to current working directory)
        old_string (str): String to be replaced
        new_string (str): Replacement string
        number_of_replacements (int): How many occurrences to replace (default = 1)

    Returns:
            str: Status or diff of the change,
    """
    writer = get_stream_writer()
    cwd = os.getcwd()

    # Input validation
    if not old_string.strip():
        return  "Empty string cannot be replaced"

    if not new_string.strip():
        return  "Replacement string cannot be empty"

    try:
        # Normalize path
        abs_path = path if os.path.isabs(path) else os.path.join(cwd, path.lstrip("/"))

        # Read current file
        with open(abs_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Replace content
        updated_content = original_content.replace(old_string, new_string, number_of_replacements)

        # If no changes
        if original_content == updated_content:
            msg = f"No occurrences of '{old_string}' found in {abs_path}"
            writer(msg)
            return msg

        # Generate unified diff
        diff = "".join(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                updated_content.splitlines(keepends=True),
                fromfile=f"{abs_path} (current)",
                tofile=f"{abs_path} (updated)"
            )
        )

        msg = f"{abs_path}\n\nDiff:\n{diff}"
        writer(msg)

        # Write file
        human_response = interrupt(f"Permission to Update {diff}")
        if not human_response.lower().find("y"):
            return "User says not to edit the file"
        # Write updated content
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        
        return  msg

    except FileNotFoundError:
        msg = f"File not found: {path}"
        writer(msg)
        return msg

    except PermissionError as e:
        msg = f"Permission denied editing {path}: {e}"
        writer(msg)
        return  msg

    except Exception as e:
        msg = f"Unexpected error editing {path}: {e}"
        writer(msg)
        return  msg

    
@tool()
def get_folder_structure():
    """Get folder Structure"""
    """
    Generate a clean text tree of folder structure, skipping unwanted files/folders.
    
    Args:
        path (str): Root folder path.
        indent (str): Current indentation (used internally).
        ignore_hidden (bool): Skip hidden files/folders (starting with '.').
        
    Returns:
        str: Folder structure as a tree.
    """
    #folder_tree()
    pass
    


@tool
def note_pad(str):
    """Can be used as a NotePad to store information for long term"""
    open(NOTEPAD,"a").write(str)
    return "Task completed"



        



