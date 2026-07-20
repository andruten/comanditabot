from pathlib import Path

import pytest

from media_downloads.downloader import (
    DownloadError,
    MediaDownloader,
    MediaTooLargeError,
    YtDlpExtractor,
)

MIB = 1024 * 1024


class FakeExtractor:
    def __init__(self, files):
        self.files = files
        self.urls = []

    def extract(self, url, output_directory):
        self.urls.append(url)
        output_paths = []
        for name, size in self.files:
            output_path = output_directory / name
            output_path.write_bytes(b"x" * size)
            output_paths.append(output_path)
        return output_paths


def test_download_preserves_extractor_file_order(tmp_path):
    extractor = FakeExtractor([("first.jpg", 1), ("second.mp4", 1)])
    downloader = MediaDownloader(extractor=extractor, max_file_size_bytes=45 * MIB)

    files = downloader.download("https://x.com/alice/status/1", tmp_path)

    assert extractor.urls == ["https://x.com/alice/status/1"]
    assert [file.path.name for file in files] == ["first.jpg", "second.mp4"]


def test_download_rejects_oversized_file(tmp_path):
    downloader = MediaDownloader(
        extractor=FakeExtractor([("clip.mp4", 46 * MIB)]), max_file_size_bytes=45 * MIB
    )

    with pytest.raises(MediaTooLargeError):
        downloader.download("https://x.com/alice/status/1", tmp_path)


def test_download_rejects_empty_output(tmp_path):
    downloader = MediaDownloader(extractor=FakeExtractor([]), max_file_size_bytes=45 * MIB)

    with pytest.raises(DownloadError, match="No media"):
        downloader.download("https://x.com/alice/status/1", tmp_path)


def test_download_rejects_file_outside_temporary_directory(tmp_path):
    outside_file = tmp_path.parent / "outside.mp4"
    outside_file.write_bytes(b"x")

    class UnsafeExtractor:
        def extract(self, url: str, output_directory: Path):
            return [outside_file]

    downloader = MediaDownloader(extractor=UnsafeExtractor(), max_file_size_bytes=45 * MIB)

    with pytest.raises(DownloadError, match="temporary directory"):
        downloader.download("https://x.com/alice/status/1", tmp_path)


def test_extractor_keeps_all_items_when_a_url_has_multiple_media(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    YtDlpExtractor(max_file_size_bytes=45 * MIB).extract("https://instagram.com/p/example", tmp_path)

    assert options.get("noplaylist") is not True


def test_extractor_does_not_expand_youtube_playlists(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    YtDlpExtractor(max_file_size_bytes=45 * MIB).extract(
        "https://youtube.com/watch?v=example&list=playlist", tmp_path
    )

    assert options["noplaylist"] is True


def test_extractor_prefers_a_telegram_playable_mp4_format(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    YtDlpExtractor(max_file_size_bytes=45 * MIB).extract("https://instagram.com/p/example", tmp_path)

    assert options["format"] == (
        "best[ext=mp4][vcodec!*=vp9][acodec!=none]/best[ext=mp4][acodec!=none]/best"
    )


def test_extractor_rejects_youtube_videos_longer_than_ten_minutes(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    YtDlpExtractor(max_file_size_bytes=45 * MIB).extract(
        "https://youtube.com/watch?v=example", tmp_path
    )

    match_filter = options["match_filter"]
    assert (
        match_filter(
            {"webpage_url": "https://youtube.com/watch?v=example", "duration": 601},
            incomplete=False,
        )
        == "YouTube videos longer than 10 minutes are not supported"
    )
    assert (
        match_filter(
            {"webpage_url": "https://youtube.com/watch?v=example", "duration": 600},
            incomplete=False,
        )
        is None
    )
    assert (
        match_filter({"webpage_url": "https://youtube.com/watch?v=example"}, incomplete=False)
        == "YouTube videos with an unknown duration are not supported"
    )
    assert (
        match_filter(
            {"webpage_url": "https://instagram.com/p/example"}, incomplete=False
        )
        is None
    )


def test_extractor_uses_the_internal_provider_for_youtube_only(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    extractor = YtDlpExtractor(
        max_file_size_bytes=45 * MIB,
        youtube_pot_provider_url="http://youtube-pot-provider:4416",
    )
    extractor.extract("https://youtube.com/shorts/example", tmp_path)

    assert options["extractor_args"] == {
        "youtube": {"player_client": ["mweb"]},
        "youtubepot-bgutilhttp": {"base_url": ["http://youtube-pot-provider:4416"]},
    }


def test_extractor_does_not_configure_the_provider_for_other_platforms(monkeypatch, tmp_path):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    extractor = YtDlpExtractor(
        max_file_size_bytes=45 * MIB,
        youtube_pot_provider_url="http://youtube-pot-provider:4416",
    )
    extractor.extract("https://instagram.com/p/example", tmp_path)

    assert "extractor_args" not in options


@pytest.mark.parametrize(
    ("url", "impersonate"),
    [
        ("https://x.com/alice/status/1", "chrome"),
        ("https://twitter.com/alice/status/1", "chrome"),
        ("https://instagram.com/p/example", None),
        ("https://youtube.com/shorts/example", None),
    ],
)
def test_extractor_uses_chrome_impersonation_only_for_x(monkeypatch, tmp_path, url, impersonate):
    options = {}

    class FakeYoutubeDL:
        def __init__(self, settings):
            options.update(settings)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def extract_info(self, url, download):
            return None

    monkeypatch.setattr("media_downloads.downloader.yt_dlp.YoutubeDL", FakeYoutubeDL)

    YtDlpExtractor(max_file_size_bytes=45 * MIB).extract(url, tmp_path)

    assert options.get("impersonate") == impersonate
