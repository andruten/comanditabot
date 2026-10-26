import asyncio
from random import randint

from telegram import Bot, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, CommandHandler


class BaseCommandHandler(CommandHandler):
    COMMAND_NAME = None

    def __init__(self, *args, **kwargs):
        if self.COMMAND_NAME is None:
            raise NotImplementedError("'COMMAND_NAME' has wrong value.")
        super().__init__(self.COMMAND_NAME, self.process, *args, **kwargs)

    async def process(self, update: Update, context: CallbackContext) -> None:
        raise NotImplementedError("'process' method is not implemented!")


async def fake_typing(bot: Bot, chat_id: int, *, seconds: int | None = None) -> None:
    """Pretend the bot is typing and take a short pause before answering."""
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    if seconds is None:
        seconds = randint(1, 3)
    await asyncio.sleep(seconds)
