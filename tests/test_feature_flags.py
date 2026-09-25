from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from chat_statistics.chat_statistics import (
    ChatStatistics,
    ChatStatisticsMessageHandlerFactory,
)
from feature_flags.catalog import flag_catalog
from feature_flags.commands import (
    KILL_SWITCH_OFF_TEXT,
    KILL_SWITCH_ON_TEXT,
    NOT_ADMIN_TEXT,
    USAGE_TEXT,
    ReactionsFlagCommandHandler,
)
from feature_flags.store import LO_QUE_ESCRIBIS, STORE_KEY, FeatureFlagStore
from reactions.exceptions import DoNothingException
from reactions.reactions import (
    MiMiMiReaction,
    RajoyReaction,
    ReactionHandlerFactory,
    ReactionRegistry,
)


class ReplyRecorder:
    def __init__(self):
        self.texts = []

    async def __call__(self, text):
        self.texts.append(text)


class RecordingBot:
    def __init__(self, admin_ids=()):
        self.admin_ids = admin_ids
        self.sent = []

    async def send_message(self, chat_id, text):
        self.sent.append(text)

    async def get_chat_administrators(self, chat_id):
        return [
            SimpleNamespace(user=SimpleNamespace(id=admin_id))
            for admin_id in self.admin_ids
        ]


def make_update(chat_id=1, user_id=1, chat_type="supergroup"):
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id, type=chat_type),
        effective_user=SimpleNamespace(id=user_id),
        effective_message=SimpleNamespace(reply_text=ReplyRecorder()),
    )


def make_context(args, bot_data, bot=None):
    return SimpleNamespace(
        args=args,
        application=SimpleNamespace(bot_data=bot_data),
        bot=bot,
    )


def replies(update):
    return update.effective_message.reply_text.texts


# store


def test_fresh_store_allows_everything():
    store = FeatureFlagStore()
    assert not store.is_blocked(1, "rajoy")
    assert not store.all_disabled(1)
    assert store.disabled_codes(1) == set()


def test_disable_and_enable_codes():
    store = FeatureFlagStore()
    store.disable(1, {"rajoy", "digi"})
    assert store.is_blocked(1, "rajoy")
    assert store.is_blocked(1, "digi")
    assert not store.is_blocked(1, "mimimi")
    assert not store.is_blocked(2, "rajoy")
    store.enable(1, {"rajoy"})
    assert not store.is_blocked(1, "rajoy")
    assert store.is_blocked(1, "digi")


def test_kill_switch_blocks_everything():
    store = FeatureFlagStore()
    store.disable_all(1)
    assert store.all_disabled(1)
    assert store.is_blocked(1, "rajoy")
    assert store.is_blocked(1, LO_QUE_ESCRIBIS)
    assert not store.all_disabled(2)


def test_enable_all_resets_everything():
    store = FeatureFlagStore()
    store.disable(1, {"rajoy"})
    store.disable_all(1)
    store.enable_all(1)
    assert not store.all_disabled(1)
    assert not store.is_blocked(1, "rajoy")
    assert store.disabled_codes(1) == set()


def test_from_bot_data_creates_and_reuses_store():
    bot_data = {}
    context = make_context([], bot_data)
    store = FeatureFlagStore.from_bot_data(context)
    assert isinstance(store, FeatureFlagStore)
    assert bot_data[STORE_KEY] is store
    assert FeatureFlagStore.from_bot_data(context) is store


# catalog


def test_catalog_covers_registry_codes_and_bot_messages():
    catalog = flag_catalog()
    codes = {flag.code for flag in catalog}
    registry_codes = {registry.code for registry in ReactionRegistry.get_registries()}
    assert codes == registry_codes | {LO_QUE_ESCRIBIS}


def test_catalog_has_descriptions_for_every_flag():
    for flag in flag_catalog():
        assert flag.description


# command


@pytest.mark.asyncio
async def test_status_lists_all_flags():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10)
    await handler.process(update, make_context([], {}))
    text = replies(update)[0]
    for flag in flag_catalog():
        assert flag.code in text
        assert flag.description in text
    assert "✅" in text


@pytest.mark.asyncio
async def test_status_marks_disabled_flags():
    handler = ReactionsFlagCommandHandler()
    bot_data = {}
    store = FeatureFlagStore()
    store.disable(10, {"rajoy"})
    bot_data[STORE_KEY] = store
    update = make_update(chat_id=10)
    await handler.process(update, make_context([], bot_data))
    text = replies(update)[0]
    assert "❌ rajoy" in text
    assert "✅ mimimi" in text


