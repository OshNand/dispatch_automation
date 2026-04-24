import logging
import time
from typing import Dict, Callable, Optional
from reasoning.planner import generate_session_plan
from tools.file_ops import write_file, read_file
from tools.cmd_ops import run_command
from monitor.safety_controller import safety_controller
from config.settings import SESSION_TIMEOUT_SECONDS
from utils import session_manager, execution_logger, validator, ValidationError

logger = logging.getLogger(__name__)

class SessionExecutor:
    """Executes sessions with checkpoint, error handling, and recovery support."""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def execute_session(
        self, 
        session: dict, 
        safety_callback: Optional[Callable] = None,
        retry_on_failure: bool = True
    ) -> dict:
        """
        Executes a single session safely with checkpoint and error recovery.
        """
        session_id = session.get("id")
        goal = session.get("goal")
        
        report = {
            "session_id": session_id,
            "goal": goal,
            "changes": [],
            "status": "failed",
            "notes": "",
            "retry_count": 0
        }
        
        # Initialize execution log
        log_file = execution_logger.initialize_session_log(session_id, goal)
        
        try:
            # Validate session structure
            validator.validate_session(session)
            logger.info(f"Starting session {session_id}: {goal}")
            execution_logger.log_step(log_file, "validation", {"status": "passed"})
            
            # Check for checkpoint (recovery from previous execution)
            checkpoint = session_manager.load_checkpoint(session_id)
            start_step = 0
            if checkpoint:
                logger.info(f"Found checkpoint for session {session_id}")
                start_step = checkpoint["current_step"]
                execution_logger.log_warning(log_file, f"Resumed from checkpoint at step {start_step}")
            
            # Enforce safety before starting
            safety_controller.enforce_safety(callback=safety_callback)
            
            # Plan steps
            logger.info(f"Generating execution plan for session {session_id}")
            plan = generate_session_plan(session)
            steps = plan.get("steps", [])
            
            if not steps:
                report["notes"] = "Planner generated no steps for this session."
                execution_logger.finalize_session_log(log_file, "success", summary=report["notes"])
                return report
            
            logger.info(f"Session {session_id} has {len(steps)} steps")
            
            # Execute steps with error handling
            for step_index, step in enumerate(steps):
                if step_index < start_step:
                    logger.debug(f"Skipping step {step_index} (already completed)")
                    continue
                
                # Enforce safety between steps
                safety_controller.enforce_safety(callback=safety_callback)
                
                # Validate step before execution
                try:
                    validator.validate_step(step)
                except ValidationError as e:
                    error_msg = f"Invalid step {step_index}: {e}"
                    logger.error(error_msg)
                    execution_logger.log_step(log_file, step.get("action", "unknown"), {"error": str(e)}, "failed")
                    raise
                
                # Execute step with retry logic
                step_executed = self._execute_step_with_retry(
                    step, step_index, session_id, log_file, report, retry_on_failure
                )
                
                if not step_executed and not retry_on_failure:
                    raise Exception(f"Failed to execute step {step_index}")
                
                # Save checkpoint after each successful step
                session_manager.save_checkpoint(
                    session_id,
                    step_index + 1,
                    {"last_successful_step": step_index, "action": step.get("action")}
                )
            
            report["status"] = "success"
            report["notes"] = f"Session executed successfully with {len(steps)} steps."
            execution_logger.finalize_session_log(log_file, "success", summary=report["notes"])
            
            # Clear checkpoint after successful completion
            session_manager.clear_checkpoint(session_id)
            logger.info(f"Session {session_id} completed successfully")
            
        except ValidationError as e:
            report["status"] = "failed"
            report["notes"] = f"Validation error: {str(e)}"
            execution_logger.finalize_session_log(log_file, "failed", error=str(e))
            logger.error(f"Session {session_id} validation failed: {e}")
            
        except Exception as e:
            report["status"] = "failed"
            report["notes"] = f"Execution error: {str(e)}"
            execution_logger.finalize_session_log(log_file, "failed", error=str(e))
            logger.error(f"Session {session_id} failed: {e}", exc_info=True)
        
        return report
    
    def _execute_step_with_retry(
        self,
        step: Dict,
        step_index: int,
        session_id: int,
        log_file: str,
        report: Dict,
        retry: bool = True
    ) -> bool:
        """Execute a single step with retry logic."""
        action = step.get("action")
        retry_count = 0
        
        while retry_count <= (self.max_retries if retry else 0):
            try:
                if action == "write_file":
                    path = step.get("path")
                    content = step.get("content")
                    if not path or content is None:
                        raise ValidationError("write_file requires path and content")
                    
                    validator.validate_file_path(path)
                    validator.validate_file_size(path)
                    
                    write_file(path, content)
                    report["changes"].append(f"✓ Wrote file: {path}")
                    execution_logger.log_step(log_file, action, {"path": path}, "success")
                    logger.info(f"Step {step_index}: Wrote {path}")
                    return True
                
                elif action == "read_file":
                    path = step.get("path")
                    if not path:
                        raise ValidationError("read_file requires path")
                    
                    validator.validate_file_path(path)
                    read_file(path)
                    report["changes"].append(f"✓ Read file: {path}")
                    execution_logger.log_step(log_file, action, {"path": path}, "success")
                    logger.info(f"Step {step_index}: Read {path}")
                    return True
                
                elif action == "run_command":
                    command = step.get("command")
                    if not command:
                        raise ValidationError("run_command requires command")
                    
                    validator.validate_command(command)
                    output = run_command(command)
                    report["changes"].append(f"✓ Executed: {command} (output: {len(output)} bytes)")
                    execution_logger.log_step(log_file, action, {"command": command}, "success")
                    logger.info(f"Step {step_index}: Executed {command}")
                    return True
                
                else:
                    raise ValidationError(f"Unknown action: {action}")
            
            except (ValidationError, Exception) as e:
                retry_count += 1
                error_msg = f"Step {step_index} ({action}) failed: {str(e)}"
                
                if retry_count <= self.max_retries:
                    logger.warning(f"{error_msg}. Retrying ({retry_count}/{self.max_retries})...")
                    execution_logger.log_warning(log_file, error_msg)
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"{error_msg}. Max retries exceeded.")
                    execution_logger.log_step(log_file, action, {"error": str(e), "retries": retry_count}, "failed")
                    report["changes"].append(f"✗ Failed ({action}): {str(e)}")
                    raise
        
        return False

# Global executor instance
executor = SessionExecutor()

# Backward compatibility function
def execute_session(session: dict, safety_callback=None) -> dict:
    """Backward compatible wrapper for execute_session."""
    return executor.execute_session(session, safety_callback=safety_callback, retry_on_failure=True)
