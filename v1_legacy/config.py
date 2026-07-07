"""Loads settings from .env. Never hardcode secrets in source files."""
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and fill it in."
    )

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Copy .env.example to .env and fill it in."
    )

_owner_chat_id_raw = os.getenv("OWNER_CHAT_ID")
OWNER_CHAT_ID: int | None = None
if _owner_chat_id_raw:
    try:
        OWNER_CHAT_ID = int(_owner_chat_id_raw)
    except ValueError:
        print(
            "WARNING: OWNER_CHAT_ID is not a valid number. "
            "Owner notifications (leads, handoff) are disabled."
        )
else:
    print(
        "WARNING: OWNER_CHAT_ID is not set. "
        "Owner notifications (leads, handoff) are disabled."
    )
