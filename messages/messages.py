from random import random, choice
import re

import validators
from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from .constants import RAJOY_PHRASES
from .exceptions import DoNothingException


class Message:

    def _shall_i_send_it(self):
        # Only response with a PROBABILITY
        if random() > (self.probability / 100):
            raise DoNothingException()
        return True

    def __init__(self, message, probability=20) -> None:
        super().__init__()
        self.message = message
        self.probability = probability
        self._shall_i_send_it()

    def transform(self):
        raise NotImplementedError()


class RajoyMessage(Message):

    def transform(self):
        return choice(RAJOY_PHRASES)


class MiMiMiMessage(Message):

    def _do_mimimi(self):
        text = re.sub('[aeou]', 'i', self.message)
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

    def transform(self):
        return self._do_mimimi()


class PunishmentMessage(Message):

    def transform(self):
        # TODO: Mix with PunisherCommandHandler
        return "Eso tiene, por lo menos, tres días."


def message_factory(message):
    if validators.url(message):
        return PunishmentMessage(message).transform()
    if 'rajoy' in message.lower():
        return RajoyMessage(message, probability=100).transform()
    return MiMiMiMessage(message, probability=1).transform()


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
