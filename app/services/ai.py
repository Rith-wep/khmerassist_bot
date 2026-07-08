"""Gemini API calls and prompt assembly — the only AI-provider-aware module.

Ported from v1_legacy/bot/ai.py: same two-call design (generate the
customer-facing reply, then silently classify the exchange for lead/
handoff signals) and the same personality rules — now assembled from
this business's knowledge_items in the DB instead of business_info.md.

Each customer message triggers two Gemini calls, kept deliberately
separate:
1. _generate_reply — plain text generation (no tools), so it always
   reliably returns something to show the customer.
2. _classify — a silent, structured-output call that reads the
   conversation (including the reply from step 1) and decides whether
   a lead was just completed or a human handoff is needed. Its output
   is never shown to the customer.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.services import conversation_state
from app.services.knowledge import build_business_info_text

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.gemini_api_key)

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "system_prompt.md"
_RULES_TEXT = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

RETRY_DELAY_SECONDS = 2
MAX_EXCHANGES = conversation_state.MAX_EXCHANGES

_HANDOFF_ALREADY_ACTIVE_NOTE = (
    "\n\nNote: this customer's issue has already been escalated to a human staff "
    "member. Keep answering simple questions normally, but do not try to resolve "
    "their original unresolved issue yourself — if it comes up again, just remind "
    "them that staff will handle it."
)

FALLBACK_REPLY = (
    "សូមទោស! ឥឡូវនេះមានបញ្ហាបច្ចេកទេសបន្តិច។ សូមសាកល្បងម្តងទៀតក្នុងពេលបន្តិចទៀត។"
)

_GEMINI_ROLE = {"customer": "user", "bot": "model"}

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


def _build_system_instruction(business_id: int, db: Session, handoff_active: bool) -> str:
    """Combine the shared personality rules with this business's knowledge_items."""
    knowledge_items = conversation_state.get_knowledge_items(db, business_id)
    business_info = build_business_info_text(knowledge_items)
    instruction = (
        f"{_RULES_TEXT}\n\n"
        "## Business Information (your ONLY source of facts — never use anything else)\n\n"
        f"{business_info}"
    )
    if handoff_active:
        instruction += _HANDOFF_ALREADY_ACTIVE_NOTE
    return instruction


def _to_contents(messages) -> list[types.Content]:
    return [
        types.Content(role=_GEMINI_ROLE[m.direction.value], parts=[types.Part(text=m.text)])
        for m in messages
    ]


async def _generate_reply(contents: list[types.Content], system_instruction: str) -> str:
    """Generate the customer-facing reply. Retries once after a short delay on failure."""
    config = types.GenerateContentConfig(system_instruction=system_instruction)
    try:
        response = await _client.aio.models.generate_content(
            model=settings.ai_model, contents=contents, config=config
        )
    except Exception:
        logger.warning("Gemini reply call failed, retrying once...", exc_info=True)
        await asyncio.sleep(RETRY_DELAY_SECONDS)
        response = await _client.aio.models.generate_content(
            model=settings.ai_model, contents=contents, config=config
        )
    return (response.text or "").strip() or FALLBACK_REPLY


async def _classify(contents: list[types.Content], assistant_reply: str) -> Optional[dict]:
    """Silently classify the exchange for lead/handoff signals (never shown to the customer)."""
    classifier_contents = contents + [
        types.Content(role="model", parts=[types.Part(text=assistant_reply)])
    ]
    try:
        response = await _client.aio.models.generate_content(
            model=settings.ai_model,
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
            "Gemini classification call failed; skipping lead/handoff detection for this message",
            exc_info=True,
        )
        return None


def _apply_conversation_flags(
    business_id: int, chat_id: int, conversation: Conversation, classification: Optional[dict]
) -> Optional[str]:
    """Update handoff/streak state from the classifier output; return a handoff reason if needed."""
    if not classification:
        return None

    if classification.get("requested_human_or_upset"):
        conversation_state.reset_unanswered_streak(business_id, chat_id)
        conversation_state.set_handed_off(conversation, True)
        return classification.get("reason") or "Customer asked for a human or seems upset."

    if classification.get("could_not_answer"):
        streak = conversation_state.increment_unanswered_streak(business_id, chat_id)
        if streak >= 2:
            conversation_state.set_handed_off(conversation, True)
            conversation_state.reset_unanswered_streak(business_id, chat_id)
            return classification.get("reason") or (
                "Could not answer two questions in a row from the business information."
            )
        return None

    conversation_state.reset_unanswered_streak(business_id, chat_id)
    return None


async def get_ai_reply(
    db: Session, business_id: int, chat_id: int, user_message: str
) -> tuple[str, Optional[dict], Optional[str], Conversation]:
    """Send the customer's message (with recent DB history) to Gemini.

    Returns (reply_text, lead, handoff_reason, conversation):
    - lead: a dict with name/phone/interest if a complete lead was just detected, else None.
    - handoff_reason: a short string if this turn should escalate to a human, else None.
    """
    conversation = conversation_state.get_active_conversation(db, business_id, chat_id)
    history = conversation_state.get_recent_messages(db, business_id, conversation.id, MAX_EXCHANGES)
    contents = _to_contents(history)
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    system_instruction = _build_system_instruction(business_id, db, conversation.handed_off)

    try:
        reply = await _generate_reply(contents, system_instruction)
    except Exception:
        logger.exception("business_id=%s chat_id=%s: get_ai_reply failed", business_id, chat_id)
        return FALLBACK_REPLY, None, None, conversation

    conversation_state.add_message(db, business_id, conversation.id, "customer", user_message)
    conversation_state.add_message(db, business_id, conversation.id, "bot", reply)

    classification = await _classify(contents, reply)
    lead = classification.get("lead") if classification else None
    handoff_reason = _apply_conversation_flags(business_id, chat_id, conversation, classification)

    return reply, lead, handoff_reason, conversation
