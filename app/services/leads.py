"""Lead capture: saving a completed lead and notifying the business owner.

Ported from v1_legacy/bot/leads.py — identical owner notification message,
now persisted to the leads table instead of leads.json.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from telegram import Bot

from app.models.conversation import Conversation
from app.repositories.lead import LeadRepository
from app.services import conversation_state

logger = logging.getLogger(__name__)


async def process_lead(
    db: Session,
    business_id: int,
    bot: Bot,
    owner_chat_id: Optional[int],
    conversation: Conversation,
    name: str,
    phone: str,
    interest: str,
) -> None:
    """Save a captured lead to the DB and notify the business owner on Telegram."""
    conversation_state.set_customer_name(conversation, name)

    lead = LeadRepository(db, business_id).create(
        conversation_id=conversation.id,
        customer_name=name,
        phone=phone,
        interest=interest,
    )

    if owner_chat_id is None:
        logger.warning(
            "business_id=%s: owner_chat_id not set; lead saved but owner was not notified.",
            business_id,
        )
        return

    owner_message = (
        "New lead!\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Wants: {interest}\n"
        f"Time: {lead.created_at.isoformat(timespec='seconds')}"
    )
    try:
        await bot.send_message(chat_id=owner_chat_id, text=owner_message)
        lead.notified_owner = True
    except Exception:
        logger.exception("business_id=%s: failed to notify owner about new lead", business_id)
