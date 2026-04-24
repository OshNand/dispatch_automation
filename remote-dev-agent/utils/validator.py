import logging
import re
from pathlib import Path
from config.settings import WORKSPACE_DIR, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass

class Validator:
    """Validates paths, files, and commands for security."""
    
    FORBIDDEN_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"mkfs",
        r"dd\s+if=",
        r":((){|:{|})",  # Bash bomb
        r"fork\s*\(",
        r"\.\.\/\.\.",  # Path traversal
    ]
    
    DANGEROUS_COMMANDS = [
        "format", "partition", "fdisk", "parted",
        "mkfs", "mount", "unmount", "chroot"
    ]
    
    @staticmethod
    def validate_file_path(filepath: str) -> bool:
        """
        Validate that a file path is safe and within workspace.
        Returns True if valid, raises ValidationError if not.
        """
        try:
            # Normalize path
            safe_path = Path(filepath).resolve()
            workspace_resolved = WORKSPACE_DIR.resolve()
            
            # Check if path is within workspace
            if not str(safe_path).startswith(str(workspace_resolved)):
                raise ValidationError(f"Path traversal detected: {filepath}")
            
            # Check for null bytes
            if "\0" in filepath:
                raise ValidationError("Null bytes in path")
            
            return True
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")
    
    @staticmethod
    def validate_file_size(filepath: str) -> bool:
        """Check if file size is within acceptable limits."""
        try:
            path = Path(filepath)
            if not path.exists():
                return True  # New files are OK
            
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                raise ValidationError(f"File too large: {size_mb}MB > {MAX_FILE_SIZE_MB}MB")
            
            return True
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to check file size: {e}")
    
    @staticmethod
    def validate_command(command: str) -> bool:
        """Validate that a command is safe to execute."""
        # Check for forbidden patterns
        for pattern in Validator.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValidationError(f"Command contains forbidden pattern: {pattern}")
        
        # Check for dangerous commands
        for dangerous in Validator.DANGEROUS_COMMANDS:
            if re.search(rf"\b{dangerous}\b", command, re.IGNORECASE):
                raise ValidationError(f"Dangerous command not allowed: {dangerous}")
        
        # Additional checks
        if ">>" in command and "/dev/" in command:
            raise ValidationError("Device redirection not allowed")
        
        if "|" in command and "sudo" in command:
            raise ValidationError("Piped commands with sudo not allowed")
        
        return True
    
    @staticmethod
    def validate_session(session: dict) -> bool:
        """Validate session structure and content."""
        required_fields = ["id", "goal", "targets", "type"]
        for field in required_fields:
            if field not in session:
                raise ValidationError(f"Missing required field in session: {field}")
        
        # Validate session type
        if session.get("type") not in ["read", "edit", "test"]:
            raise ValidationError(f"Invalid session type: {session.get('type')}")
        
        # Validate targets are list
        if not isinstance(session.get("targets"), list):
            raise ValidationError("Session targets must be a list")
        
        # Check target count
        if len(session.get("targets", [])) > 5:
            raise ValidationError("Too many targets per session (max 5)")
        
        # Validate each target path
        for target in session.get("targets", []):
            try:
                Validator.validate_file_path(target)
            except ValidationError as e:
                raise ValidationError(f"Invalid target path {target}: {e}")
        
        return True
    
    @staticmethod
    def validate_step(step: dict) -> bool:
        """Validate execution step structure."""
        if "action" not in step:
            raise ValidationError("Step missing action field")
        
        action = step.get("action")
        if action not in ["write_file", "read_file", "run_command"]:
            raise ValidationError(f"Invalid action: {action}")
        
        if action in ["write_file", "read_file"]:
            if "path" not in step:
                raise ValidationError(f"{action} step missing path")
            Validator.validate_file_path(step["path"])
        
        if action == "write_file":
            if "content" not in step:
                raise ValidationError("write_file step missing content")
        
        if action == "run_command":
            if "command" not in step:
                raise ValidationError("run_command step missing command")
            Validator.validate_command(step["command"])
        
        return True

validator = Validator()
