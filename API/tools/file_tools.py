import os
from langchain_core.tools import tool


@tool
def read_file(filepath: str) -> str:
    """Reads the content of a file from the disk. Provide absolute or relative path."""
    if not os.path.exists(filepath):
        return f"Error: File {filepath} does not exist."
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"


@tool
def write_file(filepath: str, content: str) -> str:
    """Writes content to a file on the disk, overwriting existing content. Provide absolute or relative path."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing to file {filepath}: {str(e)}"


@tool
def list_directory(dir_path: str) -> str:
    """Lists files and directories within a given directory path."""
    if not os.path.exists(dir_path):
        return f"Error: Directory {dir_path} does not exist."
    try:
        files = os.listdir(dir_path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing directory {dir_path}: {str(e)}"
