import subprocess
import logging
import shlex
from config.settings import WORKSPACE_DIR

logger = logging.getLogger(__name__)

def run_command(command: str, timeout: int = 60) -> str:
    """
    Runs a shell command safely in the workspace.
    Validates command before execution.
    """
    try:
        from utils import validator
        validator.validate_command(command)
    except Exception as e:
        error_msg = f"Command validation failed: {e}"
        logger.error(error_msg)
        return error_msg

    try:
        logger.info(f"Executing command: {command[:100]}...")
        
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
        
        success_msg = output if output else "Command executed successfully with no output."
        logger.info(f"Command executed successfully")
        return success_msg
        
    except subprocess.TimeoutExpired:
        error_msg = f"Error: Command timed out after {timeout} seconds."
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        logger.error(error_msg)
        return error_msg

def run_tests(test_command: str = "pytest") -> str:
    """Runs tests in the workspace."""
    return run_command(test_command)
