from random import choice

from telegram import Update, Bot
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        punishments = [
            "Esto tiene, por lo menos, 3 días.",
            "O sea, chao.",
        ]
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=choice(punishments),
        )