@pytest.mark.asyncio
async def test_status_announces_kill_switch():
    handler = ReactionsFlagCommandHandler()
    bot_data = {}
    store = FeatureFlagStore()
    store.disable_all(10)
    bot_data[STORE_KEY] = store
    update = make_update(chat_id=10)
    await handler.process(update, make_context([], bot_data))
    assert "Kill switch activo" in replies(update)[0]


@pytest.mark.asyncio
async def test_list_shows_codes_with_descriptions():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10)
    await handler.process(update, make_context(["list"], {}))
    text = replies(update)[0]
    assert "on|off" in text
    for flag in flag_catalog():
        assert f"{flag.code} — {flag.description}" in text


@pytest.mark.asyncio
async def test_off_requires_admin():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=7)
    bot = RecordingBot(admin_ids=(99,))
    bot_data = {STORE_KEY: FeatureFlagStore()}
    await handler.process(update, make_context(["off", "rajoy"], bot_data, bot))
    assert not bot_data[STORE_KEY].is_blocked(10, "rajoy")
    assert replies(update) == [NOT_ADMIN_TEXT]


@pytest.mark.asyncio
async def test_admin_can_disable_and_enable_codes():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=99)
    bot = RecordingBot(admin_ids=(99,))
    bot_data = {}
    await handler.process(update, make_context(["off", "rajoy", "digi"], bot_data, bot))
    store = bot_data[STORE_KEY]
    assert store.is_blocked(10, "rajoy")
    assert store.is_blocked(10, "digi")
    assert "❌ rajoy" in replies(update)[0]
    await handler.process(update, make_context(["on", "rajoy"], bot_data, bot))
    assert not store.is_blocked(10, "rajoy")
    assert store.is_blocked(10, "digi")


@pytest.mark.asyncio
async def test_admin_can_toggle_kill_switch():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=99)
    bot = RecordingBot(admin_ids=(99,))
    bot_data = {}
    await handler.process(update, make_context(["off", "all"], bot_data, bot))
    store = bot_data[STORE_KEY]
    assert store.all_disabled(10)
    assert replies(update) == [KILL_SWITCH_OFF_TEXT]
    await handler.process(update, make_context(["on", "all"], bot_data, bot))
    assert not store.all_disabled(10)
    assert store.disabled_codes(10) == set()
    assert replies(update) == [KILL_SWITCH_OFF_TEXT, KILL_SWITCH_ON_TEXT]


@pytest.mark.asyncio
async def test_private_chat_owner_can_toggle():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, chat_type="private")
    bot = RecordingBot()
    bot_data = {}
    await handler.process(update, make_context(["off", "mimimi"], bot_data, bot))
    assert bot_data[STORE_KEY].is_blocked(10, "mimimi")


@pytest.mark.asyncio
async def test_unknown_code_reports_error():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=99)
    bot = RecordingBot(admin_ids=(99,))
    bot_data = {STORE_KEY: FeatureFlagStore()}
    await handler.process(update, make_context(["off", "nope"], bot_data, bot))
    assert bot_data[STORE_KEY].disabled_codes(10) == set()
    assert "nope" in replies(update)[0]


@pytest.mark.asyncio
async def test_on_off_without_codes_shows_usage():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=99)
    bot = RecordingBot(admin_ids=(99,))
    await handler.process(update, make_context(["off"], {}, bot))
    assert replies(update) == [USAGE_TEXT]


@pytest.mark.asyncio
async def test_all_mixed_with_other_codes_shows_usage():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10, user_id=99)
    bot = RecordingBot(admin_ids=(99,))
    bot_data = {STORE_KEY: FeatureFlagStore()}
    await handler.process(update, make_context(["off", "all", "rajoy"], bot_data, bot))
    assert replies(update) == [USAGE_TEXT]
    assert not bot_data[STORE_KEY].all_disabled(10)


@pytest.mark.asyncio
async def test_unknown_action_shows_usage():
    handler = ReactionsFlagCommandHandler()
    update = make_update(chat_id=10)
    await handler.process(update, make_context(["boom"], {}))
    assert replies(update) == [USAGE_TEXT]


# reactions enforcement


