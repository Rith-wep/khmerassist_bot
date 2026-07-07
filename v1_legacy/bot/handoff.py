"""Human handoff: notifying the business owner when a conversation needs a person.

bot/ai.py detects when a handoff is needed (customer asked for a human,
seems upset, or the bot couldn't answer twice in a row) and hands the
reason to notify_owner() here, which is the only place that sends the
handoff notification.
"""
import logging

from telegram import Bot

from bot import memory
from config import OWNER_CHAT_ID

logger = logging.getLogger(__name__)

_CONTEXT_MESSAGES = 6  # last ~3 exchanges, included so the owner has context


async def notify_owner(bot: Bot, chat_id: int, reason: str) -> None:
    """Tell the business owner this conversation needs a human, with recent context."""
    if OWNER_CHAT_ID is None:
        logger.warning("OWNER_CHAT_ID not set; skipping handoff notification.")
        return

    name = memory.get_known_name(chat_id) or "(name not given yet)"
    recent = memory.get_history(chat_id)[-_CONTEXT_MESSAGES:]
    transcript = "\n".join(
        f"{'Customer' if m['role'] == 'user' else 'Bot'}: {m['text']}" for m in recent
    ) or "(no recent messages)"

    message = (
        "Human handoff needed!\n"
        f"Customer: {name}\n"
        f"Reason: {reason}\n\n"
        f"Recent conversation:\n{transcript}"
    )
    try:
        await bot.send_message(chat_id=OWNER_CHAT_ID, text=message)
    except Exception:
        logger.exception("Failed to notify owner about handoff")
