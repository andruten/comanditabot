import pytest

from clients.exceptions import NotFoundException
from clients.weather import WeatherClient


@pytest.fixture
def weather_client():
    return WeatherClient()


@pytest.fixture
def weather_response():
    return {"coord": {"lon": 126.9778, "lat": 37.5683},
            "weather": [{"id": 800, "main": "Clear", "description": "cielo claro", "icon": "01n"}], "base": "stations",
            "main": {"temp": 8.66, "feels_like": 8.08, "temp_min": 8, "temp_max": 10, "pressure": 1015, "humidity": 76},
            "visibility": 10000, "wind": {"speed": 1.54, "deg": 340}, "clouds": {"all": 0}, "dt": 1617212165,
            "sys": {"type": 1, "id": 8105, "country": "KR", "sunrise": 1617225469, "sunset": 1617270835},
            "timezone": 32400, "id": 1835848, "name": "Seoul", "cod": 200}


def test_params(weather_client):
    params = weather_client.get_params(q="Seoul")
    assert "appid" in params
    assert "units" in params
    assert "lang" in params
    assert "q" in params


def test_parse_weather_info(weather_client, weather_response):
    weather_text = weather_client.parse_weather_info(weather_response)
    assert f"Cielo claro.\n\n"\
           f"Ahora hace 8.66ºC aunque la sensación térmica es de 8.08ºC." == weather_text


def test_get_weather_data(requests_mock, weather_client):
    requests_mock.get(weather_client.WEATHER_ENDPOINT, json={"a": "a"})
    response = weather_client.get_weather_data("Seoul")
    assert {"a": "a"} == response


def test_not_found_weather_data(requests_mock, weather_client):
    requests_mock.get(weather_client.WEATHER_ENDPOINT, status_code=404)
    with pytest.raises(NotFoundException):
        weather_client.get_weather_data("Seoul")
