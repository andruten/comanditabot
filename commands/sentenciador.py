from telegram import Bot, Update
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler, fake_typing
from reactions.reactions import PunishmentReaction


class PunisherCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "sentenciador"

    def punish(self):
        return PunishmentReaction().transform()

    async def process(self, update: Update, context: CallbackContext):
        await fake_typing(context.bot, update.effective_chat.id)
        bot: Bot = context.bot
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.punish(),
        )
