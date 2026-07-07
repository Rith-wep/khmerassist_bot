import json
import logging
from datetime import datetime
from pathlib import Path

from telegram import Bot

from bot import memory
from config import OWNER_CHAT_ID

logger = logging.getLogger(__name__)

_LEADS_FILE = Path(__file__).resolve().parent.parent / "leads.json"

def _load_leads() -> list[dict]:
    if not _LEADS_FILE.exists():
        return []
    return json.loads(_LEADS_FILE.read_text(encoding="utf-8"))


def _save_lead(lead: dict) -> None:
    leads = _load_leads()
    leads.append(lead)
    _LEADS_FILE.write_text(
        json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def process_lead(bot: Bot, chat_id: int, name: str, phone: str, interest: str) -> None:
    """Save a captured lead to disk and notify the business owner on Telegram."""
    memory.set_known_name(chat_id, name)

    lead = {
        "chat_id": chat_id,
        "name": name,
        "phone": phone,
        "interest": interest,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    _save_lead(lead)

    if OWNER_CHAT_ID is None:
        logger.warning("OWNER_CHAT_ID not set; lead saved locally but owner was not notified.")
        return

    owner_message = (
        "New lead!\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Wants: {interest}\n"
        f"Time: {lead['timestamp']}"
    )
    try:
        await bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_message)
    except Exception:
        logger.exception("Failed to notify owner about new lead")
