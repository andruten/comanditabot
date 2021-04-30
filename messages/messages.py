from random import randint

from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext
import validators


class DoNothingException(Exception):
    pass


class Message:

    def __init__(self, message) -> None:
        super().__init__()
        # Only response with a 20% of probability
        if randint(1, 5) != 1:
            raise DoNothingException()
        self.message = message

    def transform(self):
        raise NotImplementedError()


class PunishmentMessage(Message):

    def transform(self):
        return "Eso tiene, por lo menos, tres días."


def message_factory(message):
    if validators.url(message):
        return PunishmentMessage(message).transform()
    raise DoNothingException()


class MessageHandlerFactory(MessageHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(Filters.text & ~Filters.command, self.process, *args, **kwargs)

    def process(self, update: Update, _: CallbackContext):
        try:
            text = message_factory(update.message.text)
        except DoNothingException:
            pass
        else:
            # Reply to
            update.message.reply_text(text)
