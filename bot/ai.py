"""Gemini API calls and prompt assembly.

All provider-specific code lives in this file only, so swapping AI
providers later means rewriting this file and nothing else.

Each customer message triggers two Gemini calls, kept deliberately
separate:
1. _generate_reply — plain text generation (no tools), so it always
   reliably returns something to show the customer.
2. _classify — a silent, structured-output call that reads the
   conversation (including the reply from step 1) and decides whether
   a lead was just completed or a human handoff is needed. Its output
   is never shown to the customer, so it doesn't matter whether Gemini
   "feels like" writing prose alongside it.
Combining both jobs into one call used to sometimes make Gemini return
only a tool call with no visible text, which meant the customer saw a
misleading "technical difficulty" message even though nothing had
failed. Splitting the calls removes that failure mode entirely.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from bot import memory
from config import AI_MODEL, GEMINI_API_KEY

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GEMINI_API_KEY)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SYSTEM_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "system_prompt.md"
_BUSINESS_INFO_PATH = _PROJECT_ROOT / "business" / "business_info.md"

RETRY_DELAY_SECONDS = 2


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

_HANDOFF_ALREADY_ACTIVE_NOTE = (
    "\n\nNote: this customer's issue has already been escalated to a human staff "
    "member. Keep answering simple questions normally, but do not try to resolve "
    "their original unresolved issue yourself — if it comes up again, just remind "
    "them that staff will handle it."
)

FALLBACK_REPLY = (
    "សូមទោស! ឥឡូវនេះមានបញ្ហាបច្ចេកទេសបន្តិច។ សូមសាកល្បងម្តងទៀតក្នុងពេលបន្តិចទៀត។"
)

_GEMINI_ROLE = {"user": "user", "assistant": "model"}

_CLASSIFIER_INSTRUCTION = (
    "You are an internal classifier for a customer support conversation. You are "
    "given the conversation so far, ending with the assistant's latest reply. Do "
    "NOT write a reply yourself — only output JSON matching the schema.\n\n"
    "Set lead to a non-null object ONLY if, across the whole conversation, the "
    "customer has now given BOTH their name and phone number and wants to book, "
    "order, or proceed with a service — include their name, phone, and a short "
    "description of what they want. Otherwise set lead to null.\n\n"
    "Set could_not_answer=true if the assistant's latest reply was not able to "
    "fully answer the customer's question using the business information. Set "
    "requested_human_or_upset=true if the customer's latest message explicitly "
    "asked for a human/staff member, or sounded upset, frustrated, or angry. Give "
    "a short reason phrase for internal staff use."
)

_CLASSIFICATION_SCHEMA = types.Schema(
    type="OBJECT",
    properties={
        "lead": types.Schema(
            type="OBJECT",
            nullable=True,
            properties={
                "name": types.Schema(type="STRING"),
                "phone": types.Schema(type="STRING"),
                "interest": types.Schema(type="STRING"),
            },
            required=["name", "phone", "interest"],
        ),
        "could_not_answer": types.Schema(type="BOOLEAN"),
        "requested_human_or_upset": types.Schema(type="BOOLEAN"),
        "reason": types.Schema(type="STRING"),
    },
    required=["could_not_answer", "requested_human_or_upset", "reason"],
)


def _build_contents(chat_id: int, user_message: str) -> list[types.Content]:
    """Turn stored history + the new message into Gemini's expected format."""
    contents = [
        types.Content(role=_GEMINI_ROLE[msg["role"]], parts=[types.Part(text=msg["text"])])
        for msg in memory.get_history(chat_id)
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return contents


def _system_instruction_for(chat_id: int) -> str:
    """Add a runtime note when this chat has already been escalated to a human."""
    if memory.is_handoff_active(chat_id):
        return SYSTEM_INSTRUCTION + _HANDOFF_ALREADY_ACTIVE_NOTE
    return SYSTEM_INSTRUCTION


async def _generate_reply(contents: list[types.Content], system_instruction: str) -> str:
    """Generate the customer-facing reply. Retries once after a short delay on failure."""
    config = types.GenerateContentConfig(system_instruction=system_instruction)
    try:
        response = await _client.aio.models.generate_content(
            model=AI_MODEL, contents=contents, config=config
        )
    except Exception:
        logger.warning("Gemini reply call failed, retrying once...", exc_info=True)
        await asyncio.sleep(RETRY_DELAY_SECONDS)
        response = await _client.aio.models.generate_content(
            model=AI_MODEL, contents=contents, config=config
        )
    return (response.text or "").strip() or FALLBACK_REPLY


async def _classify(contents: list[types.Content], assistant_reply: str) -> Optional[dict]:
    """Silently classify the exchange for lead/handoff signals (never shown to the customer)."""
    classifier_contents = contents + [
        types.Content(role="model", parts=[types.Part(text=assistant_reply)])
    ]
    try:
        response = await _client.aio.models.generate_content(
            model=AI_MODEL,
            contents=classifier_contents,
            config=types.GenerateContentConfig(
                system_instruction=_CLASSIFIER_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_CLASSIFICATION_SCHEMA,
            ),
        )
        return json.loads(response.text)
    except Exception:
        logger.warning(
            "Gemini classification call failed; skipping lead/handoff detection "
            "for this message",
            exc_info=True,
        )
        return None


def _apply_conversation_flags(chat_id: int, classification: Optional[dict]) -> Optional[str]:
    """Update handoff/streak state from the classifier output; return a handoff reason if needed."""
    if not classification:
        return None

    if classification.get("requested_human_or_upset"):
        memory.reset_unanswered_streak(chat_id)
        memory.set_handoff_active(chat_id, True)
        return classification.get("reason") or "Customer asked for a human or seems upset."

    if classification.get("could_not_answer"):
        streak = memory.increment_unanswered_streak(chat_id)
        if streak >= 2:
            memory.set_handoff_active(chat_id, True)
            memory.reset_unanswered_streak(chat_id)
            return classification.get("reason") or (
                "Could not answer two questions in a row from the business information."
            )
        return None

    memory.reset_unanswered_streak(chat_id)
    return None


async def get_ai_reply(chat_id: int, user_message: str) -> tuple[str, Optional[dict], Optional[str]]:
    """Send the customer's message (with recent history) to Gemini.

    Returns (reply_text, lead, handoff_reason):
    - lead: a dict with name/phone/interest if a complete lead was just detected, else None.
    - handoff_reason: a short string if this turn should escalate to a human, else None.
    """
    contents = _build_contents(chat_id, user_message)
    system_instruction = _system_instruction_for(chat_id)

    try:
        reply = await _generate_reply(contents, system_instruction)
    except Exception:
        logger.exception("get_ai_reply failed for chat_id=%s", chat_id)
        return FALLBACK_REPLY, None, None

    memory.add_message(chat_id, "user", user_message)
    memory.add_message(chat_id, "assistant", reply)

    classification = await _classify(contents, reply)
    lead = classification.get("lead") if classification else None
    handoff_reason = _apply_conversation_flags(chat_id, classification)

    return reply, lead, handoff_reason
