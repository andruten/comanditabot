from dataclasses import dataclass

from reactions.reactions import ReactionRegistry

from .store import LO_QUE_ESCRIBIS

SECTION_REACTIONS = "reactions"
SECTION_MESSAGES = "bot_messages"

LO_QUE_ESCRIBIS_DESCRIPTION = (
    "Aviso de estadísticas cuando el chat alcanza su umbral diario de mensajes"
)


@dataclass(frozen=True)
class FlagDefinition:
    code: str
    description: str
    section: str


def flag_catalog() -> tuple[FlagDefinition, ...]:
    reactions = tuple(
        FlagDefinition(
            code=registry.code,
            description=registry.reaction_class.description,
            section=SECTION_REACTIONS,
        )
        for registry in ReactionRegistry.get_registries()
    )
    return reactions + (
        FlagDefinition(
            code=LO_QUE_ESCRIBIS,
            description=LO_QUE_ESCRIBIS_DESCRIPTION,
            section=SECTION_MESSAGES,
        ),
    )
