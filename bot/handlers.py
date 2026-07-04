"""Telegram message handlers."""
from telegram import Update
from telegram.ext import ContextTypes

from bot.ai import get_ai_reply


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to the customer using the AI brain."""
    reply = await get_ai_reply(update.message.text)
    await update.message.reply_text(reply)
