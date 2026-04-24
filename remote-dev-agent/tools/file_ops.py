import os
from pathlib import Path
from config.settings import WORKSPACE_DIR

def read_file(filepath: str) -> str:
    """Reads content from a file within the workspace."""
    full_path = WORKSPACE_DIR / filepath
    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath: str, content: str) -> None:
    """Writes content to a file within the workspace."""
    full_path = WORKSPACE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

def list_files(subdir: str = "") -> str:
    """
    Returns an indented tree-like string of files in the workspace.
    Excludes .git, __pycache__, node_modules, etc.
    """
    start_path = WORKSPACE_DIR / subdir if subdir else WORKSPACE_DIR
    
    if not start_path.exists():
        return "Directory does not exist."

    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode'}
    
    tree_lines = []
    
    for root, dirs, files in os.walk(start_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = str(Path(root).relative_to(start_path)).count(os.sep)
        if level == 0 and root == str(start_path):
            tree_lines.append(f"{start_path.name}/")
        else:
            indent = ' ' * 4 * level
            tree_lines.append(f"{indent}{os.path.basename(root)}/")
            
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree_lines.append(f"{subindent}{f}")
            
    return "\n".join(tree_lines)
