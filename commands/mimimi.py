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
            text = self.do_mimimi(update.message.reply_to_message.text)
        except AttributeError:
            text = "No puedo hacer _mimimi_ sin citar un mensaje... 😢"

        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def do_mimimi(self, text):
        text = re.sub('[aeou]', 'i', text)
        text = re.sub('[AEOU]', 'I', text)
        text = re.sub('[áéóú]', 'í', text)
        text = re.sub('[ÁÉÓÚ]', 'Í', text)
        text = re.sub('[àèòù]', 'ì', text)
        text = re.sub('[ÀÈÒÙ]', 'Ì', text)
        text = re.sub('[äëöü]', 'ï', text)
        text = re.sub('[ÄËÖÜ]', 'Ï', text)
        text = re.sub('[âêôû]', 'î', text)
        text = re.sub('[ÂÊÔÛ]', 'Î', text)
        return text
