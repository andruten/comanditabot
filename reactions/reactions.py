import re
import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from random import choice, randint, random
from typing import List

import validators
from telegram import Bot, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, MessageHandler
from telegram.ext import filters

from feature_flags.store import FeatureFlagStore
from media_downloads.urls import supported_urls

from .constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from .exceptions import DoNothingException


class Reaction(ABC):
    reply = False
    probability = 100
    description = ""

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
    reaction_class: Reaction


class ReactionRegistry:
    @classmethod
    def register(cls, code: str, priority: int = 1):
        def wrapper(registry: Reaction):
            registries = cls.get_registries()
            registries.insert(priority, Registry(code=code, reaction_class=registry))
            setattr(cls, "__registries", registries)
            return registry

        return wrapper

    @classmethod
    def get_registries(cls) -> List[Registry]:
        registries = getattr(cls, "__registries", list())
        return registries

    @classmethod
    def process_message(
        cls, message: str, disabled_codes: Iterable[str] | None = None
    ) -> Reaction:
        disabled = set(disabled_codes) if disabled_codes else set()
        registry: Registry
        for registry in cls.get_registries():
            if registry.code in disabled:
                continue
            registry: Reaction = registry.reaction_class(message)
            if registry.trigger() and registry.shall_i_send_it():
                return registry
        raise DoNothingException()


@ReactionRegistry.register("digi", priority=5)
class DigiReaction(Reaction):
    description = 'Ladra ("Woof! Woof!") cuando alguien menciona a digi'

    def transform(self):
        return "Woof! Woof!"

    def trigger(self) -> bool:
        return "digi" in self.message.lower()


@ReactionRegistry.register("rajoy", priority=1)
class RajoyReaction(Reaction):
    description = "Frases de Rajoy cuando alguien menciona brey, rajoy o mariano"

    def transform(self):
        return choice(RAJOY_PHRASES)

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ["brey", "rajoy", "mariano"])


@ReactionRegistry.register("zapatero", priority=2)
class ZapateroReaction(Reaction):
    description = "Frases de Zapatero cuando alguien menciona zapatero o zp"

    def transform(self):
        return choice(ZAPATERO_PHRASES)

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ["zapatero", "zp"])


@ReactionRegistry.register("kids_alert", priority=3)
class KidsAlertReaction(Reaction):
    reply = True
    description = (
        "Kids Alert! cuando alguien menciona niño, niña, hijo, hija, papá o papi"
    )

    def transform(self):
        return "🚨🚨 Kids Alert! 🚨🚨"

    def trigger(self) -> bool:
        return any(
            x in self.message.lower()
            for x in ["niño", "niña", "hijo", "hija", "papá", "papi"]
        )


@ReactionRegistry.register("broken_group", priority=4)
class BrokenGroupReaction(Reaction):
    reply = True
    description = '"El grupo está roto" cuando alguien cuenta que estuvo en o fue a'

    def transform(self):
        return "Anda que avisas... El grupo está roto."

    def trigger(self) -> bool:
        return any(x in self.message.lower() for x in ["estuve en", "fui a"])


@ReactionRegistry.register("mimimi", priority=6)
class MiMiMiReaction(Reaction):
    probability = 1
    reply = True
    description = "Traduce el mensaje a mimimi (1% de las veces)"
    REPLACES = (
        ("[aeou]", "i"),
        ("[AEOU]", "I"),
        ("[áéóú]", "í"),
        ("[ÁÉÓÚ]", "Í"),
        ("[àèòù]", "ì"),
        ("[ÀÈÒÙ]", "Ì"),
        ("[äëöü]", "ï"),
        ("[ÄËÖÜ]", "Ï"),
        ("[âêôû]", "î"),
        ("[ÂÊÔÛ]", "Î"),
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


@ReactionRegistry.register("punishment", priority=0)
class PunishmentReaction(Reaction):
    probability = 10
    reply = True
    description = (
        "Sentencia aleatoria cuando alguien comparte una URL (10% de las veces)"
    )
    PUNISHMENTS = [
        "Esto tiene, por lo menos, 3 días.",
        "O sea, chao.",
        "Gilipollas tú, gilipollas tú y gilipollas tú.",
        "Perdona, ¿eres tonto?",
        "Mmmmmu tonnnto...",
    ]

    def transform(self):
        return choice(self.PUNISHMENTS)

    def trigger(self) -> bool:
        return validators.url(self.message)


class ReactionHandlerFactory(MessageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(filters.TEXT & ~filters.COMMAND, self.process, *args, **kwargs)

    async def process(self, update: Update, context: CallbackContext):
        if supported_urls(update.effective_message.text):
            return
        chat_id = update.effective_chat.id
        flags = FeatureFlagStore.from_bot_data(context)
        if flags.all_disabled(chat_id):
            return
        try:
            message_class = ReactionRegistry.process_message(
                update.effective_message.text,
                disabled_codes=flags.disabled_codes(chat_id),
            )
        except DoNothingException:
            pass
        else:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, action=ChatAction.TYPING
            )
            await asyncio.sleep(randint(1, 3))
            text = message_class.transform()
            if message_class.reply:
                # Reply to message
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action=ChatAction.TYPING,
                )
                await update.message.reply_text(text)
            else:
                bot: Bot = context.bot
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                )
