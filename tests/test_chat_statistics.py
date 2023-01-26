import pytest  # noqa
from freezegun import freeze_time

from chat_statistics.chat_statistics import ChatStatistics, DailyStatistics


def test_statistics_singleton():
    assert ChatStatistics(1) == ChatStatistics(2)


def test_daily_statistics():
    chat_id = 1
    chat_statistics = ChatStatistics(chat_id)
    daily_statistics = chat_statistics.get_daily_statistics()
    assert isinstance(daily_statistics, DailyStatistics)
    assert daily_statistics.messages == 0
    assert daily_statistics.alert_when >= 200 <= 300


@freeze_time('2023-01-27 03:00:00')
def test_get_counter_key():
    chat_id = 1
    chat_statistics = ChatStatistics(chat_id)
    assert chat_statistics._get_counter_key() == f'{chat_id}|2023-01-27'


def test_update_daily():
    chat_id = 1
    chat_statistics = ChatStatistics(chat_id)
    chat_statistics.update_daily()
    daily_statistics = chat_statistics.get_daily_statistics()
    assert daily_statistics.messages == 1
