import os
from pydantic import BaseModel
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"
LOGS_DIR = BASE_DIR / "logs"
TASKS_DIR = BASE_DIR / "tasks"

# Ensure required directories exist
for directory in [WORKSPACE_DIR, LOGS_DIR, TASKS_DIR]:
    os.makedirs(directory, exist_ok=True)

class Config(BaseModel):
    # Telegram settings
    # You can set these via environment variables before running, e.g.:
    # set TELEGRAM_BOT_TOKEN=your_token
    # set ALLOWED_USER_ID=123456789
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

settings = Config()
