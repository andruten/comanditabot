import logging
from unittest.mock import MagicMock

import pytest

import comandita
from chat_statistics import ChatStatisticsMessageHandlerFactory
from commands.chat_statistics import ChatStatisticsCommandHandler
from commands.mimimi import MiMiMiCommandHandler

# sentenciador is registered as PunisherCommandHandler
from commands.sentenciador import PunisherCommandHandler
from commands.star import StarCommandHandler
from commands.weather_in_korea import WeatherInKoreaCommandHandler
from feature_flags import ReactionsFlagCommandHandler
from media_downloads.handler import MediaMessageHandler
from reactions import ReactionHandlerFactory


def test_configure_handlers_registers_every_handler():
    application = MagicMock()

    comandita.configure_handlers(application)

    registered_types = [
        (type(call.args[0]), call.kwargs.get("group", 0))
        for call in application.add_handler.call_args_list
    ]
    expected = [
        (MediaMessageHandler, -1),
        (MiMiMiCommandHandler, 0),
        (PunisherCommandHandler, 0),
        (StarCommandHandler, 0),
        (WeatherInKoreaCommandHandler, 0),
        (ChatStatisticsCommandHandler, 0),
        (ReactionsFlagCommandHandler, 0),
        (ReactionHandlerFactory, 0),
        (ChatStatisticsMessageHandlerFactory, 1),
    ]
    assert sorted(registered_types, key=lambda item: (item[0].__name__, item[1])) == (
        sorted(expected, key=lambda item: (item[0].__name__, item[1]))
    )
    application.add_error_handler.assert_called_once_with(comandita.on_error)


@pytest.mark.asyncio
async def test_on_error_logs_the_exception(caplog):
    context = MagicMock()
    context.error = ValueError("boom")

    with caplog.at_level(logging.ERROR):
        await comandita.on_error(None, context)

    assert "Unhandled exception while processing update" in caplog.text
