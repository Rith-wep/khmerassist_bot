"""Gemini API calls and prompt assembly.

All provider-specific code lives in this file only, so swapping AI
providers later means rewriting this file and nothing else.
"""
import logging
from pathlib import Path

from google import genai
from google.genai import types

from bot import memory
from config import AI_MODEL, GEMINI_API_KEY

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GEMINI_API_KEY)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SYSTEM_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "system_prompt.md"
_BUSINESS_INFO_PATH = _PROJECT_ROOT / "business" / "business_info.md"


def _build_system_instruction() -> str:
    """Combine the bot personality rules with the current client's business facts."""
    system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    business_info = _BUSINESS_INFO_PATH.read_text(encoding="utf-8")
    return (
        f"{system_prompt}\n\n"
        "## Business Information (your ONLY source of facts — never use anything else)\n\n"
        f"{business_info}"
    )


SYSTEM_INSTRUCTION = _build_system_instruction()

FALLBACK_REPLY = (
    "សូមទោស! ឥឡូវនេះមានបញ្ហាបច្ចេកទេសបន្តិច។ សូមសាកល្បងម្តងទៀតក្នុងពេលបន្តិចទៀត។"
)

_GEMINI_ROLE = {"user": "user", "assistant": "model"}


def _build_contents(chat_id: int, user_message: str) -> list[types.Content]:
    """Turn stored history + the new message into Gemini's expected format."""
    contents = [
        types.Content(role=_GEMINI_ROLE[msg["role"]], parts=[types.Part(text=msg["text"])])
        for msg in memory.get_history(chat_id)
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return contents


async def get_ai_reply(chat_id: int, user_message: str) -> str:
    """Send the customer's message (with recent history) to Gemini and return its reply."""
    try:
        contents = _build_contents(chat_id, user_message)
        response = await _client.aio.models.generate_content(
            model=AI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
        reply = response.text
        memory.add_message(chat_id, "user", user_message)
        memory.add_message(chat_id, "assistant", reply)
        return reply
    except Exception:
        logger.exception("Gemini API call failed")
        return FALLBACK_REPLY
