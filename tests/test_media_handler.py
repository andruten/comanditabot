import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from telegram.constants import ReactionEmoji

from media_downloads.downloader import (
    DownloadError,
    MediaFile,
    MediaTooLargeError,
)
from media_downloads.handler import (
    MediaDownloadHandler,
    MediaMessageHandler,
    MediaReplyDispatcher,
    SlidingWindowRateLimiter,
)


class RecordingMessage:
    def __init__(self, text):
        self.text = text
        self.photo_replies = []
        self.video_replies = []
        self.video_thumbnails = []
        self.animation_replies = []
        self.document_replies = []
        self.text_replies = []
        self.reactions = []

    async def reply_photo(self, photo):
        self.photo_replies.append(Path(photo.name).name)

    async def reply_video(self, video, thumbnail=None):
        self.video_replies.append(Path(video.name).name)
        self.video_thumbnails.append(Path(thumbnail.name).name if thumbnail else None)

    async def reply_animation(self, animation):
        self.animation_replies.append(Path(animation.name).name)

    async def reply_document(self, document):
        self.document_replies.append(Path(document.name).name)

    async def reply_text(self, text):
        self.text_replies.append(text)

    async def set_reaction(self, reaction):
        self.reactions.append(reaction)


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


class FakeThumbnailGenerator:
    def generate(self, video_path):
        thumbnail = video_path.with_suffix(".thumbnail.jpg")
        thumbnail.write_bytes(b"thumbnail")
        return thumbnail


class NoThumbnailGenerator:
    def generate(self, video_path):
        return None


class OversizedThumbnailGenerator:
    def generate(self, video_path):
        thumbnail = video_path.with_suffix(".thumbnail.jpg")
        thumbnail.write_bytes(b"thumbnail" * (200 * 1024 // len(b"thumbnail") + 1))
        return thumbnail


def update_for(message, user_id=42):
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(id=-100),
    )


def _default_handler(**overrides):
    defaults = dict(
        downloader=FakeDownloader(["image.jpg"]),
        rate_limiter=SlidingWindowRateLimiter(limit=10, period_seconds=60),
        reply_dispatcher=MediaReplyDispatcher(),
        youtube_enabled=True,
    )
    defaults.update(overrides)
    return MediaDownloadHandler(**defaults)


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
    handler = _default_handler(downloader=FakeDownloader([name]))

    await handler.process(update_for(message), context_for_bot())

    assert getattr(message, reply_attribute) == [name]


@pytest.mark.asyncio
async def test_unsupported_link_is_silent():
    message = RecordingMessage("https://example.com/video")
    handler = _default_handler(downloader=FakeDownloader(["image.jpg"]))

    await handler.process(update_for(message), context_for_bot())

    assert message.photo_replies == []
    assert message.text_replies == []
    assert message.reactions == []


@pytest.mark.asyncio
async def test_youtube_link_is_silent_when_the_platform_is_disabled():
    class RecordingDownloader:
        def __init__(self):
            self.urls = []

        def download(self, url, output_directory):
            self.urls.append(url)
            return []

    downloader = RecordingDownloader()
    message = RecordingMessage("https://youtube.com/shorts/example")
    handler = _default_handler(downloader=downloader, youtube_enabled=False)

    await handler.process(update_for(message), context_for_bot())

    assert downloader.urls == []
    assert message.text_replies == []
    assert message.reactions == []


@pytest.mark.asyncio
async def test_download_failure_reacts_with_thumbs_down():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(downloader=FailingDownloader())

    await handler.process(update_for(message), context_for_bot())

    assert message.reactions == [ReactionEmoji.EYES, ReactionEmoji.THUMBS_DOWN]
    assert message.text_replies == []


class OversizedDownloader:
    def download(self, url, output_directory):
        raise MediaTooLargeError("too large")


@pytest.mark.asyncio
async def test_oversized_media_reacts_with_thumbs_down():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(downloader=OversizedDownloader())

    await handler.process(update_for(message), context_for_bot())

    assert message.reactions == [ReactionEmoji.EYES, ReactionEmoji.THUMBS_DOWN]
    assert message.text_replies == []


@pytest.mark.asyncio
async def test_successful_download_reacts_with_eyes_then_thumbs_up():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(downloader=FakeDownloader(["image.jpg"]))

    await handler.process(update_for(message), context_for_bot())

    assert message.reactions == [ReactionEmoji.EYES, ReactionEmoji.THUMBS_UP]
    assert message.text_replies == []


@pytest.mark.asyncio
async def test_successful_download_logs_the_platform_and_attachment_count(caplog):
    caplog.set_level(logging.INFO, logger="media_downloads.handler")
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(downloader=FakeDownloader(["image.jpg"]))

    await handler.process(update_for(message), context_for_bot())

    assert "Downloaded 1 attachment(s) for x media" in caplog.messages


@pytest.mark.asyncio
async def test_video_reply_includes_a_generated_thumbnail():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(
        downloader=FakeDownloader(["clip.mp4"]),
        reply_dispatcher=MediaReplyDispatcher(
            thumbnail_generator=FakeThumbnailGenerator()
        ),
    )

    await handler.process(update_for(message), context_for_bot())

    assert message.video_replies == ["clip.mp4"]
    assert message.video_thumbnails == ["clip.thumbnail.jpg"]


@pytest.mark.asyncio
async def test_video_reply_still_sends_when_thumbnail_generation_fails():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(
        downloader=FakeDownloader(["clip.mp4"]),
        reply_dispatcher=MediaReplyDispatcher(
            thumbnail_generator=NoThumbnailGenerator()
        ),
    )

    await handler.process(update_for(message), context_for_bot())

    assert message.video_replies == ["clip.mp4"]
    assert message.video_thumbnails == [None]


@pytest.mark.asyncio
async def test_video_reply_omits_a_thumbnail_that_is_too_large():
    message = RecordingMessage("https://x.com/alice/status/1")
    handler = _default_handler(
        downloader=FakeDownloader(["clip.mp4"]),
        reply_dispatcher=MediaReplyDispatcher(
            thumbnail_generator=OversizedThumbnailGenerator()
        ),
    )

    await handler.process(update_for(message), context_for_bot())

    assert message.video_replies == ["clip.mp4"]
    assert message.video_thumbnails == [None]


@pytest.mark.asyncio
async def test_rate_limiter_replies_without_starting_a_fourth_download():
    message = RecordingMessage("https://x.com/alice/status/1")
    limiter = SlidingWindowRateLimiter(limit=3, period_seconds=60)
    handler = _default_handler(
        downloader=FakeDownloader(["image.jpg"]), rate_limiter=limiter
    )

    for _ in range(4):
        await handler.process(update_for(message), context_for_bot())

    assert message.text_replies == [
        "Has alcanzado el límite de descargas. Inténtalo más tarde."
    ]


def test_media_handler_has_priority_over_reactions():
    from comandita import configure_handlers

    application = SimpleNamespace(handlers=[])
    application.add_handler = lambda handler, group=0: application.handlers.append(
        (group, handler)
    )

    configure_handlers(application)

    group, handler = application.handlers[0]
    assert group == -1
    assert isinstance(handler, MediaMessageHandler)
