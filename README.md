# Woof! Woof!

Welcome to Comandita bot 🐾.

## Available commands

### MiMiMi

```
/mimimi
```

Translates the replied-to message into *mimimi* speak. Reply to its own answer
with `/mimimi` again and it will give you the original text back.

### Weather in Korea

```
/tiempoencorea
```

Current weather in Seoul, powered by OpenWeatherMap. If Korea is asleep
(00:00–08:00 KST) the bot will complain first.

### Save a message

```
/star
```

Saves the replied-to message and sends it to you in a private chat. If the bot
cannot reach you it will ask you to start a conversation with it first
(https://t.me/comandita_bot).

### Punish a message

```
/sentenciador
```

Replies with a random punishment phrase.

### Chat statistics

```
/stats
```

Today's statistics for the chat: messages, photos, videos and audios.

## Automatic reactions

Beyond commands, the bot reacts to plain text messages:

| Trigger | Reaction |
| --- | --- |
| Message contains `digi` | "Woof! Woof!" |
| Message contains `brey`, `rajoy` or `mariano` | Random Rajoy phrase |
| Message contains `zapatero` or `zp` | Random Zapatero phrase |
| Message contains `niño`, `niña`, `hijo`, `hija`, `papá`, `papi` | 🚨🚨 Kids Alert! 🚨🚨 |
| Message contains `estuve en` or `fui a` | "Anda que avisas... El grupo está roto." |
| Any message (1% chance) | The message translated to mimimi |
| A bare URL (10% chance) | A punishment phrase |

The "Kids Alert" and "broken group" reactions quote the original message. All
of these are skipped when the message contains a supported media URL.

## Public media downloads

Send a public Instagram, X/Twitter, Facebook, TikTok, or YouTube media URL to
Comandita in a private chat or a group. The bot replies with the photos,
videos, GIFs, or documents from that post. It never uses credentials or cookies
and cannot download private content. Only HTTPS links are accepted.

Supported YouTube URLs are `youtube.com/watch?v=...`, `youtube.com/shorts/...`
and `youtu.be/...` links, capped at 10 minutes of duration. Videos are sent
with a thumbnail generated via `ffmpeg` and their real dimensions.

While a download is in progress the bot reacts to your message with 👀, then
👍 when it succeeds or 👎 when it fails or the media exceeds the size limit.

For groups, disable the bot's Privacy Mode in BotFather (`/setprivacy`) so
Telegram delivers regular link messages to it. The defaults are 10 downloads
per user per minute and 45 MiB per attachment; when the rate limit is hit the
bot asks you to try again later. Configure them with
`MEDIA_MAX_DOWNLOADS_PER_MINUTE` and `MEDIA_MAX_FILE_SIZE_MB`.

## Configuration

All configuration lives in a `.env` file passed to the container. Every `make`
target requires it to exist; `check_env` copies `env.sample` automatically the
first time, and dummy values are fine — except `BOT_TOKEN` when actually
running the bot.

| Variable | Default | Description |
| --- | --- | --- |
| `BOT_TOKEN` | — | Telegram bot token from BotFather (required) |
| `OPEN_WEATHER_MAP_APP_ID` | — | OpenWeatherMap API key for `/tiempoencorea` |
| `LOG_LEVEL` | `INFO` | Log level for the bot's loggers |
| `MEDIA_MAX_DOWNLOADS_PER_MINUTE` | `10` | Per-user sliding-window download rate limit |
| `MEDIA_MAX_FILE_SIZE_MB` | `45` | Maximum size per attachment sent back to Telegram |
| `MEDIA_ENABLE_YOUTUBE` | `true` | Set to `false` to ignore YouTube links |
| `YOUTUBE_POT_PROVIDER_URL` | unset | Optional URL of a [bgutil YouTube POT provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) sidecar, used by yt-dlp for YouTube challenges |

The `youtube-pot-provider/` directory builds that sidecar image; point
`YOUTUBE_POT_PROVIDER_URL` at it to enable YouTube support behind bot checks.

## Build, run and test

#### Build bot with production dependencies
```
$ make build
```

#### Build bot with development dependencies
```
$ make build_dev
```

#### Start bot with production dependencies
```
$ make run
```

#### Start bot detached (restart always)
```
$ make run_detached
```

#### Start bot with development dependencies (repo mounted at `/app`)
```
$ make run_dev
```

#### Shell into the dev image (repo mounted at `/app`)
```
$ make bash
```

Handy for running focused tests:

```
$ make bash
python -m pytest tests/test_media_urls.py -k <name>
```

#### Lint (ruff, with autofix) / check lint read-only
```
$ make lint
$ make lint_check
```

#### Format (ruff format) / check formatting read-only
```
$ make format
$ make format_check
```

#### Running tests (pytest with coverage)
```
$ make test
```

Ruff runs with default settings (no config file). Async tests require an
explicit `@pytest.mark.asyncio` (strict mode), and
`tests/test_container_contract.py` asserts on the literal contents of the
`Dockerfile`s and `requirements/*.txt`, so editing those can break tests.

## Architecture

- `comandita.py::configure_handlers` registers every handler. New commands,
  reactions, or message handlers must also be added there.
- `commands/` — slash commands.
- `reactions/` — emoji/text reactions driven by a priority registry.
- `chat_statistics/` — daily per-chat statistics behind `/stats`.
- `clients/` — external APIs (OpenWeatherMap).
- `media_downloads/` — yt-dlp based public-media downloader: URL
  classification, extraction, rate limiting, and env-driven settings.
- Feature design docs live in `docs/plans/`.

The runtime image ships with `ffmpeg` (video thumbnails) and a Node binary
(required by `yt-dlp-ejs` for YouTube challenges).
