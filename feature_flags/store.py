from collections.abc import Iterable
from dataclasses import dataclass, field

from telegram.ext import CallbackContext

STORE_KEY = "feature_flags"
LO_QUE_ESCRIBIS = "lo_que_escribis"


@dataclass
class ChatFlags:
    all_disabled: bool = False
    disabled_codes: set[str] = field(default_factory=set)


@dataclass
class FeatureFlagStore:
    chats: dict[int, ChatFlags] = field(default_factory=dict)

    @classmethod
    def from_bot_data(cls, context: CallbackContext) -> "FeatureFlagStore":
        bot_data = context.application.bot_data
        store = bot_data.get(STORE_KEY)
        if not isinstance(store, cls):
            store = cls()
            bot_data[STORE_KEY] = store
        return store

    def chat_flags(self, chat_id: int) -> ChatFlags:
        return self.chats.setdefault(chat_id, ChatFlags())

    def disable(self, chat_id: int, codes: Iterable[str]) -> None:
        self.chat_flags(chat_id).disabled_codes.update(codes)

    def enable(self, chat_id: int, codes: Iterable[str]) -> None:
        self.chat_flags(chat_id).disabled_codes.difference_update(codes)

    def disable_all(self, chat_id: int) -> None:
        self.chat_flags(chat_id).all_disabled = True

    def enable_all(self, chat_id: int) -> None:
        chat_flags = self.chat_flags(chat_id)
        chat_flags.all_disabled = False
        chat_flags.disabled_codes.clear()

    def is_blocked(self, chat_id: int, code: str) -> bool:
        chat_flags = self.chats.get(chat_id)
        if chat_flags is None:
            return False
        return chat_flags.all_disabled or code in chat_flags.disabled_codes

    def all_disabled(self, chat_id: int) -> bool:
        chat_flags = self.chats.get(chat_id)
        return chat_flags is not None and chat_flags.all_disabled

    def disabled_codes(self, chat_id: int) -> set[str]:
        chat_flags = self.chats.get(chat_id)
        if chat_flags is None:
            return set()
        return set(chat_flags.disabled_codes)
