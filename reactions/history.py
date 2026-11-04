import logging
from collections import deque
from typing import ClassVar

logger = logging.getLogger(__name__)


class ChatHistory:
    """Bounded in-memory rolling log of recent text messages per chat.

    Telegram bots cannot fetch chat history through the Bot API, so the only
    context available is the text the bot has seen since it started. The log
    is deliberately kept in RAM only: it is never written to ``bot_data`` so
    it does not end up in the PicklePersistence dump in ``/data``.
    """

    MAX_MESSAGES_PER_CHAT: ClassVar[int] = 20

    def __init__(self) -> None:
        self._messages: dict[int, deque[str]] = {}

    def add(self, chat_id: int, text: str) -> None:
        if not text:
            return
        self._messages.setdefault(
            chat_id, deque(maxlen=self.MAX_MESSAGES_PER_CHAT)
        ).append(text)

    def recent(self, chat_id: int, limit: int | None = None) -> list[str]:
        """Snapshot of the recorded texts, oldest first.

        Return up to ``limit`` most recent messages when given.
        """
        snapshot = list(self._messages.get(chat_id, ()))
        if limit is not None:
            return snapshot[-limit:]
        return snapshot

    def clear(self, chat_id: int) -> None:
        self._messages.pop(chat_id, None)


chat_history = ChatHistory()
