import re

from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.bot import Bot

from commands.base import BaseCommandHandler


class MiMiMiCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "mimimi"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        try:
            response = re.sub('[aeou]', 'i', update.message.reply_to_message.text, flags=re.I)
        except AttributeError:
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="No puedo hacer mimimi sin citar un mensaje... 😢",
            )
            return
        response = re.sub('[AEOU]', 'I', response, flags=re.I)
        response = re.sub('[áéóú]', 'í', response, flags=re.I)
        response = re.sub('[ÁÉÓÚ]', 'Í', response, flags=re.I)
        response = re.sub('[àèòù]', 'ì', response, flags=re.I)
        response = re.sub('[ÀÈÒÙ]', 'Ì', response, flags=re.I)
        response = re.sub('[äëöü]', 'ï', response, flags=re.I)
        response = re.sub('[ÄËÖÜ]', 'Ï', response, flags=re.I)

        bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
        )
