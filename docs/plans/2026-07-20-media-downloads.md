# Media Downloads Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Comandita reply with public Instagram, X, Facebook, and TikTok media in direct and group chats.

**Architecture:** A first-priority Telegram handler validates URLs, rate-limits the sender, and runs a `yt-dlp` adapter in a worker thread. The adapter uses a temporary directory and returns typed files for Telegram to reply with.

**Tech Stack:** Python 3.14, python-telegram-bot 22, yt-dlp, ffmpeg, pytest, Docker, Helm/Flux.

### Task 1: Recognise supported URLs

**Files:**
- Create: `media_downloads/__init__.py`
- Create: `media_downloads/urls.py`
- Create: `tests/test_media_urls.py`
- Modify: `requirements/pro.txt`

**Step 1: Write failing tests**

Test `classify_url` accepts Instagram posts/reels/stories, X/Twitter status URLs, Facebook media URLs, and TikTok video URLs, but rejects HTTP, lookalike, profile, and generic URLs.

**Step 2: Verify RED**

Run: `docker run --rm -v "$PWD":/app -w /app comanditabot:latest python -m pytest tests/test_media_urls.py -v`

Expected: module-not-found failure.

**Step 3: Implement minimum behaviour**

Use `urllib.parse.urlsplit`, exact host allowlists, HTTPS-only validation, and media-path checks. Add a pinned `yt-dlp` dependency.

**Step 4: Verify GREEN**

Run the Task 1 command again. Expected: PASS.

**Step 5: Commit**

```bash
git add media_downloads requirements/pro.txt tests/test_media_urls.py
git commit -m "feat: recognise supported media links"
```

### Task 2: Download temporary files safely

**Files:**
- Create: `media_downloads/downloader.py`
- Create: `tests/test_media_downloader.py`

**Step 1: Write failing tests**

Inject a fake extractor. Test preserved output order, empty output rejection, oversize rejection, and temporary directory cleanup after response handling.

**Step 2: Verify RED**

Run: `docker run --rm -v "$PWD":/app -w /app comanditabot:latest python -m pytest tests/test_media_downloader.py -v`

Expected: module-not-found failure.

**Step 3: Implement minimum behaviour**

Define `MediaFile`, download errors, extractor protocol, and `YtDlpExtractor`. Use no cookies, no playlists, a per-file ceiling, and an output template inside the supplied temporary directory.

**Step 4: Verify GREEN**

Run the Task 2 command again. Expected: PASS.

**Step 5: Commit**

```bash
git add media_downloads/downloader.py tests/test_media_downloader.py
git commit -m "feat: download public media safely"
```

### Task 3: Add reply handler and priority

**Files:**
- Create: `media_downloads/handler.py`
- Create: `tests/test_media_handler.py`
- Modify: `comandita.py`

**Step 1: Write failing tests**

Use a fake downloader and a recording message. Test photo, video, GIF, and document reply selection; unsupported-URL silence; error reply; and rate limit.

**Step 2: Verify RED**

Run: `docker run --rm -v "$PWD":/app -w /app comanditabot:latest python -m pytest tests/test_media_handler.py -v`

Expected: module-not-found failure.

**Step 3: Implement minimum behaviour**

Extract URLs, classify them, download via `asyncio.to_thread`, and reply to the originating message. Register the handler in a lower group than `ReactionHandlerFactory`, giving it priority. Default to 45 MiB per file and three downloads per minute per user.

**Step 4: Verify GREEN**

Run the Task 3 command again. Expected: PASS.

**Step 5: Commit**

```bash
git add media_downloads/handler.py comandita.py tests/test_media_handler.py
git commit -m "feat: reply to public media links"
```

### Task 4: Add runtime and GitOps capacity

**Files:**
- Modify: `Dockerfile`
- Modify: `README.md`
- Create: `tests/test_container_contract.py`
- Modify: `/Users/juanmanuel.diaz/Documents/personal/k8s-infra/helm-charts/comanditabot/values.yaml`

**Step 1: Write failing tests**

Assert that the image installs `ffmpeg` and keeps its bot command.

**Step 2: Verify RED**

Run: `docker run --rm -v "$PWD":/app -w /app comanditabot:latest python -m pytest tests/test_container_contract.py -v`

Expected: assertion failure because `ffmpeg` is absent.

**Step 3: Implement minimum behaviour**

Install `ffmpeg`, document public-only support and Telegram privacy mode, and set the Helm requests to 250m CPU/512Mi memory and limits to 1 CPU/1Gi. Keep the existing SOPS secret, one replica, and `/tmp` `emptyDir`.

**Step 4: Verify**

Run: `make test && docker build -t comanditabot:media-downloads .`

Then from `k8s-infra`, run `helm lint helm-charts/comanditabot` and `helm template comanditabot helm-charts/comanditabot >/dev/null`.

**Step 5: Commit**

Commit application and `k8s-infra` changes independently. Pin the Helm release to the immutable image tag emitted by the source CI before creating its PR.
