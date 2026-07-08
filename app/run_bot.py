"""Entry point: starts every active business's bot from the database,
running them all concurrently from this one process.

Run with: python -m app.run_bot

Ported from v1_legacy/main.py; extended in build step 3 (multi-bot) to
load and run every active bot_config instead of just one.
"""
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.engine import BotEngine

_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOGS_DIR.mkdir(exist_ok=True)

_file_handler = TimedRotatingFileHandler(
    _LOGS_DIR / "errors.log", when="midnight", backupCount=30, encoding="utf-8"
)
_file_handler.setLevel(logging.WARNING)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), _file_handler],
)

logger = logging.getLogger(__name__)


def main() -> None:
    engine = BotEngine()
    print("Starting all active bots. Press Ctrl+C to stop.")
    try:
        asyncio.run(engine.run_forever())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")


if __name__ == "__main__":
    main()
