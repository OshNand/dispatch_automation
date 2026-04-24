import logging
import sys
from bot.telegram_bot import run_bot

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Initializing Remote Autonomous Development Agent...")
    
    # Run the Telegram Bot polling loop
    run_bot()
