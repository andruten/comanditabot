"""Recognise the public media URL shapes supported by the bot."""

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Callable
from urllib.parse import parse_qs, urlsplit


URL_PATTERN = re.compile(r"https?://[^\s<>()]+")


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    X = "x"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


_INSTAGRAM_HOSTNAMES = frozenset({"instagram.com"})
_X_HOSTNAMES = frozenset({"x.com", "twitter.com"})
_FACEBOOK_HOSTNAMES = frozenset({"facebook.com", "m.facebook.com"})
_TIKTOK_SHORT_HOSTNAMES = frozenset({"vm.tiktok.com", "vt.tiktok.com"})
_YOUTUBE_HOSTNAMES = frozenset({"youtube.com", "m.youtube.com"})


@dataclass(frozen=True)
class _PlatformRule:
    platform: Platform
    hostnames: frozenset[str]
    validate: Callable[[list[str], str], bool]


def _has_path(path_parts: list[str], _query: str) -> bool:
    return bool(path_parts)


def _is_instagram_media(path_parts: list[str], _query: str) -> bool:
    if len(path_parts) >= 2 and path_parts[0] in {"p", "reel", "reels", "tv"}:
        return True
    return len(path_parts) >= 3 and path_parts[0] == "stories"


def _is_x_media(path_parts: list[str], _query: str) -> bool:
    return len(path_parts) >= 3 and path_parts[1] == "status"


def _is_facebook_media(path_parts: list[str], query: str) -> bool:
    if len(path_parts) >= 2 and path_parts[0] in {"reel", "reels"}:
        return True
    if "videos" in path_parts and path_parts.index("videos") < len(path_parts) - 1:
        return True
    if path_parts and path_parts[0] == "watch" and "v=" in query:
        return True
    if path_parts and path_parts[0] in {"photo.php", "permalink.php"}:
        return "fbid=" in query or "story_fbid=" in query
    return False


def _is_tiktok_media(path_parts: list[str], _query: str) -> bool:
    return len(path_parts) >= 3 and path_parts[-2] == "video"


def _is_youtube_media(path_parts: list[str], query: str) -> bool:
    if len(path_parts) >= 2 and path_parts[0] == "shorts":
        return True
    return path_parts == ["watch"] and bool(parse_qs(query).get("v"))


_PLATFORM_RULES: list[_PlatformRule] = [
    _PlatformRule(Platform.INSTAGRAM, _INSTAGRAM_HOSTNAMES, _is_instagram_media),
    _PlatformRule(Platform.X, _X_HOSTNAMES, _is_x_media),
    _PlatformRule(Platform.FACEBOOK, _FACEBOOK_HOSTNAMES, _is_facebook_media),
    _PlatformRule(Platform.FACEBOOK, frozenset({"fb.watch"}), _has_path),
    _PlatformRule(Platform.TIKTOK, _TIKTOK_SHORT_HOSTNAMES, _has_path),
    _PlatformRule(Platform.TIKTOK, frozenset({"tiktok.com"}), _is_tiktok_media),
    _PlatformRule(Platform.YOUTUBE, _YOUTUBE_HOSTNAMES, _is_youtube_media),
    _PlatformRule(Platform.YOUTUBE, frozenset({"youtu.be"}), _has_path),
]


def classify_url(raw_url: str) -> Platform | None:
    """Return a platform only when *raw_url* is a supported public media URL."""
    parsed = urlsplit(raw_url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return None

    hostname = parsed.hostname.lower().removeprefix("www.")
    path_parts = [part for part in parsed.path.split("/") if part]

    for rule in _PLATFORM_RULES:
        if hostname in rule.hostnames and rule.validate(path_parts, parsed.query):
            return rule.platform
    return None


def supported_urls(text: str) -> list[str]:
    """Return supported media URLs embedded in a Telegram message."""
    urls = []
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,!?;:")
        if classify_url(url) is not None:
            urls.append(url)
    return urls
