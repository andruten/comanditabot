"""Safe, temporary public-media downloads backed by yt-dlp."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Protocol

import yt_dlp

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when no safe attachment can be produced."""


class MediaTooLargeError(DownloadError):
    """Raised when a downloaded attachment exceeds the configured limit."""


@dataclass(frozen=True)
class MediaFile:
    path: Path


class Extractor(Protocol):
    def extract(self, url: str, output_directory: Path) -> list[Path]: ...


class MediaDownloader:
    def __init__(self, *, extractor: Extractor, max_file_size_bytes: int) -> None:
        self._extractor = extractor
        self._max_file_size_bytes = max_file_size_bytes

    def download(self, url: str, output_directory: Path) -> list[MediaFile]:
        output_root = output_directory.resolve()
        paths = self._extractor.extract(url, output_root)
        if not paths:
            raise DownloadError("No media was downloaded")

        media_files = []
        for path in paths:
            resolved_path = path.resolve()
            if not resolved_path.is_relative_to(output_root) or not resolved_path.is_file():
                raise DownloadError("Downloaded media is outside the temporary directory")
            if resolved_path.stat().st_size > self._max_file_size_bytes:
                raise MediaTooLargeError("Downloaded media is larger than the configured limit")
            media_files.append(MediaFile(path=resolved_path))
        return media_files


class YtDlpExtractor:
    def __init__(self, *, max_file_size_bytes: int) -> None:
        self._max_file_size_bytes = max_file_size_bytes

    def extract(self, url: str, output_directory: Path) -> list[Path]:
        logger.info("yt-dlp starting public media extraction for %s", _loggable_url(url))
        options = {
            "outtmpl": str(output_directory / "%(id)s.%(ext)s"),
            "noplaylist": False,
            "format": (
                "best[ext=mp4][vcodec!*=vp9][acodec!=none]"
                "/best[ext=mp4][acodec!=none]/best"
            ),
            "max_filesize": self._max_file_size_bytes,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as error:
            logger.warning("yt-dlp failed to download %s: %s", _loggable_url(url), error)
            raise DownloadError("The media could not be downloaded") from error

        downloaded_paths = sorted(
            (path for path in output_directory.iterdir() if path.is_file()),
            key=lambda path: path.stat().st_mtime_ns,
        )
        logger.info(
            "yt-dlp completed %s file(s) for %s: %s",
            len(downloaded_paths),
            _loggable_url(url),
            ", ".join(path.name for path in downloaded_paths),
        )
        return downloaded_paths


def _loggable_url(url: str) -> str:
    return url.split("?", maxsplit=1)[0].split("#", maxsplit=1)[0]
