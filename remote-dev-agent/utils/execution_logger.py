import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from config.settings import LOGS_DIR

logger = logging.getLogger(__name__)

class ExecutionLogger:
    """Logs all session executions with detailed information."""
    
    @staticmethod
    def initialize_session_log(session_id: int, goal: str) -> str:
        """Create a new log file for a session."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = LOGS_DIR / f"session_{session_id}_{timestamp}.json"
        
        log_entry = {
            "session_id": session_id,
            "goal": goal,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "steps": [],
            "error": None,
            "warnings": []
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_entry, f, indent=2)
            logger.debug(f"Initialized log file: {log_file}")
            return str(log_file)
        except Exception as e:
            logger.error(f"Failed to initialize session log: {e}")
            return None
    
    @staticmethod
    def log_step(log_file: str, action: str, details: Dict, status: str = "success"):
        """Log a step execution."""
        try:
            log_path = Path(log_file)
            if not log_path.exists():
                logger.warning(f"Log file not found: {log_file}")
                return
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            step_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details,
                "status": status
            }
            
            log_data["steps"].append(step_entry)
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.debug(f"Logged step: {action}")
        except Exception as e:
            logger.error(f"Failed to log step: {e}")
    
    @staticmethod
    def log_warning(log_file: str, warning: str):
        """Log a warning during execution."""
        try:
            log_path = Path(log_file)
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            log_data["warnings"].append({
                "timestamp": datetime.now().isoformat(),
                "message": warning
            })
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log warning: {e}")
    
    @staticmethod
    def finalize_session_log(log_file: str, status: str, error: str = None, summary: str = None):
        """Mark session as complete and store final status."""
        try:
            log_path = Path(log_file)
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            log_data["end_time"] = datetime.now().isoformat()
            log_data["status"] = status
            if error:
                log_data["error"] = error
            if summary:
                log_data["summary"] = summary
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"Session log finalized: {status}")
        except Exception as e:
            logger.error(f"Failed to finalize session log: {e}")
    
    @staticmethod
    def generate_execution_summary() -> Dict:
        """Generate a summary of all executions."""
        summary = {
            "total_sessions": 0,
            "successful": 0,
            "failed": 0,
            "sessions": []
        }
        
        try:
            for log_file in LOGS_DIR.glob("session_*.json"):
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
                
                summary["total_sessions"] += 1
                if log_data.get("status") == "success":
                    summary["successful"] += 1
                elif log_data.get("status") == "failed":
                    summary["failed"] += 1
                
                summary["sessions"].append({
                    "session_id": log_data.get("session_id"),
                    "goal": log_data.get("goal"),
                    "status": log_data.get("status"),
                    "start_time": log_data.get("start_time"),
                    "end_time": log_data.get("end_time"),
                    "steps_count": len(log_data.get("steps", []))
                })
        except Exception as e:
            logger.error(f"Failed to generate execution summary: {e}")
        
        return summary

execution_logger = ExecutionLogger()
