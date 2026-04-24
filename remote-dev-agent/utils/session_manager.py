import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import TASKS_DIR, CHECKPOINT_DIR

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages session storage, retrieval, and checkpoint operations."""
    
    @staticmethod
    def save_session_queue(sessions: List[Dict], session_name: str = None) -> str:
        """Save a list of sessions to disk for later retrieval."""
        if not session_name:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        queue_file = TASKS_DIR / f"{session_name}.json"
        try:
            with open(queue_file, 'w') as f:
                json.dump(sessions, f, indent=2)
            logger.info(f"Saved session queue to {queue_file}")
            return str(queue_file)
        except Exception as e:
            logger.error(f"Failed to save session queue: {e}")
            return None
    
    @staticmethod
    def load_session_queue(session_file: Path) -> Optional[List[Dict]]:
        """Load a previously saved session queue."""
        try:
            with open(session_file, 'r') as f:
                sessions = json.load(f)
            logger.info(f"Loaded session queue from {session_file}")
            return sessions if isinstance(sessions, list) else None
        except Exception as e:
            logger.error(f"Failed to load session queue: {e}")
            return None
    
    @staticmethod
    def save_checkpoint(session_id: int, current_step: int, step_context: Dict) -> bool:
        """Save checkpoint data for resuming after cooldown/pause."""
        checkpoint_data = {
            "session_id": session_id,
            "current_step": current_step,
            "context": step_context,
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_file = CHECKPOINT_DIR / f"checkpoint_session_{session_id}.json"
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Checkpoint saved for session {session_id} at step {current_step}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    @staticmethod
    def load_checkpoint(session_id: int) -> Optional[Dict]:
        """Load checkpoint data for resuming execution."""
        checkpoint_file = CHECKPOINT_DIR / f"checkpoint_session_{session_id}.json"
        try:
            if not checkpoint_file.exists():
                return None
            
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            logger.info(f"Loaded checkpoint for session {session_id}")
            return checkpoint_data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    @staticmethod
    def clear_checkpoint(session_id: int) -> bool:
        """Delete checkpoint after successful session completion."""
        checkpoint_file = CHECKPOINT_DIR / f"checkpoint_session_{session_id}.json"
        try:
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                logger.info(f"Cleared checkpoint for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")
            return False

session_manager = SessionManager()
