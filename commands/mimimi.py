import re

from telegram import ParseMode
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.bot import Bot

from commands.base import BaseCommandHandler


class MiMiMiCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "mimimi"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mimimis = {}

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        try:
            text = self.do_mimimi(update.message.reply_to_message.text)
            if update.message.reply_to_message.text == text:
                bot.send_message(
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.MARKDOWN,
                    text=self.mimimis.get(text) or text,
                )
                return
            self.mimimis[text] = update.message.reply_to_message.text
        except AttributeError:
            text = "No puedo hacer mimimi sin citar un mensaje... 😢"
        # "store" the translated value for joking purposes
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
