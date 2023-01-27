from random import randint
from time import sleep

from telegram import Bot, ChatAction, Update
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from reactions.reactions import PunishmentReaction


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = 'sentenciador'

    def punish(self):
        return PunishmentReaction().transform()

    def process(self, update: Update, context: CallbackContext):
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        sleep(randint(1, 3))
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
