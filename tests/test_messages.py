from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from telegram import Chat, Message, Update

from reactions.constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from reactions.reactions import (
    BrokenGroupReaction,
    KidsAlertReaction,
    MiMiMiReaction,
    PunishmentReaction,
    RajoyReaction,
    ReactionRegistry,
    ReactionHandlerFactory,
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


@pytest.mark.parametrize(
    "message,reaction_class",
    [
        ("Vas a votar a Rajoy, y lo sabes", RajoyReaction),
        ("Esta es la españa que nos deja zapatero", ZapateroReaction),
        ("https://google.com", PunishmentReaction),
        ("Probando, probando", MiMiMiReaction),
        ("El otro día estuve en casa de mi tía", BrokenGroupReaction),
        ("El otro día fui a casa de mi tía", BrokenGroupReaction),
    ],
)
def test_reaction_factory(message, reaction_class):
    reaction_class.probability = 100
    message_instance = ReactionRegistry.process_message(message)
    assert isinstance(message_instance, reaction_class)


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
        date=datetime.now(timezone.utc),
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
