# AGENTS.md

## Overview

Telegram bot (python-telegram-bot) that runs exclusively in Docker.
Entrypoint: `comandita.py`, launched as `python -m comandita`. Do not set up
a local Python environment; use the Make targets.

## Commands (all go through Docker)

- `make test` — pytest with coverage (`--cov` comes from `pytest.ini`);
  runs against the built image (no volume mount) on purpose
- `make lint` / `make format` — ruff check --fix / ruff format; they mount
  the repo at `/app` so fixes and reformatting persist on the host
- `make lint_check` / `make format_check` — read-only ruff check
  --show-fixes / ruff format --check; what CI enforces on PRs
- `make bash` — shell in the dev image with the repo mounted at `/app`;
  use it to run focused tests:
  `python -m pytest tests/test_media_urls.py -k <name>`
- Every target rebuilds the image first. `make test` picks up local edits
  through the rebuild; lint/format/bash also bind-mount the repo at `/app`
  (the image WORKDIR). `make run` / `make run_detached` are mount-free
  except for the `comanditabot_data:/data` named volume, which stores bot
  state (`PicklePersistence` via `PERSISTENCE_PATH`); production runs need
  the same volume or flags are lost on container recreation.
- A `.env` file must exist (`--env-file .env`), even for lint/test;
  `check_env` copies `env.sample` if missing. Dummy values are fine except
  when actually running the bot (needs real `BOT_TOKEN`).

## Gotchas

- Ruff has no config file — defaults apply. `.flake8` and `.isort.cfg` are
  stale legacy configs; ignore them.
- Async tests require an explicit `@pytest.mark.asyncio` (strict mode).
- `tests/test_container_contract.py` asserts on the literal contents of the
  `Dockerfile`s, `requirements/*.txt`, and `.github/workflows/deploy.yml`.
  Editing any of these can break tests.
- The runtime image includes `ffmpeg` (thumbnails) and a Node binary
  (required by `yt-dlp-ejs` for YouTube challenges).

## Architecture

- `comandita.py::configure_handlers` registers every handler. New commands,
  reactions, or message handlers must also be added there.
- Packages: `commands/` (slash commands), `reactions/` (emoji reactions),
  `feature_flags/` (per-chat feature flags persisted in bot_data,
  `/reactions` admin command), `chat_statistics/`, `clients/` (external
  APIs), `media_downloads/` (yt-dlp based public-media downloader: URL
  classification, extraction, rate limiting, env-driven settings).
- `youtube-pot-provider/` builds a separate sidecar image (bgutil YouTube
  POT provider) consumed via the `YOUTUBE_POT_PROVIDER_URL` env var.
- Feature design docs live in `docs/plans/`.

## CI / CD

- PRs to `main`: `.github/workflows/test.yml` runs `make lint_check && make format_check && make test`.


## Conventions

- Commit subjects use prefixes like `feat:`, `fix:`, `ci:`, `chore:` (PRs
  squash-merged with `(#NN)` suffixes).
