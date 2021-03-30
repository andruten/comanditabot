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
            text = update.message.reply_to_message.text
        except AttributeError:
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="No puedo hacer mimimi sin citar un mensaje... 😢",
            )
            return
        text = re.sub('[aeou]', 'i', text, flags=re.I)
        text = re.sub('[AEOU]', 'I', text, flags=re.I)
        text = re.sub('[áéóú]', 'í', text, flags=re.I)
        text = re.sub('[ÁÉÓÚ]', 'Í', text, flags=re.I)
        text = re.sub('[àèòù]', 'ì', text, flags=re.I)
        text = re.sub('[ÀÈÒÙ]', 'Ì', text, flags=re.I)
        text = re.sub('[äëöü]', 'ï', text, flags=re.I)
        text = re.sub('[ÄËÖÜ]', 'Ï', text, flags=re.I)

        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )
