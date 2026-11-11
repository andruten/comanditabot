import asyncio
import urllib.parse
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from telegram import Chat, Message, Update

from reactions.constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from reactions.history import chat_history
from reactions.reactions import (
    BrokenGroupReaction,
    DigiReaction,
    KidsAlertReaction,
    LmgtfyReaction,
    MiMiMiReaction,
    PunishmentReaction,
    RajoyReaction,
    ReactionContext,
    ReactionHandlerFactory,
    ReactionRegistry,
    ZapateroReaction,
)


def test_rajoy_message():
    message_handler = RajoyReaction()
    assert message_handler.reply is False
    assert message_handler.transform() in RAJOY_PHRASES


def test_zapatero_message():
    message_handler = ZapateroReaction()
    assert message_handler.reply is False
    assert message_handler.transform() in ZAPATERO_PHRASES


def test_mimimi_message():
    message = "This is a test message"
    message_handler = MiMiMiReaction(message=message)
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == "This is i tist missigi"


def test_punishent_message():
    message_handler = PunishmentReaction()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message in message_handler.PUNISHMENTS


def test_kids_alert_message():
    message_handler = KidsAlertReaction()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == "🚨🚨 Kids Alert! 🚨🚨"


def test_message_broken_group():
    broken_group_handler = BrokenGroupReaction()
    assert broken_group_handler.reply is True
    transformed_message = broken_group_handler.transform()
    assert transformed_message == "Anda que avisas... El grupo está roto."


def test_lmgtfy_message():
    message = "No sé qué es un nodo Kubernetes"
    lmgtfy_handler = LmgtfyReaction(message=message)
    assert lmgtfy_handler.reply is True
    assert lmgtfy_handler.trigger() is True
    assert lmgtfy_handler.transform() == (
        "Te lo busco en Google... https://lmgtfy.com/?q=un+nodo+Kubernetes"
    )


def test_lmgtfy_uses_the_replied_message_as_topic():
    lmgtfy_handler = LmgtfyReaction(
        message="No sé de qué habláis",
        context=ReactionContext(
            reply_text="Qué buena banda es Angine de Poitrine",
            history=["Sí, me encantan"],
        ),
    )
    transformed_message = lmgtfy_handler.transform()
    assert "Angine+de+Poitrine" in transformed_message
    assert "encantan" not in transformed_message


def test_lmgtfy_skips_short_banter_and_picks_the_last_substantial_message():
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué habláis",
        context=ReactionContext(
            history=[
                "¿Alguien conoce Angine de Poitrine?",
                "Sí, me encantan",
            ]
        ),
    )
    assert "Angine+de+Poitrine" in lmgtfy_handler.transform()


def test_lmgtfy_ignores_commands_and_links_in_the_history():
    lmgtfy_handler = LmgtfyReaction(
        message="no pillo nada",
        context=ReactionContext(
            history=[
                "/star",
                "mira esto https://example.com/x",
                "Qué buena banda es Angine de Poitrine",
            ]
        ),
    )
    assert "Angine+de+Poitrine" in lmgtfy_handler.transform()


def test_lmgtfy_combines_recent_short_messages_as_a_last_resort():
    lmgtfy_handler = LmgtfyReaction(
        message="ni idea de lo que decís",
        context=ReactionContext(history=["iones", "fantasmas"]),
    )
    assert "iones+fantasmas" in lmgtfy_handler.transform()


@pytest.mark.parametrize(
    "context",
    [None, ReactionContext()],
)
def test_lmgtfy_falls_back_to_the_message_topic(context):
    lmgtfy_handler = LmgtfyReaction(
        message="No sé qué es un nodo Kubernetes", context=context
    )
    assert "un+nodo+Kubernetes" in lmgtfy_handler.transform()


@pytest.mark.parametrize(
    "message,context",
    [
        ("Ni idea", None),
        ("Ni idea", ReactionContext()),
        ("No sé", None),
    ],
)
def test_lmgtfy_replies_without_link_when_there_is_nothing_to_search(message, context):
    lmgtfy_handler = LmgtfyReaction(message=message, context=context)
    assert lmgtfy_handler.transform() == LmgtfyReaction.NO_TOPIC_REPLY


