from random import random, choice

import validators
from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from .constants import RAJOY_PHRASES
from .exceptions import DoNothingException


class Message:
    PROBABILITY = 20

    def _shall_i_send_it(self):
        # Only response with a PROBABILITY
        if random() < self.PROBABILITY / 100.:
            raise DoNothingException()
        return True

    def __init__(self, message) -> None:
        super().__init__()
        self._shall_i_send_it()
        self.message = message

    def transform(self):
        raise NotImplementedError()


class RajoyMessage(Message):
    PROBABILITY = 100

    def transform(self):
        return choice(RAJOY_PHRASES)


class PunishmentMessage(Message):

    def transform(self):
        # TODO: Mix with PunisherCommandHandler
        return "Eso tiene, por lo menos, tres días."


def message_factory(message):
    if validators.url(message):
        return PunishmentMessage(message).transform()
    if 'rajoy' in message.lower():
        return RajoyMessage(message).transform()
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
            # Reply to message
            update.message.reply_text(text)
