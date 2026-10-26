import logging

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler, fake_typing
from reactions.reactions import MiMiMiReaction

logger = logging.getLogger(__name__)


class MiMiMiCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "mimimi"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mimimis = {}

    async def process(self, update: Update, context: CallbackContext):
        await fake_typing(context.bot, update.effective_chat.id)
        bot: Bot = context.bot
        try:
            text = self.do_mimimi(update.message.reply_to_message.text)
            if update.message.reply_to_message.text == text:
                logger.info("Replying an already mimimied message")
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.MARKDOWN,
                    text=self.mimimis.get(text) or text,
                )
                return
            self.mimimis[text] = update.message.reply_to_message.text
        except AttributeError:
            logger.warning("/mimimi invoked without a quoted message")
            text = "No puedo hacer mimimi sin citar un mensaje... 😢"
        # "store" the translated value for joking purposes
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def do_mimimi(self, text):
        return MiMiMiReaction(text, probability=100).transform()
