import asyncio
from random import randint

from telegram import Bot, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler
from reactions.reactions import MiMiMiReaction


class MiMiMiCommandHandler(BaseCommandHandler):
    COMMAND_NAME = 'mimimi'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mimimis = {}

    async def process(self, update: Update, context: CallbackContext):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(randint(1, 3))
        bot: Bot = context.bot
        try:
            text = self.do_mimimi(update.message.reply_to_message.text)
            if update.message.reply_to_message.text == text:
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.MARKDOWN,
                    text=self.mimimis.get(text) or text,
                )
                return
            self.mimimis[text] = update.message.reply_to_message.text
        except AttributeError:
            text = 'No puedo hacer mimimi sin citar un mensaje... 😢'
        # "store" the translated value for joking purposes
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def do_mimimi(self, text):
        return MiMiMiReaction(text, probability=100).transform()
