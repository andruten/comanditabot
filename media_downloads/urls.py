"""Recognise the public media URL shapes supported by the bot."""

from enum import StrEnum
import re
from urllib.parse import parse_qs, urlsplit


URL_PATTERN = re.compile(r"https?://[^\s<>()]+")


class Platform(StrEnum):
    INSTAGRAM = "instagram"
    X = "x"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


def classify_url(raw_url: str) -> Platform | None:
    """Return a platform only when *raw_url* is a supported public media URL."""
    parsed = urlsplit(raw_url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return None

    hostname = parsed.hostname.lower().removeprefix("www.")
    path_parts = [part for part in parsed.path.split("/") if part]

    if hostname == "instagram.com" and _is_instagram_media(path_parts):
        return Platform.INSTAGRAM
    if hostname in {"x.com", "twitter.com"} and _is_x_media(path_parts):
        return Platform.X
    if hostname == "fb.watch" and path_parts:
        return Platform.FACEBOOK
    if hostname in {"facebook.com", "m.facebook.com"} and _is_facebook_media(
        path_parts, parsed.query
    ):
        return Platform.FACEBOOK
    if hostname in {"vm.tiktok.com", "vt.tiktok.com"} and path_parts:
        return Platform.TIKTOK
    if hostname == "tiktok.com" and _is_tiktok_media(path_parts):
        return Platform.TIKTOK
    if hostname in {"youtube.com", "m.youtube.com"} and _is_youtube_media(
        path_parts, parsed.query
    ):
        return Platform.YOUTUBE
    if hostname == "youtu.be" and path_parts:
        return Platform.YOUTUBE
    return None


def supported_urls(text: str) -> list[str]:
    """Return supported media URLs embedded in a Telegram message."""
    urls = []
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,!?;:")
        if classify_url(url) is not None:
            urls.append(url)
    return urls


def _is_instagram_media(path_parts: list[str]) -> bool:
    if len(path_parts) >= 2 and path_parts[0] in {"p", "reel", "reels", "tv"}:
        return True
    return len(path_parts) >= 3 and path_parts[0] == "stories"


def _is_x_media(path_parts: list[str]) -> bool:
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


def _is_tiktok_media(path_parts: list[str]) -> bool:
    return len(path_parts) >= 3 and path_parts[-2] == "video"


def _is_youtube_media(path_parts: list[str], query: str) -> bool:
    if len(path_parts) >= 2 and path_parts[0] == "shorts":
        return True
    return path_parts == ["watch"] and bool(parse_qs(query).get("v"))
