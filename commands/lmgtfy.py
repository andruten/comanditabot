import asyncio
import logging
import urllib.parse

from telegram import Bot, Update
from telegram.ext import CallbackContext

from clients.nlp import topic_extractor
from commands.base import BaseCommandHandler, fake_typing

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 200


class LmgtfyCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "lmgtfy"

    async def process(self, update: Update, context: CallbackContext) -> None:
        await fake_typing(context.bot, update.effective_chat.id)
        bot: Bot = context.bot
        try:
            text = update.message.reply_to_message.text
        except AttributeError:
            logger.info("/lmgtfy invoked without a quoted message")
            text = None
        if not (text or "").strip():
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="No puedo googlear sin citar un mensaje... 😢",
            )
            return
        # NER parsing is CPU-bound; keep the event loop free.
        topic = await asyncio.to_thread(topic_extractor.extract_topic, text)
        if not topic or topic.strip().lower() == text.strip().lower():
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="No sé qué googlear ahí... 😢",
            )
            return
        query = urllib.parse.quote_plus(topic[:MAX_QUERY_LENGTH])
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Te lo busco en Google... https://lmgtfy.com/?q={query}",
        )
