import os

import requests

from clients.exceptions import NotFoundException


class WeatherClient:
    def __init__(self) -> None:
        super().__init__()
        self.OPEN_WEATHER_MAP_APP_ID = os.environ.get('OPEN_WEATHER_MAP_APP_ID')
        self.WEATHER_ENDPOINT = 'https://api.openweathermap.org/data/2.5/weather'

    def _default_params(self):
        return {
            'appid': self.OPEN_WEATHER_MAP_APP_ID,
            'units': 'metric',
            'lang': 'es',
        }

    def get_params(self, **kwargs):
        return {
            **self._default_params(),
            **kwargs,
        }

    def get_weather_data(self, city_name):
        params = self.get_params(q=city_name)
        response = requests.get(self.WEATHER_ENDPOINT, params=params)
        if response.status_code == 404:
            raise NotFoundException()
        return response.json()

    def parse_weather_info(self, weather_data):
        weather_text = ', '.join([weather.get('description', '')
                                  for weather in weather_data.get('weather', [])])
        temperature = weather_data.get('main', {})
        temp = temperature.get('temp', 0)
        feels_like = temperature.get('feels_like', 0)
        return f'{weather_text.capitalize()}.\n\n'\
               f'Ahora hace {temp}ºC aunque la sensación térmica es de {feels_like}ºC.'
