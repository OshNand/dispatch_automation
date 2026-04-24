import os
from pydantic import BaseModel
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent

# Use REMOTE WORKSPACE if available, otherwise fallback
REMOTE_WORKSPACE = Path("C:\\Users\\oshna\\Desktop\\REMOTE WORKSPACE")
if REMOTE_WORKSPACE.exists():
    WORKSPACE_DIR = REMOTE_WORKSPACE
else:
    WORKSPACE_DIR = BASE_DIR / "workspace"

LOGS_DIR = BASE_DIR / "logs"
TASKS_DIR = BASE_DIR / "tasks"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"

# Ensure required directories exist
for directory in [WORKSPACE_DIR, LOGS_DIR, TASKS_DIR, CHECKPOINT_DIR]:
    os.makedirs(directory, exist_ok=True)

class Config(BaseModel):
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    ALLOWED_USER_ID: str = os.getenv("ALLOWED_USER_ID", "YOUR_TELEGRAM_USER_ID_HERE")

    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma")

    # Safety thresholds
    CPU_CRITICAL_PERCENT: float = 95.0
    GPU_CRITICAL_PERCENT: float = 95.0
    TEMP_CRITICAL_C: float = 85.0
    COOLDOWN_SECONDS: int = 600  # 10 minutes
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Execution settings
    MAX_FILE_SIZE_MB: float = 50.0  # Max file size to process
    MAX_FILES_PER_SESSION: int = 5
    SESSION_TIMEOUT_SECONDS: int = 300  # 5 minutes per session

    class Config:
        validate_assignment = True

settings = Config()
