from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext


async def ensure_chat_admin(update: Update, context: CallbackContext) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return False
    if chat.type == ChatType.PRIVATE:
        return True
    administrators = await context.bot.get_chat_administrators(chat.id)
    return any(administrator.user.id == user.id for administrator in administrators)
