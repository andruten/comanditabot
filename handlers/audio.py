import logging

from telegram import Update, ParseMode, constants
from telegram.ext import MessageHandler, Filters, CallbackContext

from transcriber.audio_message_processor import AudioMessageTranscriberMixin

logger = logging.getLogger(__name__)


class AudioHandlerFactory(MessageHandler, AudioMessageTranscriberMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(Filters.voice & ~Filters.command, self.process, *args, **kwargs)

    def process(self, update: Update, context: CallbackContext):
        effective_chat_id = update.effective_chat.id
        message_id = update.message.message_id

        context.bot.send_chat_action(
            chat_id=effective_chat_id,
            action=constants.CHATACTION_TYPING,
        )

        text = self.transcribe(context, update.message.voice)

        context.bot.send_message(
            chat_id=effective_chat_id,
            text=text,
            reply_to_message_id=message_id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
