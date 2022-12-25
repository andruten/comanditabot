from telegram import Update, Bot
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from handlers.messages import PunishmentMessage


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"

    def punish(self):
        return PunishmentMessage().transform()

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
