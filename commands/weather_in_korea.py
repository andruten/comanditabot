from time import sleep

import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.bot import Bot

from commands.base import BaseCommandHandler


class WeatherInKoreaCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "tiempoencorea"
    OPEN_WEATHER_MAP_APP_ID = "1234"
    WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        if self.is_korea_sleeping():
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="Dormida... 😡"
            )
            sleep(2)
        try:
            weather_data = self.get_weather_data()
            text = self.parse_weather_info(weather_data)
        except ConnectionError:
            text = "No he podido obtener tiempo 😢"
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )

    def is_korea_sleeping(self):
        # TODO: Calculate if korea is sleeping
        return True

    def get_weather_data(self):
        params = {
            "q": "Seoul",
            "appid": self.OPEN_WEATHER_MAP_APP_ID,
            "units": "metric",
            "lang": "es",
        }
        response = requests.get(self.WEATHER_ENDPOINT, params=params)
        return response.json()

    def parse_weather_info(self, weather_data):
        weather_text = ", ".join([weather.get("description", "")
                                  for weather in weather_data.get("weather", [])])
        temperature = weather_data.get("main", {})
        temp = temperature.get("temp", 0)
        feels_like = temperature.get("feels_like", 0)
        temp_min = temperature.get("temp_min", 0)
        temp_max = temperature.get("temp_max", 0)
        return f"Hoy hay {weather_text}.\n" \
               f"Ahora hacen {temp}ºC aunque la sensación térmica es de {feels_like}ºC.\n" \
               f"La mínima para hoy es de {temp_min}ºC y la máxima de {temp_max}ºC."
