from abc import ABCMeta, abstractmethod
from datetime import datetime
from random import random, choice, randint
import re

import validators
from telegram import Update, Bot
from telegram.ext import MessageHandler, Filters, CallbackContext

from .constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from .exceptions import DoNothingException


KIDS_ALERT = ['niño', 'niña', 'hijo', 'hija', 'papá', 'papi', 'nene', 'kid', 'sobri', 'peque', 'bebé', 'mocoso']


class Message(metaclass=ABCMeta):
    reply = False

    def __init__(self, message=None, probability=100) -> None:
        super().__init__()
        self.message = message
        self.probability = probability
        self._shall_i_send_it()

    def _shall_i_send_it(self):
        # Only response with a PROBABILITY
        if random() > (self.probability / 100):
            raise DoNothingException()
        return True

    @abstractmethod
    def transform(self):
        pass


class DigiMessage(Message):

    def transform(self):
        return 'Woof! Woof!'


class RajoyMessage(Message):

    def transform(self):
        return choice(RAJOY_PHRASES)


class ZapateroMessage(Message):

    def transform(self):
        return choice(ZAPATERO_PHRASES)


class KidsAlertMessage(Message):
    reply = True

    def transform(self):
        return '🚨🚨 Kids Alert! 🚨🚨'


class MiMiMiMessage(Message):
    reply = True
    REPLACES = (
        ('[aeou]', 'i'),
        ('[AEOU]', 'I'),
        ('[áéóú]', 'í'),
        ('[ÁÉÓÚ]', 'Í'),
        ('[àèòù]', 'ì'),
        ('[ÀÈÒÙ]', 'Ì'),
        ('[äëöü]', 'ï'),
        ('[ÄËÖÜ]', 'Ï'),
        ('[âêôû]', 'î'),
        ('[ÂÊÔÛ]', 'Î'),
    )

    def _do_mimimi(self):
        text = self.message
        for key, value in self.REPLACES:
            text = re.sub(key, value, text)
        return text

    def transform(self):
        return self._do_mimimi()


class PunishmentMessage(Message):
    reply = True
    PUNISHMENTS = [
        'Esto tiene, por lo menos, 3 días.',
        'O sea, chao.',
        'Gilipollas tú, gilipollas tú y gilipollas tú.',
        'Perdona, ¿eres tonto?',
        'Mmmmmu tonnnto...',
        '¡Me estáis poniendo de una mala hostia...!',
    ]

    def transform(self):
        return choice(self.PUNISHMENTS)


def message_factory(message, probability=None):
    if validators.url(message):
        if not probability:
            probability = 10
        return PunishmentMessage(message, probability=probability)
    if any(x in message.lower() for x in ['brey', 'rajoy', 'mariano']):
        return RajoyMessage(message)
    if any(x in message.lower() for x in ['zapatero', 'zp']):
        return ZapateroMessage(message)
    if any(x in message.lower() for x in KIDS_ALERT):
        return KidsAlertMessage()
    if 'digi' in message.lower():
        return DigiMessage(message)
    if not probability:
        probability = 1
    return MiMiMiMessage(message, probability=probability)


class MessageHandlerFactory(MessageHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(Filters.text & ~Filters.command, self.process, *args, **kwargs)
        self.daily_counter = {}

    def grumpy_digi(self, update: Update, context: CallbackContext):
        today = datetime.utcnow().today().strftime('%Y-%m-%d')
        if today not in self.daily_counter:
            self.daily_counter[today] = {
                'messages': 0,
                'alert_when': randint(200, 300)
            }
        self.daily_counter[today]['messages'] += 1
        if self.daily_counter[today].get('messages') == self.daily_counter[today].get('alert_when'):
            bot: Bot = context.bot
            messages_count = self.daily_counter[today].get('messages')
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'¡La virgen, lo que escribís! {messages_count} mensajes',
            )

    def process(self, update: Update, context: CallbackContext):
        self.grumpy_digi(update, context)
        try:
            message_class = message_factory(update.message.text)
        except DoNothingException:
            pass
        else:
            text = message_class.transform()
            if message_class.reply:
                # Reply to message
                update.message.reply_text(text)
            else:
                bot: Bot = context.bot
                bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                )
