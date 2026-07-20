"""Telegram handler that replies to supported public-media links."""

import asyncio
import re
from collections import defaultdict, deque
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, MessageHandler, filters

from .downloader import DownloadError, MediaDownloader, YtDlpExtractor
from .urls import classify_url

MAX_FILE_SIZE_BYTES = 45 * 1024 * 1024
MAX_DOWNLOADS_PER_MINUTE = 3
URL_PATTERN = re.compile(r"https?://[^\s<>()]+")


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


class MediaDownloadHandler:
    def __init__(self, *, downloader=None, rate_limiter=None) -> None:
        self._downloader = downloader or MediaDownloader(
            extractor=YtDlpExtractor(max_file_size_bytes=MAX_FILE_SIZE_BYTES),
            max_file_size_bytes=MAX_FILE_SIZE_BYTES,
        )
        self._rate_limiter = rate_limiter or SlidingWindowRateLimiter(
            limit=MAX_DOWNLOADS_PER_MINUTE, period_seconds=60
        )

    async def process(self, update: Update, context: CallbackContext) -> None:
        message = update.effective_message
        if not message or not message.text or not update.effective_user:
            return

        for url in _supported_urls(message.text):
            if not self._rate_limiter.allow(str(update.effective_user.id)):
                await message.reply_text("Has alcanzado el límite de descargas. Inténtalo más tarde.")
                return

            try:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT
                )
                with TemporaryDirectory(prefix="comandita-media-", dir="/tmp") as temporary_dir:
                    media_files = await asyncio.to_thread(
                        self._downloader.download, url, Path(temporary_dir)
                    )
                    for media_file in media_files:
                        await _reply_with_attachment(message, media_file.path)
            except DownloadError:
                await message.reply_text("No se ha podido descargar este enlace.")


class MediaDownloadHandlerFactory(MessageHandler):
    def __init__(self) -> None:
        self._handler = MediaDownloadHandler()
        super().__init__(filters.TEXT & ~filters.COMMAND, self.process)

    async def process(self, update: Update, context: CallbackContext) -> None:
        await self._handler.process(update, context)


def _supported_urls(text: str) -> list[str]:
    urls = []
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,!?;:")
        if classify_url(url) is not None:
            urls.append(url)
    return urls


async def _reply_with_attachment(message, path: Path) -> None:
    suffix = path.suffix.lower()
    with path.open("rb") as attachment:
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            await message.reply_photo(attachment)
        elif suffix in {".mp4", ".mov", ".m4v", ".webm"}:
            await message.reply_video(attachment)
        elif suffix == ".gif":
            await message.reply_animation(attachment)
        else:
            await message.reply_document(attachment)
