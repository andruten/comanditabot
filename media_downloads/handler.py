"""Telegram handler that replies to supported public-media links."""

import asyncio
import logging
import os
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Mapping

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, MessageHandler, filters

from .downloader import DownloadError, MediaDownloader, YtDlpExtractor
from .urls import classify_url, supported_urls

MAX_TELEGRAM_THUMBNAIL_SIZE_BYTES = 200 * 1024
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaSettings:
    max_file_size_bytes: int
    max_downloads_per_minute: int

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "MediaSettings":
        return cls(
            max_file_size_bytes=_positive_int(env, "MEDIA_MAX_FILE_SIZE_MB", default=45) * 1024 * 1024,
            max_downloads_per_minute=_positive_int(
                env, "MEDIA_MAX_DOWNLOADS_PER_MINUTE", default=10
            ),
        )


class SlidingWindowRateLimiter:
    def __init__(self, *, limit: int, period_seconds: float) -> None:
        self._limit = limit
        self._period_seconds = period_seconds
        self._events = defaultdict(deque)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        event_time = monotonic() if now is None else now
        events = self._events[key]
        cutoff = event_time - self._period_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self._limit:
            return False
        events.append(event_time)
        return True


class VideoThumbnailGenerator:
    def generate(self, video_path: Path) -> Path | None:
        thumbnail_path = video_path.with_suffix(".thumbnail.jpg")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    "1",
                    "-i",
                    str(video_path),
                    "-frames:v",
                    "1",
                    "-vf",
                    "scale=320:-2",
                    "-q:v",
                    "5",
                    str(thumbnail_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            logger.warning("Could not generate thumbnail for %s", video_path.name)
            return None
        if thumbnail_path.is_file() and thumbnail_path.stat().st_size:
            logger.info("Generated thumbnail for %s", video_path.name)
            return thumbnail_path
        logger.warning("No thumbnail frame generated for %s", video_path.name)
        return None


class MediaDownloadHandler:
    def __init__(self, *, downloader=None, rate_limiter=None, thumbnail_generator=None) -> None:
        settings = MediaSettings.from_env(os.environ)
        self._downloader = downloader or MediaDownloader(
            extractor=YtDlpExtractor(max_file_size_bytes=settings.max_file_size_bytes),
            max_file_size_bytes=settings.max_file_size_bytes,
        )
        self._rate_limiter = rate_limiter or SlidingWindowRateLimiter(
            limit=settings.max_downloads_per_minute, period_seconds=60
        )
        self._thumbnail_generator = thumbnail_generator or VideoThumbnailGenerator()

    async def process(self, update: Update, context: CallbackContext) -> None:
        message = update.effective_message
        if not message or not message.text or not update.effective_user:
            return

        for url in supported_urls(message.text):
            platform = classify_url(url)
            if not self._rate_limiter.allow(str(update.effective_user.id)):
                logger.warning("Rate limit reached for %s media", platform)
                await message.reply_text("Has alcanzado el límite de descargas. Inténtalo más tarde.")
                return

            try:
                logger.info("Starting %s media download", platform)
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT
                )
                with TemporaryDirectory(prefix="comandita-media-", dir="/tmp") as temporary_dir:
                    media_files = await asyncio.to_thread(
                        self._downloader.download, url, Path(temporary_dir)
                    )
                    logger.info("Downloaded %s attachment(s) for %s media", len(media_files), platform)
                    for media_file in media_files:
                        await _reply_with_attachment(
                            message, media_file.path, self._thumbnail_generator
                        )
            except DownloadError as error:
                logger.warning("Failed %s media download: %s", platform, error)
                await message.reply_text("No se ha podido descargar este enlace.")


class MediaDownloadHandlerFactory(MessageHandler):
    def __init__(self) -> None:
        self._handler = MediaDownloadHandler()
        super().__init__(filters.TEXT & ~filters.COMMAND, self.process)

    async def process(self, update: Update, context: CallbackContext) -> None:
        await self._handler.process(update, context)


async def _reply_with_attachment(message, path: Path, thumbnail_generator) -> None:
    suffix = path.suffix.lower()
    with path.open("rb") as attachment:
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            await message.reply_photo(attachment)
        elif suffix in {".mp4", ".mov", ".m4v", ".webm"}:
            thumbnail_path = await asyncio.to_thread(thumbnail_generator.generate, path)
            if (
                thumbnail_path
                and thumbnail_path.is_file()
                and thumbnail_path.stat().st_size <= MAX_TELEGRAM_THUMBNAIL_SIZE_BYTES
            ):
                with thumbnail_path.open("rb") as thumbnail:
                    await message.reply_video(attachment, thumbnail=thumbnail)
                logger.info("Sent video attachment with thumbnail: %s", path.name)
            else:
                await message.reply_video(attachment)
                logger.info("Sent video attachment without thumbnail: %s", path.name)
        elif suffix == ".gif":
            await message.reply_animation(attachment)
        else:
            await message.reply_document(attachment)


def _positive_int(env: Mapping[str, str], name: str, *, default: int) -> int:
    raw_value = env.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer") from error
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value
