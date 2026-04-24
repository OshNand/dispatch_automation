import os
import logging
from pathlib import Path
from config.settings import WORKSPACE_DIR

logger = logging.getLogger(__name__)

def read_file(filepath: str) -> str:
    """Reads content from a file within the workspace."""
    try:
        from utils import validator
        validator.validate_file_path(filepath)
    except Exception as e:
        logger.error(f"Path validation failed for {filepath}: {e}")
        raise
    
    full_path = WORKSPACE_DIR / filepath
    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"Read file: {filepath} ({len(content)} bytes)")
        return content
    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        raise

def write_file(filepath: str, content: str) -> None:
    """Writes content to a file within the workspace."""
    try:
        from utils import validator
        validator.validate_file_path(filepath)
        validator.validate_file_size(filepath)
    except Exception as e:
        logger.error(f"Validation failed for {filepath}: {e}")
        raise
    
    full_path = WORKSPACE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote file: {filepath} ({len(content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        raise

def list_files(subdir: str = "") -> str:
    """
    Returns an indented tree-like string of files in the workspace.
    Excludes .git, __pycache__, node_modules, etc.
    """
    start_path = WORKSPACE_DIR / subdir if subdir else WORKSPACE_DIR
    
    if not start_path.exists():
        return "Directory does not exist."

    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', 'logs', 'tasks', 'checkpoints'}
    
    tree_lines = []
    file_count = 0
    
    try:
        for root, dirs, files in os.walk(start_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            level = str(Path(root).relative_to(start_path)).count(os.sep)
            if level == 0 and root == str(start_path):
                tree_lines.append(f"{start_path.name}/")
            else:
                indent = ' ' * 2 * level
                tree_lines.append(f"{indent}{os.path.basename(root)}/")
                
            subindent = ' ' * 2 * (level + 1)
            for f in sorted(files)[:50]:  # Limit to first 50 files per directory
                tree_lines.append(f"{subindent}{f}")
                file_count += 1
            
            if len(files) > 50:
                tree_lines.append(f"{subindent}... and {len(files) - 50} more files")
        
        if not tree_lines:
            return "Workspace is empty."
        
        logger.debug(f"Listed workspace with {file_count} files")
        return "\n".join(tree_lines)
    
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        return f"Error listing files: {e}"
    return "\n".join(tree_lines)
