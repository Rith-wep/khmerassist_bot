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
