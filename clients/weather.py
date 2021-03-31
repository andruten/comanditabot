import requests


class WeatherClient:
    OPEN_WEATHER_MAP_APP_ID = "1234"
    WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

    def _default_params(self):
        return {
            "appid": self.OPEN_WEATHER_MAP_APP_ID,
            "units": "metric",
            "lang": "es",
        }

    def get_weather_data(self, city_name):
        params = {
            "q": city_name,
            **self._default_params()
        }
        response = requests.get(self.WEATHER_ENDPOINT, params=params)
        if response.status_code == 404:
            return {}
        return response.json()

    def parse_weather_info(self, weather_data):
        weather_text = ", ".join([weather.get("description", "")
                                  for weather in weather_data.get("weather", [])])
        temperature = weather_data.get("main", {})
        temp = temperature.get("temp", 0)
        feels_like = temperature.get("feels_like", 0)
        return f"{weather_text.capitalize()}.\n\n"\
               f"Ahora hace {temp}ºC aunque la sensación térmica es de {feels_like}ºC."