@pytest.mark.parametrize(
    "message",
    [
        "No sé de qué habláis",
        "no sé de qué va la peli",
        "No sé qué es un nodo Kubernetes",
        "no sé qué significa ese meme",
        "No sé ni qué estáis contando",
        "No sé por dónde va la cosa",
        "No tengo ni idea",
        "Ni idea",
        "ni idea de la peli",
        "no pillo",
        "no pillo nada de esto",
        "No pilláis nada",
        "No me entero del asunto",
        "No entiendo el chiste",
        "no entiendo nada",
        "¿De qué habláis?",
        "de qué hablas",
        "¿De qué hablamos?",
        "De qué va eso",
        "¿Qué es eso?",
        "¿Qué es esto?",
        "no tengo contexto",
        "necesito contexto",
        "dame contexto",
        "dadme contexto porfa",
        "ponme en contexto",
        "ponme al día",
        "ponedme al día de esto",
        "me pierdo",
        "me pierdo con el argumento",
        "estoy perdido",
        "estoy perdida con este tema",
        "Hostia, no sé qué es eso",
    ],
)
def test_lmgtfy_triggers_on_being_lost_phrases(message):
    assert LmgtfyReaction(message=message).trigger() is True


@pytest.mark.parametrize(
    "message",
    [
        "Hoy hace sol",
        "El nodo Kubernetes está caído",
        "No es lo mismo",
        "No sé si vendré mañana",
        "no sé si os apetece tener la final",
        "El que no sabe es porque no quiere",
        "El tío no sabe de qué va",
        "No sabe ni su nombre",
        "No sabía yo",
        "No sabéis nada de esto",
        "No sabemos",
        "No sabe nada del proyecto",
        "No lo sé",
        "No sé",
        "No conoce este bar",
        "Yo no conozco la respuesta",
        "No conozco ninguna de las dos",
        "No sé qué cenar hoy",
        "una idea genial",
        "Dame una idea para el finde",
        "El contexto histórico de la novela es fascinante",
    ],
)
def test_lmgtfy_does_not_trigger_on_other_messages(message):
    assert LmgtfyReaction(message=message).trigger() is False


def test_lmgtfy_strips_ignorance_phrases_left_in_the_topic():
    lmgtfy_handler = LmgtfyReaction(
        message="no tengo ni idea, no sé de qué va esto", context=ReactionContext()
    )
    query = lmgtfy_handler.transform().split("?q=", 1)[1]
    unquoted = urllib.parse.unquote_plus(query)
    assert unquoted == "va esto"
    assert "no sé" not in unquoted.lower()


def test_lmgtfy_transform_truncates_long_topics_on_word_boundaries():
    message = "No sé qué es " + "aa " * 200
    transformed_message = LmgtfyReaction(message=message).transform()
    query = transformed_message.split("?q=", 1)[1]
    # Trims back to the last whole word that fits in 200 characters.
    assert urllib.parse.unquote_plus(query) == " ".join(["aa"] * 66)


def test_process_message_passes_context_to_reactions():
    reaction = ReactionRegistry.process_message(
        "No sé de qué habláis",
        context=ReactionContext(reply_text="¿Alguien conoce Angine de Poitrine?"),
    )
    assert isinstance(reaction, LmgtfyReaction)
    assert "Angine+de+Poitrine" in reaction.transform()


def test_lmgtfy_transform_prefers_the_query_resolved_by_the_extractor():
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué va", context=ReactionContext()
    )
    lmgtfy_handler.resolved_query = "Angine de Poitrine"
    assert lmgtfy_handler.transform() == (
        "Te lo busco en Google... https://lmgtfy.com/?q=Angine+de+Poitrine"
    )


class StubTopicExtractor:
    def __init__(self, topic="Angine de Poitrine", error=None, ready=True):
        self.topic = topic
        self.error = error
        self.ready = ready
        self.calls = []
        self.warmed_up = False

    @property
    def is_ready(self):
        return self.ready

    def ensure_loaded(self):
        self.warmed_up = True

    def extract_topic(self, message, reply_text=None, history=()):
        assert self.ready, "a loading extractor must not be consulted"
        self.calls.append((message, reply_text, list(history)))
        if self.error:
            raise self.error
        return self.topic


