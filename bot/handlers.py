"""Telegram message handlers."""
from telegram import Update
from telegram.ext import ContextTypes

from bot import memory
from bot.ai import get_ai_reply


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to the customer using the AI brain, with conversation memory."""
    chat_id = update.effective_chat.id
    reply = await get_ai_reply(chat_id, update.message.text)
    await update.message.reply_text(reply)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear this chat's conversation history (/reset command)."""
    chat_id = update.effective_chat.id
    memory.clear_history(chat_id)
    await update.message.reply_text("ការសន្ទនាត្រូវបានលុបចោល។ ចាប់ផ្តើមថ្មីបានហើយ!")
