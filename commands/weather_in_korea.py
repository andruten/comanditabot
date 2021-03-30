from time import sleep

import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.bot import Bot

from commands.base import BaseCommandHandler


OPEN_WEATHER_MAP_APP_ID = "1234"


class WeatherInKoreaCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "tiempoencorea"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text="Dormida... 😡"
        )
        sleep(2)
        bot.send_message(
            chat_id=update.effective_chat.id,
            text="No, en serio, ahora te digo."
        )
        sleep(1)
        query = {
            "q": "Seoul",
            "appid": OPEN_WEATHER_MAP_APP_ID,
            "units": "metric",
        }
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=query,
        )
        weather_data = response.json()
        weather_text = ", ".join([weather.get("main", "") for weather in weather_data.get("weather", [])])
        temperature = weather_data.get("main", {})
        temp = temperature.get("temp", 0)
        feels_like = temperature.get("feels_like", 0)
        temp_min = temperature.get("temp_min", 0)
        temp_max = temperature.get("temp_max", 0)
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Weather: {weather_text}\n"
                 f"Temp: {temp}ºC\n"
                 f"Feels like: {feels_like}ºC\n"
                 f"Min: {temp_min}ºC\n"
                 f"Max: {temp_max}ºC",
        )