@pytest.mark.asyncio
async def test_registry_skips_disabled_codes(monkeypatch):
    monkeypatch.setattr(MiMiMiReaction, "probability", 0)
    with pytest.raises(DoNothingException):
        ReactionRegistry.process_message(
            "Vas a votar a Rajoy, y lo sabes", disabled_codes={"rajoy"}
        )


@pytest.mark.asyncio
async def test_registry_keeps_other_codes_when_disabling(monkeypatch):
    monkeypatch.setattr(MiMiMiReaction, "probability", 0)
    reaction = ReactionRegistry.process_message(
        "Vas a votar a Rajoy, y lo sabes", disabled_codes={"digi"}
    )
    assert isinstance(reaction, RajoyReaction)


@pytest.mark.asyncio
async def test_reaction_handler_kill_switch_blocks_registry(monkeypatch):
    handler = ReactionHandlerFactory()
    bot_data = {}
    store = FeatureFlagStore()
    store.disable_all(123)
    bot_data[STORE_KEY] = store
    context = make_context([], bot_data)

    def should_not_process(_message, disabled_codes=None):
        raise AssertionError("Kill switch must short-circuit the registry")

    monkeypatch.setattr(ReactionRegistry, "process_message", should_not_process)
    update = SimpleNamespace(
        effective_message=SimpleNamespace(text="hola a todos"),
        effective_chat=SimpleNamespace(id=123),
    )
    await handler.process(update, context)


@pytest.mark.asyncio
async def test_reaction_handler_passes_disabled_codes(monkeypatch):
    handler = ReactionHandlerFactory()
    bot_data = {}
    store = FeatureFlagStore()
    store.disable(123, {"rajoy", "digi"})
    bot_data[STORE_KEY] = store
    context = make_context([], bot_data)
    captured = {}

    def fake_process_message(_message, disabled_codes=None):
        captured["disabled_codes"] = disabled_codes
        raise DoNothingException()

    monkeypatch.setattr(ReactionRegistry, "process_message", fake_process_message)
    update = SimpleNamespace(
        effective_message=SimpleNamespace(text="hola"),
        effective_chat=SimpleNamespace(id=123),
    )
    await handler.process(update, context)
    assert captured["disabled_codes"] == {"rajoy", "digi"}


# chat statistics enforcement


@pytest.mark.asyncio
async def test_statistics_alert_blocked_by_kill_switch():
    chat_id = 4242
    chat_statistics = ChatStatistics()
    chat_statistics.get_daily_statistics(chat_id).alert_when = 1
    bot_data = {}
    store = FeatureFlagStore()
    store.disable_all(chat_id)
    bot_data[STORE_KEY] = store
    bot = RecordingBot()
    context = make_context([], bot_data, bot)
    update = SimpleNamespace(
        effective_message=MagicMock(),
        effective_chat=SimpleNamespace(id=chat_id),
    )
    await ChatStatisticsMessageHandlerFactory().process(update, context)
    assert chat_statistics.get_daily_statistics(chat_id).messages_count == 1
    assert bot.sent == []


@pytest.mark.asyncio
async def test_statistics_alert_blocked_by_flag():
    chat_id = 4243
    chat_statistics = ChatStatistics()
    chat_statistics.get_daily_statistics(chat_id).alert_when = 1
    bot_data = {}
    store = FeatureFlagStore()
    store.disable(chat_id, {LO_QUE_ESCRIBIS})
    bot_data[STORE_KEY] = store
    bot = RecordingBot()
    context = make_context([], bot_data, bot)
    update = SimpleNamespace(
        effective_message=MagicMock(),
        effective_chat=SimpleNamespace(id=chat_id),
    )
    await ChatStatisticsMessageHandlerFactory().process(update, context)
    assert chat_statistics.get_daily_statistics(chat_id).messages_count == 1
    assert bot.sent == []


@pytest.mark.asyncio
async def test_statistics_alert_sent_when_flag_active():
    chat_id = 4244
    chat_statistics = ChatStatistics()
    chat_statistics.get_daily_statistics(chat_id).alert_when = 1
    bot_data = {}
    bot_data[STORE_KEY] = FeatureFlagStore()
    bot = RecordingBot()
    context = make_context([], bot_data, bot)
    update = SimpleNamespace(
        effective_message=MagicMock(),
        effective_chat=SimpleNamespace(id=chat_id),
    )
    await ChatStatisticsMessageHandlerFactory().process(update, context)
    assert len(bot.sent) == 1
    assert "mensajes" in bot.sent[0]
