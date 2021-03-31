import pytest

from commands import MiMiMiCommandHandler


@pytest.fixture()
def mimimi_command_handler():
    return MiMiMiCommandHandler()


def test_mimimi(mimimi_command_handler):
    text = "Hola"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "Hili"


def test_mimimi_special_chars(mimimi_command_handler):
    text = "AÁÀÄÂ"
    response = mimimi_command_handler.do_mimimi(text)
    assert response == "IÍÌÏÎ"