@pytest.mark.asyncio
async def test_lmgtfy_prepare_asks_the_extractor_for_the_topic(monkeypatch):
    stub = StubTopicExtractor()
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué habláis",
        context=ReactionContext(
            reply_text="Qué buena banda es Angine de Poitrine",
            history=["Sí, me encantan"],
        ),
    )

    await lmgtfy_handler.prepare()

    assert lmgtfy_handler.resolved_query == "Angine de Poitrine"
    assert stub.calls == [
        (
            "no sé de qué habláis",
            "Qué buena banda es Angine de Poitrine",
            ["Sí, me encantan"],
        )
    ]


@pytest.mark.asyncio
async def test_lmgtfy_prepare_ignores_the_extractor_repeating_the_message(monkeypatch):
    stub = StubTopicExtractor(topic="No sé de qué va")
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué va", context=ReactionContext()
    )

    await lmgtfy_handler.prepare()

    assert lmgtfy_handler.resolved_query is None


@pytest.mark.asyncio
async def test_lmgtfy_prepare_skips_the_extractor_without_conversation_material(
    monkeypatch,
):
    stub = StubTopicExtractor()
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué habláis", context=ReactionContext()
    )

    await lmgtfy_handler.prepare()

    assert stub.calls == []
    assert lmgtfy_handler.resolved_query is None


@pytest.mark.asyncio
async def test_lmgtfy_prepare_skips_the_extractor_without_context():
    lmgtfy_handler = LmgtfyReaction(message="no sé de qué va")

    await lmgtfy_handler.prepare()

    assert lmgtfy_handler.resolved_query is None


@pytest.mark.asyncio
async def test_lmgtfy_prepare_degrades_when_the_extractor_fails(monkeypatch):
    stub = StubTopicExtractor(error=RuntimeError("boom"))
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué va",
        context=ReactionContext(history=["tema interesante del grupo"]),
    )

    await lmgtfy_handler.prepare()

    assert lmgtfy_handler.resolved_query is None


@pytest.mark.asyncio
async def test_lmgtfy_prepare_skips_the_extractor_while_it_is_loading(monkeypatch):
    stub = StubTopicExtractor(ready=False)
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    lmgtfy_handler = LmgtfyReaction(
        message="no sé de qué va",
        context=ReactionContext(history=["tema interesante del grupo"]),
    )

    await lmgtfy_handler.prepare()

    assert stub.calls == []
    assert lmgtfy_handler.resolved_query is None

    # The warm-up was scheduled in the background; let it finish.
    pending = [
        task for task in asyncio.all_tasks() if task is not asyncio.current_task()
    ]
    await asyncio.gather(*pending, return_exceptions=True)
    assert stub.warmed_up is True


@pytest.mark.parametrize(
    "message,reaction_class",
    [
        ("Vas a votar a Rajoy, y lo sabes", RajoyReaction),
        ("Esta es la españa que nos deja zapatero", ZapateroReaction),
        ("https://google.com", PunishmentReaction),
        ("Probando, probando", MiMiMiReaction),
        ("El otro día estuve en casa de mi tía", BrokenGroupReaction),
        ("El otro día fui a casa de mi tía", BrokenGroupReaction),
        ("Digi, no sé nada de esto", DigiReaction),
        ("Hostia, no sé qué es eso", LmgtfyReaction),
    ],
)
def test_reaction_factory(message, reaction_class):
    reaction_class.probability = 100
    message_instance = ReactionRegistry.process_message(message)
    assert isinstance(message_instance, reaction_class)


def test_reaction_priorities_are_unique():
    priorities = [
        registration.priority for registration in ReactionRegistry.get_registries()
    ]
    assert len(priorities) == len(set(priorities))


def test_instantiating_a_reaction_does_not_roll_the_send_probability(monkeypatch):
    rolls = []
    monkeypatch.setattr("reactions.reactions.random", lambda: rolls.append(1) or 0.0)

    RajoyReaction()

    assert rolls == []


def test_process_message_rolls_the_send_probability_only_once(monkeypatch):
    rolls = []
    monkeypatch.setattr("reactions.reactions.random", lambda: rolls.append(1) or 0.0)

    reaction = ReactionRegistry.process_message("Vas a votar a Rajoy, y lo sabes")

    assert isinstance(reaction, RajoyReaction)
    assert rolls == [1]
    assert reaction.shall_i_send_it() is True


@pytest.fixture
def registry_snapshot():
    registries = ReactionRegistry.get_registries()
    yield
    ReactionRegistry._registries[:] = registries


