from telegram import Bot, Update
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from reactions.reactions import PunishmentReaction


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = 'sentenciador'

    def punish(self):
        return PunishmentReaction().transform()

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
