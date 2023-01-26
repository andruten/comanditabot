from dataclasses import dataclass
from datetime import datetime
from random import randint

from telegram import Bot, Update
from telegram.ext import CallbackContext, Filters, MessageHandler


class SingletonMeta(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


@dataclass
class DailyStatistics:
    messages: int
    alert_when: int

    @property
    def threshold_reached(self) -> bool:
        return self.messages == self.alert_when


class ChatStatistics(metaclass=SingletonMeta):
    _daily_counter = {}

    def __init__(self, chat_id: int) -> None:
        super().__init__()
        self.chat_id = chat_id

    def _get_counter_key(self) -> str:
        today = datetime.utcnow().today().strftime('%Y-%m-%d')
        return f'{self.chat_id}|{today}'

    def get_daily_statistics(self) -> DailyStatistics:
        counter_key = self._get_counter_key()
        if counter_key not in self._daily_counter:
            self._daily_counter[counter_key] = DailyStatistics(messages=0, alert_when=randint(200, 300))
        return self._daily_counter[counter_key]

    def update_daily(self) -> None:
        daily_statistics = self.get_daily_statistics()
        daily_statistics.messages += 1

    @property
    def daily_threshold_reached(self) -> bool:
        daily_statistics = self.get_daily_statistics()
        return daily_statistics.threshold_reached


class ChatStatisticsMessageHandlerFactory(MessageHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(Filters.all, self.process, *args, **kwargs)

    def process(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        chat_statistics = ChatStatistics(chat_id)
        chat_statistics.update_daily()
        daily_statistics = chat_statistics.get_daily_statistics()
        if daily_statistics.threshold_reached:
            bot: Bot = context.bot
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'¡La virgen, lo que escribís! {daily_statistics.messages} mensajes 😵‍💫',
            )
