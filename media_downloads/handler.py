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
from telegram.error import TelegramError
from telegram.ext import CallbackContext, MessageHandler, filters

from .downloader import (
    DownloadError,
    MediaDownloader,
    MediaTooLargeError,
    VIDEO_EXTENSIONS,
    YtDlpExtractor,
)
from .urls import Platform, classify_url, supported_urls

MAX_TELEGRAM_THUMBNAIL_SIZE_BYTES = 200 * 1024
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
COMPRESSION_TARGET_MARGIN_BYTES = 2 * 1024 * 1024
COMPRESSED_AUDIO_KBPS = 96
MINIMUM_VIDEO_BITRATE_KBPS = 150
ENCODE_PRESET = "veryfast"
MAX_COMPRESSED_HEIGHT = 720
SCALE_FILTER = f"scale=-2:'min({MAX_COMPRESSED_HEIGHT},ih)'"
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


class VideoDimensionExtractor:
    def extract(self, video_path: Path) -> tuple[int, int] | None:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            width, height = result.stdout.strip().split(",")
            return int(width), int(height)
        except (OSError, subprocess.CalledProcessError, ValueError):
            return None


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


class VideoCompressor:
    def __init__(self, *, max_file_size_bytes: int) -> None:
        self._max_file_size_bytes = max_file_size_bytes
        target_size_bytes = max_file_size_bytes - COMPRESSION_TARGET_MARGIN_BYTES
        self._target_size_bytes = (
            target_size_bytes if target_size_bytes > 0 else max_file_size_bytes
        )

    def compress_if_needed(self, video_path: Path) -> Path | None:
        if video_path.suffix.lower() not in VIDEO_EXTENSIONS:
            return video_path
        if video_path.stat().st_size <= self._target_size_bytes:
            return video_path
        logger.info(
            "Compressing %s (%.1f MiB) to fit the Telegram size limit",
            video_path.name,
            video_path.stat().st_size / (1024 * 1024),
        )
        compressed_path = video_path.with_suffix(".compressed.mp4")
        duration_seconds = self._probe_duration(video_path)
        if duration_seconds is not None:
            compressed = self._two_pass_encode(
                video_path, compressed_path, duration_seconds
            )
        else:
            compressed = self._constant_quality_encode(
                video_path, compressed_path, crf=23
            )
            if compressed and self._exceeds_limit(compressed_path):
                logger.info(
                    "Retrying compression of %s with lower quality", video_path.name
                )
                compressed = self._constant_quality_encode(
                    video_path, compressed_path, crf=28
                )
        if not compressed or self._exceeds_limit(compressed_path):
            logger.warning(
                "Could not compress %s below the size limit", video_path.name
            )
            return None
        logger.info(
            "Compressed %s: %.1f MiB -> %.1f MiB",
            video_path.name,
            video_path.stat().st_size / (1024 * 1024),
            compressed_path.stat().st_size / (1024 * 1024),
        )
        return compressed_path

    def _probe_duration(self, video_path: Path) -> float | None:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except (OSError, subprocess.CalledProcessError, ValueError):
            return None

    def _two_pass_encode(
        self, source: Path, target: Path, duration_seconds: float
    ) -> bool:
        total_kbps = (self._target_size_bytes * 8 / 1000) / duration_seconds
        video_kbps = max(
            int(total_kbps) - COMPRESSED_AUDIO_KBPS, MINIMUM_VIDEO_BITRATE_KBPS
        )
        common_options = [
            "-c:v",
            "libx264",
            "-preset",
            ENCODE_PRESET,
            "-vf",
            SCALE_FILTER,
            "-b:v",
            f"{video_kbps}k",
            "-passlogfile",
            str(target.with_suffix(".passes")),
        ]
        return self._run_ffmpeg(
            [
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    *common_options,
                    "-pass",
                    "1",
                    "-an",
                    "-f",
                    "mp4",
                    os.devnull,
                ],
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    *common_options,
                    "-pass",
                    "2",
                    "-maxrate",
                    f"{int(video_kbps * 1.5)}k",
                    "-bufsize",
                    f"{video_kbps * 2}k",
                    "-c:a",
                    "aac",
                    "-b:a",
                    f"{COMPRESSED_AUDIO_KBPS}k",
                    "-movflags",
                    "+faststart",
                    str(target),
                ],
            ]
        )

    def _constant_quality_encode(self, source: Path, target: Path, *, crf: int) -> bool:
        return self._run_ffmpeg(
            [
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-c:v",
                    "libx264",
                    "-preset",
                    ENCODE_PRESET,
                    "-vf",
                    SCALE_FILTER,
                    "-crf",
                    str(crf),
                    "-c:a",
                    "aac",
                    "-b:a",
                    f"{COMPRESSED_AUDIO_KBPS}k",
                    "-movflags",
                    "+faststart",
                    str(target),
                ]
            ]
        )

    def _run_ffmpeg(self, commands: list[list[str]]) -> bool:
        for command in commands:
            try:
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (OSError, subprocess.CalledProcessError):
                logger.warning("ffmpeg compression failed for %s", command[-1])
                return False
        return True

    def _exceeds_limit(self, video_path: Path) -> bool:
        return video_path.stat().st_size > self._max_file_size_bytes


