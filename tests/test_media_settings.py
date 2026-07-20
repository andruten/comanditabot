import pytest

from media_downloads.handler import MediaSettings


def test_media_settings_default_to_ten_downloads_per_minute():
    settings = MediaSettings.from_env({})

    assert settings.max_downloads_per_minute == 10
    assert settings.max_file_size_bytes == 45 * 1024 * 1024


def test_media_settings_allow_the_limits_to_be_configured():
    settings = MediaSettings.from_env(
        {"MEDIA_MAX_DOWNLOADS_PER_MINUTE": "15", "MEDIA_MAX_FILE_SIZE_MB": "40"}
    )

    assert settings.max_downloads_per_minute == 15
    assert settings.max_file_size_bytes == 40 * 1024 * 1024


def test_media_settings_reject_invalid_limits():
    with pytest.raises(ValueError, match="MEDIA_MAX_DOWNLOADS_PER_MINUTE"):
        MediaSettings.from_env({"MEDIA_MAX_DOWNLOADS_PER_MINUTE": "0"})
