import subprocess
from config.settings import WORKSPACE_DIR

def git_status() -> str:
    """Returns the git status of the workspace directory."""
    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Git error: {e.stderr}"
    except FileNotFoundError:
        return "Git is not installed or not found in PATH."

def git_add_commit(message: str) -> str:
    """Adds all changes and commits them."""
    try:
        subprocess.run(["git", "add", "."], cwd=WORKSPACE_DIR, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Git commit error: {e.stderr}"
