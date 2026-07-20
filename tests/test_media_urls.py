import pytest

from media_downloads.urls import Platform, classify_url


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.instagram.com/p/example/", Platform.INSTAGRAM),
        ("https://instagram.com/reel/example", Platform.INSTAGRAM),
        ("https://instagram.com/stories/alice/123", Platform.INSTAGRAM),
        ("https://x.com/alice/status/123", Platform.X),
        ("https://twitter.com/alice/status/123", Platform.X),
        ("https://www.facebook.com/alice/videos/123", Platform.FACEBOOK),
        ("https://fb.watch/example", Platform.FACEBOOK),
        ("https://www.tiktok.com/@alice/video/123", Platform.TIKTOK),
        ("https://vm.tiktok.com/ZN819gjqL", Platform.TIKTOK),
    ],
)
def test_classify_url_accepts_supported_public_media(url, platform):
    assert classify_url(url) is platform


@pytest.mark.parametrize(
    "url",
    [
        "http://instagram.com/p/example",
        "https://instagram.com.evil.test/p/example",
        "https://instagram.com/alice",
        "https://x.com/alice",
        "https://facebook.com/groups/example",
        "https://tiktok.com/@alice",
        "https://example.com/video",
    ],
)
def test_classify_url_rejects_unsupported_urls(url):
    assert classify_url(url) is None