class MediaReplyDispatcher:
    def __init__(
        self,
        thumbnail_generator: VideoThumbnailGenerator | None = None,
        dimension_extractor: VideoDimensionExtractor | None = None,
    ) -> None:
        self._thumbnail_generator = thumbnail_generator or VideoThumbnailGenerator()
        self._dimension_extractor = dimension_extractor or VideoDimensionExtractor()

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
        thumbnail_path, dimensions = await asyncio.gather(
            asyncio.to_thread(self._thumbnail_generator.generate, path),
            asyncio.to_thread(self._dimension_extractor.extract, path),
        )
        send_kwargs: dict[str, int] = {}
        if dimensions:
            send_kwargs["width"] = dimensions[0]
            send_kwargs["height"] = dimensions[1]
        if (
            thumbnail_path
            and thumbnail_path.is_file()
            and thumbnail_path.stat().st_size <= MAX_TELEGRAM_THUMBNAIL_SIZE_BYTES
        ):
            with thumbnail_path.open("rb") as thumbnail:
                await message.reply_video(
                    attachment, thumbnail=thumbnail, **send_kwargs
                )
            logger.info("Sent video attachment with thumbnail: %s", path.name)
        else:
            await message.reply_video(attachment, **send_kwargs)
            logger.info("Sent video attachment without thumbnail: %s", path.name)


class MediaDownloadHandler:
    def __init__(
        self,
        *,
        downloader: MediaDownloader,
        rate_limiter: SlidingWindowRateLimiter,
        reply_dispatcher: MediaReplyDispatcher,
        video_compressor: VideoCompressor,
        youtube_enabled: bool,
    ) -> None:
        self._downloader = downloader
        self._rate_limiter = rate_limiter
        self._reply_dispatcher = reply_dispatcher
        self._video_compressor = video_compressor
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
            video_compressor=VideoCompressor(
                max_file_size_bytes=settings.max_file_size_bytes
            ),
            youtube_enabled=settings.youtube_enabled,
        )

    async def _set_reaction_safely(self, message, reaction: str) -> None:
        try:
            await message.set_reaction(reaction)
        except TelegramError:
            logger.warning("Could not set reaction %s", reaction)

    async def process(self, update: Update, context: CallbackContext) -> None:
        message = update.effective_message
        if not message or not message.text or not update.effective_user:
            return

        urls = supported_urls(message.text)
        if not urls:
            return

        await self._set_reaction_safely(message, ReactionEmoji.EYES)
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
                        media_path = await asyncio.to_thread(
                            self._video_compressor.compress_if_needed,
                            media_file.path,
                        )
                        if media_path is None:
                            raise DownloadError(
                                "The media could not be compressed to fit the limit"
                            )
                        await self._reply_dispatcher.send(message, media_path)
                    await self._set_reaction_safely(message, ReactionEmoji.THUMBS_UP)
            except MediaTooLargeError:
                logger.warning("Media too large for %s media", platform)
                await self._set_reaction_safely(message, ReactionEmoji.THUMBS_DOWN)
            except DownloadError as error:
                logger.warning("Failed %s media download: %s", platform, error)
                await self._set_reaction_safely(message, ReactionEmoji.THUMBS_DOWN)


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
