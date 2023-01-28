import logging
from dataclasses import dataclass, field
from datetime import datetime
from random import randint

from telegram import Bot, Message, Update
from telegram.ext import CallbackContext, Filters, MessageHandler

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


@dataclass
class DailyStatistics:
    messages_count: int = 0
    photos_count: int = 0
    audios_count: int = 0
    videos_count: int = 0
    voices_count: int = 0
    alert_when: int = field(init=False)

    def __post_init__(self):
        self.alert_when = randint(200, 300)

    @property
    def threshold_reached(self) -> bool:
        return self.messages_count == self.alert_when


class ChatStatistics(metaclass=SingletonMeta):
    _daily_counter = {}

    def __init__(self, chat_id: int) -> None:
        super().__init__()
        self.chat_id = chat_id

    def get_daily_statistics(self) -> DailyStatistics:
        if self.chat_id not in self._daily_counter:
            self._daily_counter[self.chat_id] = {}
        today = datetime.utcnow().today().strftime('%Y-%m-%d')
        if today not in self._daily_counter[self.chat_id]:
            self._daily_counter[self.chat_id][today] = DailyStatistics()
        return self._daily_counter[self.chat_id][today]

    def update_daily(self, message: Message) -> None:
        daily_statistics = self.get_daily_statistics()
        daily_statistics.messages_count += 1
        if message.photo:
            daily_statistics.photos_count += 1
        if message.video:
            daily_statistics.videos_count += 1
        if message.voice:
            daily_statistics.voices_count += 1


class ChatStatisticsMessageHandlerFactory(MessageHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(Filters.all, self.process, *args, **kwargs)

    def process(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        chat_statistics = ChatStatistics(chat_id)
        chat_statistics.update_daily(update.effective_message)
        daily_statistics = chat_statistics.get_daily_statistics()
        logger.info(f'{daily_statistics.messages_count} messages today in chat "{chat_id}"')
        if daily_statistics.threshold_reached:
            bot: Bot = context.bot
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'¡La virgen, lo que escribís! {daily_statistics.messages_count} mensajes 😵‍💫',
            )
