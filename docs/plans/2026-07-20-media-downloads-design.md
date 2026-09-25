# Media downloads design

Comandita will download public media from Instagram, X, Facebook, and TikTok in both direct and group chats. A dedicated handler will run before the existing reaction handler, so a supported link is handled once and never triggers the URL punishment or random MiMiMi reaction.

It accepts only HTTPS URLs with exact platform domains and known media paths. The handler limits requests per Telegram user and downloads each accepted URL outside the event loop with `yt-dlp`, using a fresh temporary directory below `/tmp`. No credentials, cookies, or private content are used. Files are deleted after the response, and each file has a size limit.

The bot replies to the source message: photos are sent as photos, videos as videos, GIFs as animations, and other downloaded formats as documents. A short error is sent only if a recognised URL cannot be processed. The image adds `ffmpeg`, and the Helm release receives more CPU and memory while retaining its read-only filesystem and `/tmp` `emptyDir`.
