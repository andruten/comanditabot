from random import random, choice
import re

import validators
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CallbackContext

from .constants import RAJOY_PHRASES
from .exceptions import DoNothingException


class Message:

    def __init__(self, message, probability=20) -> None:
        super().__init__()
        self.message = message
        self.probability = probability
        self._shall_i_send_it()

    def _shall_i_send_it(self):
        # Only response with a PROBABILITY
        if random() > (self.probability / 100):
            raise DoNothingException()
        return True

    def send_as_reply(self):
        return False

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

    def send_as_reply(self):
        return True

    def transform(self):
        return self._do_mimimi()


class PunishmentMessage(Message):

    def send_as_reply(self):
        return True

    def transform(self):
        # TODO: Mix with PunisherCommandHandler
        return "Eso tiene, por lo menos, tres días."


def message_factory(message):
    if validators.url(message):
        return PunishmentMessage(message)
    if 'rajoy' in message.lower():
        return RajoyMessage(message, probability=100)
    return MiMiMiMessage(message, probability=1)


class MessageHandlerFactory(MessageHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(Filters.text & ~Filters.command, self.process, *args, **kwargs)

    def process(self, update: Update, context: CallbackContext):
        try:
            message_class = message_factory(update.message.text)
        except DoNothingException:
            pass
        else:
            text = message_class.transform()
            if message_class.send_as_reply():
                # Reply to message
                update.message.reply_text(text)
            else:
                bot: Bot = context.bot
                bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                )
