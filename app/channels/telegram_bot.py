"""Wires Telegram updates to the DB-backed engine for one business's bot.

Ported from v1_legacy/main.py + bot/handlers.py. Running many of these
from one process (multi-bot) is a later build step — this builds and
runs a single Application for one business.
"""
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.db.session import SessionLocal
from app.services import conversation_state, handoff, leads
from app.services.ai import FALLBACK_REPLY, get_ai_reply

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to the customer using the AI brain, with memory, lead capture, and handoff."""
    business_id = context.application.bot_data["business_id"]
    owner_chat_id = context.application.bot_data["owner_chat_id"]
    chat_id = update.effective_chat.id
    customer_message = update.message.text

    db = SessionLocal()
    try:
        reply, lead, handoff_reason, conversation = await get_ai_reply(
            db, business_id, chat_id, customer_message
        )
        await update.message.reply_text(reply)

        if lead:
            await leads.process_lead(
                db,
                business_id,
                context.bot,
                owner_chat_id,
                conversation,
                name=lead.get("name", ""),
                phone=lead.get("phone", ""),
                interest=lead.get("interest", ""),
            )

        if handoff_reason:
            await handoff.notify_owner(
                db, business_id, context.bot, owner_chat_id, conversation, handoff_reason
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear this chat's conversation history and state (/reset command)."""
    business_id = context.application.bot_data["business_id"]
    chat_id = update.effective_chat.id

    db = SessionLocal()
    try:
        conversation_state.start_new_conversation(db, business_id, chat_id)
        conversation_state.clear_streak(business_id, chat_id)
        db.commit()
    finally:
        db.close()

    await update.message.reply_text("ការសន្ទនាត្រូវបានលុបចោល។ ចាប់ផ្តើមថ្មីបានហើយ!")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the sender's numeric Telegram chat ID (/myid command)."""
    await update.message.reply_text(str(update.effective_chat.id))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Safety net: log any unexpected exception and apologize instead of crashing."""
    business_id = context.application.bot_data.get("business_id")
    logger.error(
        "business_id=%s: unhandled exception while processing an update",
        business_id,
        exc_info=context.error,
    )
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(FALLBACK_REPLY)
        except Exception:
            logger.exception("business_id=%s: failed to send the fallback apology", business_id)


def build_application(token: str, business_id: int, owner_chat_id: int) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data["business_id"] = business_id
    app.bot_data["owner_chat_id"] = owner_chat_id
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(on_error)
    return app
