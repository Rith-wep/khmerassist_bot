"""Per-chat conversation memory and lightweight conversation state.

Stored in-memory for now (dicts keyed by Telegram chat ID). Only the
functions below should be used by other files — keeping this interface
stable means swapping the storage for SQLite later won't require
changing bot/ai.py, bot/handlers.py, bot/leads.py, or bot/handoff.py.
"""
from typing import Literal, Optional

Role = Literal["user", "assistant"]

MAX_EXCHANGES = 10  # keep the last 10 user+assistant pairs per chat
_MAX_MESSAGES = MAX_EXCHANGES * 2

_history: dict[int, list[dict[str, str]]] = {}
_state: dict[int, dict] = {}


def _default_state() -> dict:
    return {"unanswered_streak": 0, "handoff_active": False, "known_name": None}


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
    """Forget everything remembered for a chat, including handoff state (used by /reset)."""
    _history.pop(chat_id, None)
    _state.pop(chat_id, None)


def increment_unanswered_streak(chat_id: int) -> int:
    """Record one more 'could not answer' reply in a row; return the new streak."""
    state = _state.setdefault(chat_id, _default_state())
    state["unanswered_streak"] += 1
    return state["unanswered_streak"]


def reset_unanswered_streak(chat_id: int) -> None:
    """Reset the 'could not answer' counter once the bot answers successfully."""
    if chat_id in _state:
        _state[chat_id]["unanswered_streak"] = 0


def is_handoff_active(chat_id: int) -> bool:
    """Whether this chat has already been escalated to a human."""
    return _state.get(chat_id, _default_state())["handoff_active"]


def set_handoff_active(chat_id: int, active: bool) -> None:
    """Mark whether this chat has been escalated to a human staff member."""
    state = _state.setdefault(chat_id, _default_state())
    state["handoff_active"] = active


def get_known_name(chat_id: int) -> Optional[str]:
    """Return the customer's name for this chat, if we've ever learned it."""
    return _state.get(chat_id, _default_state())["known_name"]


def set_known_name(chat_id: int, name: str) -> None:
    """Remember the customer's name (e.g. once a lead has been captured)."""
    state = _state.setdefault(chat_id, _default_state())
    state["known_name"] = name
