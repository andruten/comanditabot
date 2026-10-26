import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time

from clients.weather import WeatherClient
from commands import (
    MiMiMiCommandHandler,
    PunisherCommandHandler,
    StarCommandHandler,
    WeatherInKoreaCommandHandler,
)

# mimimi
from reactions.reactions import PunishmentReaction


@pytest.fixture
def mimimi_command_handler():
    return MiMiMiCommandHandler()


def test_mimimi(mimimi_command_handler):
    text = "aáàäâ AÁÀÄÂ"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "iíìïî IÍÌÏÎ"

    text = "eéèëê EÉÈËÊ"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "iíìïî IÍÌÏÎ"

    text = "oóòöô OÓÒÖÔ"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "iíìïî IÍÌÏÎ"

    text = "uúùüû UÚÙÜÛ"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "iíìïî IÍÌÏÎ"


# sentenciador


@pytest.fixture
def punisher_command_handler():
    return PunisherCommandHandler()


def test_punishments(punisher_command_handler):
    assert punisher_command_handler.punish() in PunishmentReaction.PUNISHMENTS


# star


@pytest.fixture
def star_command_handler():
    return StarCommandHandler()


# tiempoencorea


@pytest.fixture
def weather_in_korea_command_handler():
    return WeatherInKoreaCommandHandler()


@freeze_time("2021-03-31 8:00:00")
def test_utc_now(weather_in_korea_command_handler):
    assert weather_in_korea_command_handler.get_utc_now() == datetime(
        2021, 3, 31, 8, 0, 0, tzinfo=ZoneInfo("UTC")
    )


@freeze_time("2021-03-31 8:00:00")
def test_is_korea_awake(weather_in_korea_command_handler):
    assert weather_in_korea_command_handler.is_korea_sleeping() is False


@freeze_time("2021-03-31 18:00:00")
def test_is_korea_sleeping(weather_in_korea_command_handler):
    assert weather_in_korea_command_handler.is_korea_sleeping() is True


def test_uses_the_injected_weather_client(monkeypatch):
    client = MagicMock(spec=WeatherClient)
    client.get_weather_data.return_value = {}
    client.parse_weather_info.return_value = "Soleado"
    handler = WeatherInKoreaCommandHandler(weather_client=client)
    monkeypatch.setattr(
        "commands.weather_in_korea.asyncio.sleep", AsyncMock(return_value=None)
    )

    bot = MagicMock()
    bot.send_chat_action = AsyncMock()
    bot.send_message = AsyncMock()
    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=123), message=SimpleNamespace()
    )
    context = SimpleNamespace(bot=bot)

    asyncio.run(handler.process(update, context))

    client.get_weather_data.assert_called_once_with("Seoul")
    bot.send_message.assert_called_with(chat_id=123, text="Soleado")
