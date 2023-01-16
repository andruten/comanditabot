import pytest

from reactions.constants import RAJOY_PHRASES, ZAPATERO_PHRASES
from reactions.reactions import (BrokenGroupReaction, KidsAlertReaction,
                                 MiMiMiReaction, PunishmentReaction,
                                 RajoyReaction, ReactionRegistry,
                                 ZapateroReaction)


def test_rajoy_message():
    message_handler = RajoyReaction()
    assert message_handler.reply is False
    assert message_handler.transform() in RAJOY_PHRASES


def test_zapatero_message():
    message_handler = ZapateroReaction()
    assert message_handler.reply is False
    assert message_handler.transform() in ZAPATERO_PHRASES


def test_mimimi_message():
    message = 'This is a test message'
    message_handler = MiMiMiReaction(message=message)
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == 'This is i tist missigi'


def test_punishent_message():
    message_handler = PunishmentReaction()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message in message_handler.PUNISHMENTS


def test_kids_alert_message():
    message_handler = KidsAlertReaction()
    assert message_handler.reply is True
    transformed_message = message_handler.transform()
    assert transformed_message == '🚨🚨 Kids Alert! 🚨🚨'


def test_message_broken_group():
    broken_group_handler = BrokenGroupReaction()
    assert broken_group_handler.reply is True
    transformed_message = broken_group_handler.transform()
    assert transformed_message == 'Anda que avisas... El grupo está roto.'


@pytest.mark.parametrize(
    'message,reaction_class',
    [
        ('Vas a votar a Rajoy, y lo sabes', RajoyReaction),
        ('Esta es la españa que nos deja zapatero', ZapateroReaction),
        ('https://google.com', PunishmentReaction),
        ('Probando, probando', MiMiMiReaction),
        ('El otro día estuve en casa de mi tía', BrokenGroupReaction),
        ('El otro día fui a casa de mi tía', BrokenGroupReaction),
    ],
)
def test_reaction_factory(message, reaction_class):
    reaction_class.probability = 100
    message_instance = ReactionRegistry.process_message(message)
    assert isinstance(message_instance, reaction_class)
