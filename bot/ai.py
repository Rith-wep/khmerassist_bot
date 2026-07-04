"""Gemini API calls and prompt assembly.

All provider-specific code lives in this file only, so swapping AI
providers later means rewriting this file and nothing else.
"""
import logging
from pathlib import Path

from google import genai
from google.genai import types

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


async def get_ai_reply(user_message: str) -> str:
    """Send the customer's message to Gemini and return its reply text."""
    try:
        response = await _client.aio.models.generate_content(
            model=AI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
        return response.text
    except Exception:
        logger.exception("Gemini API call failed")
        return FALLBACK_REPLY
