# Comandita bot
Welcome to Comandita bot 👋. I run with docker :).


## Available commands

### MiMiMi
```
/mimimi
```

### Weather in Korea
```
/tiempoencorea
```

### Save a message
```
/star
```

### Punish a message
```
/sentenciador
```

## Public media downloads

Send a public Instagram, X/Twitter, Facebook, or TikTok media URL to Comandita
in a private chat or a group. The bot replies with the photos, videos, GIFs, or
documents from that post. It never uses credentials or cookies and cannot
download private content.

For groups, disable the bot's Privacy Mode in BotFather (`/setprivacy`) so
Telegram delivers regular link messages to it. The defaults are 10 downloads
per user per minute and 45 MiB per attachment; configure them with
`MEDIA_MAX_DOWNLOADS_PER_MINUTE` and `MEDIA_MAX_FILE_SIZE_MB`.


## Build, run and test

#### Build bot with development dependencies
```
$ make build_dev
```

#### Build bot with production dependencies
```
$ make build
```

#### Start bot with development dependencies
```
$ make run_dev
```

#### Start bot with production dependencies
```
$ make run
```

#### Running Tests
```
$ make test
```
