"""Per-chat conversation memory.

Stored in-memory for now (a dict keyed by Telegram chat ID). Only the
functions below should be used by other files — keeping this interface
stable means swapping the storage for SQLite later won't require
changing bot/ai.py or bot/handlers.py.
"""
from typing import Literal

Role = Literal["user", "assistant"]

MAX_EXCHANGES = 10  # keep the last 10 user+assistant pairs per chat
_MAX_MESSAGES = MAX_EXCHANGES * 2

_history: dict[int, list[dict[str, str]]] = {}


def add_message(chat_id: int, role: Role, text: str) -> None:
    """Append a message to a chat's history, dropping the oldest if over the cap."""
    messages = _history.setdefault(chat_id, [])
    messages.append({"role": role, "text": text})
    if len(messages) > _MAX_MESSAGES:
        del messages[: len(messages) - _MAX_MESSAGES]


def get_history(chat_id: int) -> list[dict[str, str]]:
    """Return the stored messages for a chat, oldest first."""
    return list(_history.get(chat_id, []))


def clear_history(chat_id: int) -> None:
    """Forget everything remembered for a chat (used by /reset)."""
    _history.pop(chat_id, None)
