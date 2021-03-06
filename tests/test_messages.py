import pytest

from messages.constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from messages.messages import (
    RajoyMessage, ZapateroMessage, MiMiMiMessage, PunishmentMessage, message_factory, KidsAlertMessage
)


def test_rajoy_message():
    message_handler = RajoyMessage()
    assert message_handler.reply is False
    assert message_handler.transform() in RAJOY_PHRASES


def test_zapatero_message():
    message_handler = ZapateroMessage()
    assert message_handler.reply is False
    assert message_handler.transform() in ZAPATERO_PHRASES


def test_mimimi_message():
    message = 'This is a test message'
    message_handler = MiMiMiMessage(message=message)
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == 'This is i tist missigi'


def test_punishent_message():
    message_handler = PunishmentMessage()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message in message_handler.PUNISHMENTS


def test_kids_alert_message():
    message_handler = KidsAlertMessage()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == '🚨🚨 Kids Alert! 🚨🚨'


@pytest.mark.parametrize(
    'message,message_class',
    [
        ('Vas a votar a Rajoy, y lo sabes', RajoyMessage),
        ('Esta es la españa que nos deja zapatero', ZapateroMessage),
        ('https://google.com', PunishmentMessage),
        ('Probando, probando', MiMiMiMessage),
    ],
)
def test_message_factory(message, message_class):
    message_instance = message_factory(message, probability=100)
    assert isinstance(message_instance, message_class)
