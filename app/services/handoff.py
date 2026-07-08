"""Human handoff: notifying the business owner when a conversation needs a person.

Ported from v1_legacy/bot/handoff.py. Recent context now comes from the
messages table instead of in-memory history.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from telegram import Bot

from app.models.conversation import Conversation
from app.services import conversation_state

logger = logging.getLogger(__name__)

_CONTEXT_EXCHANGES = 3  # last ~3 exchanges (6 messages), included so the owner has context


async def notify_owner(
    db: Session,
    business_id: int,
    bot: Bot,
    owner_chat_id: Optional[int],
    conversation: Conversation,
    reason: str,
) -> None:
    """Tell the business owner this conversation needs a human, with recent context."""
    if owner_chat_id is None:
        logger.warning(
            "business_id=%s: owner_chat_id not set; skipping handoff notification.", business_id
        )
        return

    name = conversation.customer_name or "(name not given yet)"
    recent = conversation_state.get_recent_messages(
        db, business_id, conversation.id, max_exchanges=_CONTEXT_EXCHANGES
    )
    transcript = "\n".join(
        f"{'Customer' if m.direction.value == 'customer' else 'Bot'}: {m.text}" for m in recent
    ) or "(no recent messages)"

    message = (
        "Human handoff needed!\n"
        f"Customer: {name}\n"
        f"Reason: {reason}\n\n"
        f"Recent conversation:\n{transcript}"
    )
    try:
        await bot.send_message(chat_id=owner_chat_id, text=message)
    except Exception:
        logger.exception("business_id=%s: failed to notify owner about handoff", business_id)
