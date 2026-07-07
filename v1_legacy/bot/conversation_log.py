"""Logs every customer/bot exchange to a local file, one file per day."""
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def log_exchange(chat_id: int, customer_message: str, bot_reply: str) -> None:
    """Append one exchange to today's log file (creates logs/ and the file if needed)."""
    try:
        _LOGS_DIR.mkdir(exist_ok=True)
        log_file = _LOGS_DIR / f"{datetime.now():%Y-%m-%d}.log"
        timestamp = datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] chat_id={chat_id} | customer: {customer_message} | bot: {bot_reply}\n"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        logger.exception("Failed to write conversation log")
