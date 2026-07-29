"""Safe, temporary public-media downloads backed by yt-dlp."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Protocol

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

from .urls import Platform, classify_url

logger = logging.getLogger(__name__)
YOUTUBE_MAX_DURATION_SECONDS = 10 * 60


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
            if (
                not resolved_path.is_relative_to(output_root)
                or not resolved_path.is_file()
            ):
                raise DownloadError(
                    "Downloaded media is outside the temporary directory"
                )
            if resolved_path.stat().st_size > self._max_file_size_bytes:
                raise MediaTooLargeError(
                    "Downloaded media is larger than the configured limit"
                )
            media_files.append(MediaFile(path=resolved_path))
        return media_files


class YtDlpExtractor:
    def __init__(self, *, youtube_pot_provider_url: str | None) -> None:
        self._youtube_pot_provider_url = youtube_pot_provider_url

    def extract(self, url: str, output_directory: Path) -> list[Path]:
        logger.info(
            "yt-dlp starting public media extraction for %s", _loggable_url(url)
        )
        platform = classify_url(url)
        options = {
            "outtmpl": str(output_directory / "%(id)s.%(ext)s"),
            "noplaylist": platform is Platform.YOUTUBE,
            "format": (
                "best[ext=mp4][vcodec!*=vp9][acodec!=none]"
                "/best[ext=mp4][acodec!=none]/best"
            ),
            "match_filter": _youtube_duration_filter,
            "quiet": True,
            "no_warnings": True,
        }
        _apply_platform_options(options, platform, self._youtube_pot_provider_url)
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as error:
            logger.warning(
                "yt-dlp failed to download %s: %s", _loggable_url(url), error
            )
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


def _apply_platform_options(
    options: dict,
    platform: Platform | None,
    youtube_pot_provider_url: str | None,
) -> None:
    if platform is Platform.X:
        options["impersonate"] = ImpersonateTarget.from_str("chrome")
        logger.info("yt-dlp using Chrome impersonation for public X media")
    if platform is Platform.INSTAGRAM:
        options["ignore_no_formats_error"] = True
        options["lazy_playlist"] = True
        logger.info("yt-dlp will skip unavailable media inside an Instagram carousel")
    if platform is Platform.YOUTUBE and youtube_pot_provider_url is not None:
        options["extractor_args"] = {
            "youtube": {"player_client": ["mweb"]},
            "youtubepot-bgutilhttp": {"base_url": [youtube_pot_provider_url]},
        }
        options["js_runtimes"] = {"node": {}}
        logger.info(
            "yt-dlp using the internal PO Token provider for public YouTube media"
        )


def _loggable_url(url: str) -> str:
    return url.split("?", maxsplit=1)[0].split("#", maxsplit=1)[0]


def _youtube_duration_filter(info: dict, *, incomplete: bool) -> str | None:
    if incomplete:
        return None

    webpage_url = info.get("webpage_url") or info.get("original_url")
    if not webpage_url or classify_url(webpage_url) is not Platform.YOUTUBE:
        return None

    duration = info.get("duration")
    if duration is None:
        return "YouTube videos with an unknown duration are not supported"
    if duration > YOUTUBE_MAX_DURATION_SECONDS:
        return "YouTube videos longer than 10 minutes are not supported"
    return None
