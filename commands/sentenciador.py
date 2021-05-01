from telegram import Update, Bot
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from messages.messages import PunishmentMessage


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"

    def punish(self, message, **kwargs):
        return PunishmentMessage(message, **kwargs).transform()

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(update.message.reply_to_message.text),
        )
