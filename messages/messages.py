import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from random import choice, randint, random
from typing import List

import validators
from telegram import Bot, Update
from telegram.ext import CallbackContext, Filters, MessageHandler

from .constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from .exceptions import DoNothingException


class Message(ABC):
    reply = False
    probability = 100

    def __init__(self, message=None, probability=None) -> None:
        super().__init__()
        self.message = message
        self.probability = probability if probability else self.probability
        self.shall_i_send_it()

    def shall_i_send_it(self) -> bool:
        # Only response with a PROBABILITY
        return random() < (self.probability / 100)

    @abstractmethod
    def transform(self) -> str:
        pass

    @abstractmethod
    def trigger(self) -> bool:
        pass


@dataclass
class Registry:
    code: str
    message_class: Message


class MessageRegistry:

    @classmethod
    def register(cls, code: str, priority: int = 1):
        def wrapper(registry: Message):
            registries = cls.get_registries()
            registries.insert(priority, Registry(code=code, message_class=registry))
            setattr(cls, '__registries', registries)
            return registry

        return wrapper

    @classmethod
    def get_registries(cls) -> List[Registry]:
        registries = getattr(cls, '__registries', list())
        return registries

    @classmethod
    def process_message(cls, message: str) -> Message:
        registry: Registry
        for registry in cls.get_registries():
            registry: Message = registry.message_class(message)
            if registry.trigger() and registry.shall_i_send_it():
                return registry
        raise DoNothingException()


@MessageRegistry.register('digi', priority=5)
class DigiMessage(Message):

    def transform(self):
        return 'Woof! Woof!'

    def trigger(self) -> bool:
        return 'digi' in self.message.lower()


@MessageRegistry.register('rajoy', priority=1)
class RajoyMessage(Message):

    def transform(self):
        return choice(RAJOY_PHRASES)

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ['brey', 'rajoy', 'mariano'])


@MessageRegistry.register('zapatero', priority=2)
class ZapateroMessage(Message):

    def transform(self):
        return choice(ZAPATERO_PHRASES)

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ['zapatero', 'zp'])


@MessageRegistry.register('kids_alert', priority=3)
class KidsAlertMessage(Message):
    reply = True

    def transform(self):
        return '🚨🚨 Kids Alert! 🚨🚨'

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ['niño', 'niña', 'hijo', 'hija', 'papá', 'papi'])


@MessageRegistry.register('broken_group', priority=4)
class BrokenGroupMessage(Message):
    reply = True

    def transform(self):
        return 'Anda que avisas... El grupo está roto.'

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ['estuve en', 'fui a'])


@MessageRegistry.register('mimimi', priority=6)
class MiMiMiMessage(Message):
    probability = 1
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

    def trigger(self) -> bool:
        return True


@MessageRegistry.register('punishment', priority=0)
class PunishmentMessage(Message):
    probability = 10
    reply = True
    PUNISHMENTS = [
        'Esto tiene, por lo menos, 3 días.',
        'O sea, chao.',
        'Gilipollas tú, gilipollas tú y gilipollas tú.',
        'Perdona, ¿eres tonto?',
        'Mmmmmu tonnnto...',
    ]

    def transform(self):
        return choice(self.PUNISHMENTS)

    def trigger(self) -> bool:
        return validators.url(self.message)


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
            message_class = MessageRegistry.process_message(update.message.text)
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
