"""Entry point: starts the Telegram bot (polling mode)."""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.ai import FALLBACK_REPLY
from bot.handlers import handle_message, myid, reset
from config import TELEGRAM_BOT_TOKEN

_LOGS_DIR = Path(__file__).resolve().parent / "logs"
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


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Safety net: log any unexpected exception and apologize instead of crashing."""
    logger.error("Unhandled exception while processing an update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(FALLBACK_REPLY)
        except Exception:
            logger.exception("Failed to send the fallback apology to the user")


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(_on_error)

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
