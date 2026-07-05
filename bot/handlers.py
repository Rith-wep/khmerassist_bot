"""Telegram message handlers."""
from telegram import Update
from telegram.ext import ContextTypes

from bot import conversation_log, handoff, leads, memory
from bot.ai import get_ai_reply


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to the customer using the AI brain, with memory, lead capture, and handoff."""
    chat_id = update.effective_chat.id
    customer_message = update.message.text

    reply, lead, handoff_reason = await get_ai_reply(chat_id, customer_message)
    await update.message.reply_text(reply)

    conversation_log.log_exchange(chat_id, customer_message, reply)

    if lead:
        await leads.process_lead(
            bot=context.bot,
            chat_id=chat_id,
            name=lead.get("name", ""),
            phone=lead.get("phone", ""),
            interest=lead.get("interest", ""),
        )

    if handoff_reason:
        await handoff.notify_owner(bot=context.bot, chat_id=chat_id, reason=handoff_reason)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear this chat's conversation history and state (/reset command)."""
    chat_id = update.effective_chat.id
    memory.clear_history(chat_id)
    await update.message.reply_text("ការសន្ទនាត្រូវបានលុបចោល។ ចាប់ផ្តើមថ្មីបានហើយ!")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the sender's numeric Telegram chat ID (/myid command)."""
    await update.message.reply_text(str(update.effective_chat.id))