def test_registrations_are_sorted_by_priority(registry_snapshot):
    class DummyReaction(RajoyReaction):
        pass

    ReactionRegistry.register("low", priority=90)(DummyReaction)
    ReactionRegistry.register("high", priority=10)(DummyReaction)

    registrations = ReactionRegistry.get_registries()
    priorities = [registration.priority for registration in registrations]
    assert priorities == sorted(priorities)


@pytest.mark.asyncio
async def test_reaction_handler_skips_supported_media_links(monkeypatch):
    handler = ReactionHandlerFactory()
    called = False

    def should_not_process(_message):
        nonlocal called
        called = True
        raise AssertionError(
            "A supported media link must not reach the reactions registry"
        )

    monkeypatch.setattr(ReactionRegistry, "process_message", should_not_process)

    await handler.process(
        SimpleNamespace(
            effective_message=SimpleNamespace(
                text="https://www.instagram.com/p/carousel/"
            ),
        ),
        SimpleNamespace(),
    )

    assert not called


def make_text_message(text):
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type="private"),
        text=text,
    )


def test_reaction_handler_ignores_updates_that_are_not_plain_messages():
    """Edited messages and channel posts must not trigger reactions.

    They reach MessageHandler via filters.TEXT (which checks effective_message)
    but update.message is None on those update types.
    """
    handler = ReactionHandlerFactory()
    message = make_text_message("Vas a votar a Rajoy, y lo sabes")

    assert not handler.filters.check_update(Update(update_id=1, edited_message=message))
    assert not handler.filters.check_update(Update(update_id=2, channel_post=message))
    assert not handler.filters.check_update(
        Update(update_id=3, edited_channel_post=message)
    )
    assert handler.filters.check_update(Update(update_id=4, message=message))


@pytest.mark.asyncio
async def test_reaction_handler_replies_via_effective_message(monkeypatch):
    """reply=True reactions must not rely on update.message being present."""
    handler = ReactionHandlerFactory()

    class DummyReaction:
        reply = True

        def transform(self):
            return "🚨🚨 Kids Alert! 🚨🚨"

    class DummyBot:
        async def send_chat_action(self, chat_id, action):
            pass

    monkeypatch.setattr(
        ReactionRegistry, "process_message", lambda *args, **kwargs: DummyReaction()
    )
    monkeypatch.setattr("reactions.reactions.randint", lambda _a, _b: 0)

    recorder = SimpleNamespace(texts=[])

    async def reply_text(text):
        recorder.texts.append(text)

    # No `message` attribute on purpose: mimics edited/channel updates.
    update = SimpleNamespace(
        effective_message=SimpleNamespace(text="mi hija", reply_text=reply_text),
        effective_chat=SimpleNamespace(id=1),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={}),
        bot=DummyBot(),
    )

    await handler.process(update, context)

    assert recorder.texts == ["🚨🚨 Kids Alert! 🚨🚨"]


@pytest.mark.asyncio
async def test_reaction_handler_lets_the_extractor_resolve_the_lmgtfy_topic(
    monkeypatch,
):
    stub = StubTopicExtractor()
    monkeypatch.setattr("reactions.reactions.topic_extractor", stub)
    monkeypatch.setattr("reactions.reactions.randint", lambda _a, _b: 0)

    class DummyBot:
        async def send_chat_action(self, chat_id, action):
            pass

    handler = ReactionHandlerFactory()
    recorder = SimpleNamespace(texts=[])

    async def reply_text(text):
        recorder.texts.append(text)

    update = SimpleNamespace(
        effective_message=SimpleNamespace(
            text="no sé de qué habláis", reply_text=reply_text
        ),
        effective_chat=SimpleNamespace(id=7),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={}),
        bot=DummyBot(),
    )

    # The extractor is only consulted when the chat has conversation context.
    chat_history.add(7, "Qué buena banda es Angine de Poitrine")
    chat_history.add(7, "Sí, me encantan")
    try:
        await handler.process(update, context)
    finally:
        chat_history.clear(7)

    assert recorder.texts == [
        "Te lo busco en Google... https://lmgtfy.com/?q=Angine+de+Poitrine"
    ]
    assert stub.calls[0][0] == "no sé de qué habláis"
    assert stub.calls[0][2] == [
        "Qué buena banda es Angine de Poitrine",
        "Sí, me encantan",
    ]
