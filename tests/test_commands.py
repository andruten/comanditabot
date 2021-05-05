from datetime import datetime

import pytest
from freezegun import freeze_time
from pytz import timezone

from commands import (
    MiMiMiCommandHandler,
    PunisherCommandHandler,
    StarCommandHandler,
    WeatherInKoreaCommandHandler,
)


# mimimi
from messages.messages import PunishmentMessage


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
    assert punisher_command_handler.punish() in PunishmentMessage.PUNISHMENTS


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
    assert weather_in_korea_command_handler.get_utc_now() == datetime(2021, 3, 31, 8, 0, 0, tzinfo=timezone('UTC'))


@freeze_time("2021-03-31 8:00:00")
def test_is_korea_awake(weather_in_korea_command_handler):
    assert weather_in_korea_command_handler.is_korea_sleeping() is False


@freeze_time("2021-03-31 18:00:00")
def test_is_korea_sleeping(weather_in_korea_command_handler):
    assert weather_in_korea_command_handler.is_korea_sleeping() is True
