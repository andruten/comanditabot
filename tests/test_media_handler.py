from pathlib import Path
from types import SimpleNamespace

import pytest

from media_downloads.downloader import DownloadError, MediaFile
from media_downloads.handler import (
    MediaDownloadHandler,
    MediaDownloadHandlerFactory,
    SlidingWindowRateLimiter,
)


class RecordingMessage:
    def __init__(self, text):
        self.text = text
        self.photo_replies = []
        self.video_replies = []
        self.animation_replies = []
        self.document_replies = []
        self.text_replies = []

    async def reply_photo(self, photo):
        self.photo_replies.append(Path(photo.name).name)

    async def reply_video(self, video):
        self.video_replies.append(Path(video.name).name)

    async def reply_animation(self, animation):
        self.animation_replies.append(Path(animation.name).name)

    async def reply_document(self, document):
        self.document_replies.append(Path(document.name).name)

    async def reply_text(self, text):
        self.text_replies.append(text)


class FakeDownloader:
    def __init__(self, names):
        self.names = names

    def download(self, url, output_directory):
        files = []
        for name in self.names:
            path = output_directory / name
            path.write_bytes(b"media")
            files.append(MediaFile(path))
        return files


class FailingDownloader:
    def download(self, url, output_directory):
        raise DownloadError("not available")


def update_for(message, user_id=42):
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(id=-100),
    )


def context_for_bot():
    async def send_chat_action(**kwargs):
        return None

    return SimpleNamespace(bot=SimpleNamespace(send_chat_action=send_chat_action))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("name", "reply_attribute"),
    [
        ("image.jpg", "photo_replies"),
        ("clip.mp4", "video_replies"),
        ("loop.gif", "animation_replies"),
        ("archive.bin", "document_replies"),
    ],
)
async def test_supported_link_replies_with_matching_attachment(name, reply_attribute):
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = MediaDownloadHandler(downloader=FakeDownloader([name]))

    await handler.process(update_for(message), context_for_bot())

    assert getattr(message, reply_attribute) == [name]


@pytest.mark.asyncio
async def test_unsupported_link_is_silent():
    message = RecordingMessage("https://example.com/video")
    handler = MediaDownloadHandler(downloader=FakeDownloader(["image.jpg"]))

    await handler.process(update_for(message), context_for_bot())

    assert message.photo_replies == []
    assert message.text_replies == []


@pytest.mark.asyncio
async def test_download_failure_replies_with_a_concise_error():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = MediaDownloadHandler(downloader=FailingDownloader())

    await handler.process(update_for(message), context_for_bot())

    assert message.text_replies == ["No se ha podido descargar este enlace."]


@pytest.mark.asyncio
async def test_rate_limiter_replies_without_starting_a_fourth_download():
    message = RecordingMessage("https://x.com/alice/status/1")
    limiter = SlidingWindowRateLimiter(limit=3, period_seconds=60)
    handler = MediaDownloadHandler(downloader=FakeDownloader(["image.jpg"]), rate_limiter=limiter)

    for _ in range(4):
        await handler.process(update_for(message), context_for_bot())

    assert message.text_replies == ["Has alcanzado el límite de descargas. Inténtalo más tarde."]


def test_media_handler_has_priority_over_reactions():
    from comandita import configure_handlers

    application = SimpleNamespace(handlers=[])
    application.add_handler = lambda handler, group=0: application.handlers.append((group, handler))

    configure_handlers(application)

    group, handler = application.handlers[0]
    assert group == -1
    assert isinstance(handler, MediaDownloadHandlerFactory)
