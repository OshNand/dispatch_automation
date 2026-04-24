import logging
import sys
import os
import subprocess

def setup_logging():
    from config.settings import LOG_LEVEL
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def bootstrap_venv():
    """Automatically restarts the script using the local virtual environment if it exists."""
    # Check if we are already in the venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return

    # Check for local venv
    venv_dir = os.path.join(os.path.dirname(__file__), "venv")
    if os.name == "nt":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")

    if os.path.exists(venv_python):
        print(f"Detected local virtual environment. Restarting with {venv_python}...")
        # Use subprocess to run the venv python and exit this process
        try:
            # On Windows, we use subprocess.run and exit. 
            # os.execv is sometimes buggy on Windows with python paths.
            process = subprocess.run([venv_python] + sys.argv)
            sys.exit(process.returncode)
        except Exception as e:
            print(f"Failed to bootstrap venv: {e}")

if __name__ == "__main__":
    # Bootstrap must happen BEFORE other imports to avoid library compatibility issues
    bootstrap_venv()
    
    # Now safe to import project modules
    from bot.telegram_bot import run_bot
    
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Initializing Remote Autonomous Development Agent...")
    
    # Run the Telegram Bot polling loop
    run_bot()
