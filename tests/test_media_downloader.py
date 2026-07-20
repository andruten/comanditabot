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
