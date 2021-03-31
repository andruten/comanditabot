import pytest

from commands import (
    MiMiMiCommandHandler,
    PunisherCommandHandler,
    StarCommandHandler,
    WeatherInKoreaCommandHandler,
)


# mimimi

@pytest.fixture()
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

@pytest.fixture()
def punisher_command_handler():
    return PunisherCommandHandler()


def test_punishments(punisher_command_handler):
    assert punisher_command_handler.punish() in punisher_command_handler.PUNISHMENTS


# star

@pytest.fixture()
def star_command_handler():
    return StarCommandHandler()


# tiempoencorea

@pytest.fixture()
def weather_in_korea_command_handler():
    return WeatherInKoreaCommandHandler()
