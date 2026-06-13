import asyncio
from datetime import datetime

from zoneinfo import ZoneInfo
from telegram import Bot, Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext

from clients.exceptions import NotFoundException
from clients.weather import WeatherClient
from commands.base import BaseCommandHandler


class WeatherInKoreaCommandHandler(WeatherClient, BaseCommandHandler):
    COMMAND_NAME = 'tiempoencorea'

    async def process(self, update: Update, context: CallbackContext):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(1)
        bot: Bot = context.bot
        if self.is_korea_sleeping():
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text='Dormida... 😡'
            )
            await asyncio.sleep(1)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(2)
        try:
            weather_data = self.get_weather_data('Seoul')
            text = self.parse_weather_info(weather_data)
        except (ConnectionError, NotFoundException, ):
            text = 'No he podido obtener tiempo 😢'
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def get_utc_now(self):
        return datetime.now(ZoneInfo('UTC'))

    def is_korea_sleeping(self):
        now_utc = self.get_utc_now()
        now_korea = now_utc.astimezone(ZoneInfo('Asia/Seoul'))
        return 0 <= now_korea.hour < 8
