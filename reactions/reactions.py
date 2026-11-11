import asyncio
import logging
import re
import urllib.parse
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from random import choice, randint, random
from typing import ClassVar

import validators
from telegram import Bot, Message, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, MessageHandler, filters

from clients.nlp import topic_extractor
from feature_flags.store import FeatureFlagStore
from media_downloads.urls import supported_urls

from .constants import (
    MIMIMI_REACTION_PROBABILITY,
    PUNISHMENT_REACTION_PROBABILITY,
    RAJOY_PHRASES,
    ZAPATERO_PHRASES,
)
from .exceptions import DoNothingException
from .history import chat_history

logger = logging.getLogger(__name__)


@dataclass
class ReactionContext:
    """Conversation context a message may react to.

    ``reply_text`` is the text of the message being replied to, if any, and
    ``history`` holds the chat's most recent texts (oldest first) as recorded
    by ``reactions.history``.
    """

    reply_text: str | None = None
    history: list[str] = field(default_factory=list)


class Reaction(ABC):
    reply = False
    probability = 100
    description = ""

    def __init__(
        self, message=None, probability=None, context: ReactionContext | None = None
    ) -> None:
        super().__init__()
        self.message = message
        self.probability = probability if probability else self.probability
        self.context = context

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
class Registration:
    code: str
    priority: int
    reaction_class: type["Reaction"]


class ReactionRegistry:
    _registries: ClassVar[list[Registration]] = []

    @classmethod
    def register(cls, code: str, priority: int = 1):
        def wrapper(reaction_class: type[Reaction]) -> type[Reaction]:
            cls._registries.append(
                Registration(
                    code=code, priority=priority, reaction_class=reaction_class
                )
            )
            cls._registries.sort(key=lambda registration: registration.priority)
            return reaction_class

        return wrapper

    @classmethod
    def get_registries(cls) -> list[Registration]:
        return list(cls._registries)

    @classmethod
    def process_message(
        cls,
        message: str | None,
        disabled_codes: Iterable[str] | None = None,
        context: ReactionContext | None = None,
    ) -> Reaction:
        disabled = set(disabled_codes) if disabled_codes else set()
        for registration in cls.get_registries():
            if registration.code in disabled:
                continue
            reaction = registration.reaction_class(message, context=context)
            if reaction.trigger() and reaction.shall_i_send_it():
                return reaction
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


