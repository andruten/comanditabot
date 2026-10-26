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


class WeatherInKoreaCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "tiempoencorea"

    def __init__(self, weather_client: WeatherClient | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._weather_client = weather_client or WeatherClient()

    async def process(self, update: Update, context: CallbackContext) -> None:
        bot: Bot = context.bot
        chat_id = update.effective_chat.id
        await fake_typing(bot, chat_id, seconds=1)
        if self.is_korea_sleeping():
            await bot.send_message(chat_id=chat_id, text="Dormida... 😡")
            await fake_typing(bot, chat_id, seconds=2)
        try:
            weather_data = await asyncio.to_thread(
                self._weather_client.get_weather_data, "Seoul"
            )
            text = self._weather_client.parse_weather_info(weather_data)
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

    def get_utc_now(self) -> datetime:
        return datetime.now(ZoneInfo("UTC"))

    def is_korea_sleeping(self) -> bool:
        now_utc = self.get_utc_now()
        now_korea = now_utc.astimezone(ZoneInfo("Asia/Seoul"))
        return 0 <= now_korea.hour < 8
