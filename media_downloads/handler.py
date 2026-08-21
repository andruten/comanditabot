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
from telegram.constants import ChatAction, ReactionEmoji
from telegram.ext import CallbackContext, MessageHandler, filters

from .downloader import (
    DownloadError,
    MediaDownloader,
    MediaTooLargeError,
    YtDlpExtractor,
)
from .urls import Platform, classify_url, supported_urls

MAX_TELEGRAM_THUMBNAIL_SIZE_BYTES = 200 * 1024
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".webm"})
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaSettings:
    max_file_size_bytes: int
    max_downloads_per_minute: int
    youtube_enabled: bool
    youtube_pot_provider_url: str | None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "MediaSettings":
        return cls(
            max_file_size_bytes=_positive_int(env, "MEDIA_MAX_FILE_SIZE_MB", default=45)
            * 1024
            * 1024,
            max_downloads_per_minute=_positive_int(
                env, "MEDIA_MAX_DOWNLOADS_PER_MINUTE", default=10
            ),
            youtube_enabled=_boolean(env, "MEDIA_ENABLE_YOUTUBE", default=True),
            youtube_pot_provider_url=env.get("YOUTUBE_POT_PROVIDER_URL") or None,
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


class MediaReplyDispatcher:
    def __init__(
        self, thumbnail_generator: VideoThumbnailGenerator | None = None
    ) -> None:
        self._thumbnail_generator = thumbnail_generator or VideoThumbnailGenerator()

    async def send(self, message, path: Path) -> None:
        suffix = path.suffix.lower()
        with path.open("rb") as attachment:
            if suffix in IMAGE_EXTENSIONS:
                await message.reply_photo(attachment)
            elif suffix in VIDEO_EXTENSIONS:
                await self._send_video(message, attachment, path)
            elif suffix == ".gif":
                await message.reply_animation(attachment)
            else:
                await message.reply_document(attachment)

    async def _send_video(self, message, attachment, path: Path) -> None:
        thumbnail_path = await asyncio.to_thread(
            self._thumbnail_generator.generate, path
        )
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


class MediaDownloadHandler:
    def __init__(
        self,
        *,
        downloader: MediaDownloader,
        rate_limiter: SlidingWindowRateLimiter,
        reply_dispatcher: MediaReplyDispatcher,
        youtube_enabled: bool,
    ) -> None:
        self._downloader = downloader
        self._rate_limiter = rate_limiter
        self._reply_dispatcher = reply_dispatcher
        self._youtube_enabled = youtube_enabled

    @classmethod
    def from_env(cls) -> "MediaDownloadHandler":
        settings = MediaSettings.from_env(os.environ)
        return cls(
            downloader=MediaDownloader(
                extractor=YtDlpExtractor(
                    youtube_pot_provider_url=settings.youtube_pot_provider_url,
                ),
                max_file_size_bytes=settings.max_file_size_bytes,
            ),
            rate_limiter=SlidingWindowRateLimiter(
                limit=settings.max_downloads_per_minute, period_seconds=60
            ),
            reply_dispatcher=MediaReplyDispatcher(),
            youtube_enabled=settings.youtube_enabled,
        )

    async def process(self, update: Update, context: CallbackContext) -> None:
        message = update.effective_message
        if not message or not message.text or not update.effective_user:
            return

        urls = supported_urls(message.text)
        if not urls:
            return

        await message.set_reaction(ReactionEmoji.EYES)
        for url in urls:
            platform = classify_url(url)
            if platform is Platform.YOUTUBE and not self._youtube_enabled:
                logger.info("Ignoring YouTube media because it is disabled")
                continue
            if not self._rate_limiter.allow(str(update.effective_user.id)):
                logger.warning("Rate limit reached for %s media", platform)
                await message.reply_text(
                    "Has alcanzado el límite de descargas. Inténtalo más tarde."
                )
                return

            try:
                logger.info("Starting %s media download", platform)
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT
                )
                with TemporaryDirectory(
                    prefix="comandita-media-", dir="/tmp"
                ) as temporary_dir:
                    media_files = await asyncio.to_thread(
                        self._downloader.download, url, Path(temporary_dir)
                    )
                    logger.info(
                        "Downloaded %s attachment(s) for %s media",
                        len(media_files),
                        platform,
                    )
                    for media_file in media_files:
                        await self._reply_dispatcher.send(message, media_file.path)
                    await message.set_reaction(ReactionEmoji.THUMBS_UP)
            except MediaTooLargeError:
                logger.warning("Media too large for %s media", platform)
                await message.set_reaction(ReactionEmoji.THUMBS_DOWN)
            except DownloadError as error:
                logger.warning("Failed %s media download: %s", platform, error)
                await message.set_reaction(ReactionEmoji.THUMBS_DOWN)


class MediaMessageHandler(MessageHandler):
    def __init__(self) -> None:
        self._handler = MediaDownloadHandler.from_env()
        super().__init__(filters.TEXT & ~filters.COMMAND, self._handle)

    async def _handle(self, update: Update, context: CallbackContext) -> None:
        await self._handler.process(update, context)


def _positive_int(env: Mapping[str, str], name: str, *, default: int) -> int:
    raw_value = env.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer") from error
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _boolean(env: Mapping[str, str], name: str, *, default: bool) -> bool:
    raw_value = env.get(name)
    if raw_value is None:
        return default
    if raw_value.lower() == "true":
        return True
    if raw_value.lower() == "false":
        return False
    raise ValueError(f"{name} must be true or false")