# Priority 6: after the deterministic joke reactions but before mimimi's dice
# roll (7), so a "no sé" message is not randomly consumed by a mimimi translation.
@ReactionRegistry.register("lmgtfy", priority=6)
class LmgtfyReaction(Reaction):
    reply = True
    description = (
        '"Let me google that for you" cuando alguien está perdido: busca en '
        "Google el mensaje al que responde, el tema de los últimos mensajes del "
        "chat o lo que el propio mensaje menciona"
    )
    # Ignorance statements aimed at the *current topic*, not generic "I don't
    # know" phrases: "no sé si vendré mañana" or "el que no sabe es porque no
    # quiere" must not reach the LLM.
    TRIGGERS: ClassVar[list] = [
        "no sé de qué",
        "no sé qué es",
        "no sé qué significa",
        "no sé ni qué",
        "no sé por dónde",
        "no tengo ni idea",
        "ni idea",
        "no entiendo",
        "no pillo",
        "no pilláis",
        "no me entero",
        "de qué habláis",
        "de qué hablas",
        "de qué hablamos",
        "de qué va eso",
        "qué es eso",
        "qué es esto",
        "no tengo contexto",
        "necesito contexto",
        "dame contexto",
        "dadme contexto",
        "ponme en contexto",
        "ponme al día",
        "ponedme al día",
        "me pierdo",
        "estoy perdido",
        "estoy perdida",
    ]
    NO_TOPIC_REPLY = "Pues a Google, que no muerde."
    MAX_QUERY_LENGTH: ClassVar[int] = 200
    REPLY_MIN_WORDS: ClassVar[int] = 3
    MIN_TOPIC_WORDS: ClassVar[int] = 4
    MIN_TOPIC_LENGTH: ClassVar[int] = 3
    resolved_query = None

    async def prepare(self) -> None:
        """Hook the factory calls before ``transform()``.

        Asks the offline spaCy extractor for the exact topic worth googling;
        any failure keeps ``resolved_query`` empty and the deterministic
        topic selection chain stays in charge. Without conversation material
        there is nothing to pick from, and while the model is still loading
        the reply must not wait for it: the fallback chain answers and the
        model warms up in the background.
        """
        if self.context is None or not self._has_context():
            return
        if not topic_extractor.is_ready:
            logger.info("Topic extractor still loading; using the fallback chain")
            asyncio.create_task(asyncio.to_thread(topic_extractor.ensure_loaded))
            return
        try:
            # NER parsing is CPU-bound; keep the event loop free.
            resolved = await asyncio.to_thread(
                topic_extractor.extract_topic,
                self.message,
                self.context.reply_text,
                self.context.history,
            )
        except Exception as error:  # noqa: BLE001 - failures degrade to None
            logger.warning("Topic extraction failed: %s", error)
            return
        if (
            resolved
            and (self.message or "").strip().lower() != resolved.strip().lower()
        ):
            self.resolved_query = resolved

    def _has_context(self) -> bool:
        return bool((self.context.reply_text or "").strip()) or bool(
            self.context.history
        )

    def transform(self):
        if self.resolved_query:
            return self._lmgtfy_reply(self.resolved_query)
        return self._lmgtfy_reply(self._clean_topic(self._select_topic()))

    def _lmgtfy_reply(self, topic: str) -> str:
        cleaned = self._clean_topic(topic)
        if len(cleaned) < self.MIN_TOPIC_LENGTH:
            return self.NO_TOPIC_REPLY
        query = urllib.parse.quote_plus(self._truncate_to_word_limit(cleaned))
        return f"Te lo busco en Google... https://lmgtfy.com/?q={query}"

    def trigger(self) -> bool:
        message = self.message.lower()
        return any(phrase in message for phrase in self.TRIGGERS)

    # --- topic selection ---------------------------------------------------

    def _select_topic(self) -> str:
        if self.context is None:
            return self._topic_from_message()
        replied = self.context.reply_text or ""
        if self._qualifies(replied, min_words=self.REPLY_MIN_WORDS):
            return replied
        for text in reversed(self.context.history):
            if self._qualifies(text, min_words=self.MIN_TOPIC_WORDS):
                return text
        combined = " ".join(
            text for text in self.context.history[-3:] if self._is_searchable(text)
        )
        if len(combined.split()) >= 2:
            return combined
        return self._topic_from_message()

    def _topic_from_message(self) -> str:
        if not self.message:
            return ""
        lowered = self.message.lower()
        for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
            index = lowered.find(trigger)
            if index != -1:
                return self.message[index + len(trigger) :]
        return ""

    def _clean_topic(self, topic: str) -> str:
        topic = topic.strip(" \t:;,.!¡?¿-_")
        # Drop accumulated ignorance phrases left after slicing, e.g. turning
        # "no tengo ni idea, no sé de qué va" into "de qué va".
        lowered = topic.lower()
        changed = True
        while changed:
            changed = False
            for trigger in sorted(self.TRIGGERS, key=len, reverse=True):
                if lowered.startswith(trigger):
                    topic = topic[len(trigger) :].strip(" \t:;,.!¡?¿-_")
                    lowered = topic.lower()
                    changed = True
                    break
        return topic

    def _truncate_to_word_limit(self, topic: str) -> str:
        if len(topic) <= self.MAX_QUERY_LENGTH:
            return topic
        truncated = topic[: self.MAX_QUERY_LENGTH]
        return truncated.rsplit(" ", 1)[0]

    def _qualifies(self, text: str, min_words: int) -> bool:
        return self._is_searchable(text) and len(text.split()) >= min_words

    @staticmethod
    def _is_searchable(text: str | None) -> bool:
        text = (text or "").strip()
        if not text or text.startswith("/"):
            return False
        return not any(
            token.startswith(("http://", "https://", "www."))
            for token in text.lower().split()
        )


@ReactionRegistry.register("mimimi", priority=7)
class MiMiMiReaction(Reaction):
    probability = MIMIMI_REACTION_PROBABILITY
    reply = True
    description = "Traduce el mensaje a mimimi (configurable, 1% por defecto)"
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
    probability = PUNISHMENT_REACTION_PROBABILITY
    reply = True
    description = "Sentencia aleatoria cuando alguien comparte una URL (configurable, 10% por defecto)"
    PUNISHMENTS: ClassVar[list] = [
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
        super().__init__(
            filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE,
            self.process,
            *args,
            **kwargs,
        )

    async def process(self, update: Update, context: CallbackContext) -> None:
        if supported_urls(update.effective_message.text):
            return
        chat_id = update.effective_chat.id
        message_text = update.effective_message.text
        reaction_context = ReactionContext(
            reply_text=replied_to_text(update.effective_message),
            history=chat_history.recent(chat_id),
        )
        flags = FeatureFlagStore.from_bot_data(context)
        if flags.all_disabled(chat_id):
            return
        try:
            message_class = ReactionRegistry.process_message(
                message_text,
                disabled_codes=flags.disabled_codes(chat_id),
                context=reaction_context,
            )
        except DoNothingException:
            pass
        else:
            logger.info("Reaction %s triggered", type(message_class).__name__)
            # Reactions may define an async prepare() hook to enrich themselves
            # (e.g. the LMGTFY reaction asks the spaCy extractor for the topic).
            prepare = getattr(message_class, "prepare", None)
            if prepare:
                await prepare()
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
                await update.effective_message.reply_text(text)
            else:
                bot: Bot = context.bot
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                )
        finally:
            # Record after the reaction is chosen, so the reaction does not see
            # its own trigger message as conversation context.
            chat_history.add(chat_id, message_text)


def replied_to_text(message: Message) -> str | None:
    replied = getattr(message, "reply_to_message", None)
    if replied is None:
        return None
    return (replied.text or "").strip() or None
