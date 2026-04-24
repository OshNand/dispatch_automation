import subprocess
import shlex
from config.settings import WORKSPACE_DIR

def run_command(command: str, timeout: int = 60) -> str:
    """
    Runs a shell command safely in the workspace.
    Restricts potentially destructive commands in a basic way.
    """
    # Very basic safety check
    forbidden = ["rm -rf /", "mkfs", "dd"]
    for f in forbidden:
        if f in command:
            return f"Error: Command contains forbidden pattern: {f}"

    try:
        # Use shlex to split for safe execution (not using shell=True unless necessary)
        # Note: on Windows we might need shell=True for some built-ins, but for cross-platform
        # subprocess.run with a string and shell=True is easiest, though risky.
        # Given it's a local agent, we allow shell=True but run it in WORKSPACE_DIR
        result = subprocess.run(
            command,
            cwd=WORKSPACE_DIR,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        return output if output else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def run_tests(test_command: str = "pytest") -> str:
    """Runs tests in the workspace."""
    return run_command(test_command)
