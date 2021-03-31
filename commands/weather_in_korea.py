from time import sleep
from datetime import datetime
from pytz import timezone

from telegram import Update
from telegram.ext import CallbackContext
from telegram.bot import Bot

from clients.weather import WeatherClient
from commands.base import BaseCommandHandler


class WeatherInKoreaCommandHandler(WeatherClient, BaseCommandHandler):
    COMMAND_NAME = "tiempoencorea"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        if self.is_korea_sleeping():
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="Dormida... 😡"
            )
            sleep(2)
        try:
            weather_data = self.get_weather_data("Seoul")
            text = self.parse_weather_info(weather_data)
        except ConnectionError:
            text = "No he podido obtener tiempo 😢"
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def get_utc_now(self):
        return datetime.now(timezone('UTC'))

    def is_korea_sleeping(self):
        now_utc = self.get_utc_now()
        now_korea = now_utc.astimezone(timezone('Asia/Seoul'))
        return 0 <= now_korea.hour < 8
