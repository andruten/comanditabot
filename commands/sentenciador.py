from random import choice

from telegram import Update, Bot
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"
    PUNISHMENTS = [
        "Esto tiene, por lo menos, 3 días.",
        "O sea, chao.",
        "Gilipollas tú, gilipollas tú y gilipollas tú.",
        "Perdona, ¿eres tonto?",
        "Mmmmmu tonnnto...",
    ]

    def punish(self):
        return choice(self.PUNISHMENTS)

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
