import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from telegram import Bot, Update
from telegram.ext import CallbackContext

from clients.exceptions import NotFoundException
from clients.weather import WeatherClient
from commands.base import BaseCommandHandler, fake_typing

logger = logging.getLogger(__name__)


class WeatherInKoreaCommandHandler(WeatherClient, BaseCommandHandler):
    COMMAND_NAME = "tiempoencorea"

    async def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        chat_id = update.effective_chat.id
        await fake_typing(bot, chat_id, seconds=1)
        if self.is_korea_sleeping():
            await bot.send_message(chat_id=chat_id, text="Dormida... 😡")
            await fake_typing(bot, chat_id, seconds=2)
        try:
            weather_data = await asyncio.to_thread(self.get_weather_data, "Seoul")
            text = self.parse_weather_info(weather_data)
        except (
            ConnectionError,
            httpx.RequestError,
            NotFoundException,
        ):
            logger.warning("Could not fetch the weather for Korea")
            text = "No he podido obtener tiempo 😢"
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def get_utc_now(self):
        return datetime.now(ZoneInfo("UTC"))

    def is_korea_sleeping(self):
        now_utc = self.get_utc_now()
        now_korea = now_utc.astimezone(ZoneInfo("Asia/Seoul"))
        return 0 <= now_korea.hour < 8
