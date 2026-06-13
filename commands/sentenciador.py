import asyncio
from random import randint

from telegram import Bot, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from reactions.reactions import PunishmentReaction


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"

    def punish(self):
        return PunishmentReaction().transform()

    async def process(self, update: Update, context: CallbackContext):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        await asyncio.sleep(randint(1, 3))
        bot: Bot = context.bot
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
