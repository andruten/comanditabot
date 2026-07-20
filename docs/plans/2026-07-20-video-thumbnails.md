# Video Thumbnails Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Attach a reliable preview image when Comandita replies with a downloaded video.

**Architecture:** Generate a small JPEG from the first usable video frame with the existing FFmpeg runtime. Keep the JPEG beside the downloaded video inside the existing temporary directory, pass it as Telegram's `thumbnail` parameter, and fall back to a video without a thumbnail if extraction fails.

**Tech Stack:** Python 3.14, python-telegram-bot 22, FFmpeg, pytest.

### Task 1: Generate and attach video thumbnails

**Files:**
- Modify: `media_downloads/handler.py`
- Modify: `tests/test_media_handler.py`

**Step 1: Write a failing async handler test**

Update the recording message's `reply_video` to record a supplied `thumbnail`.
Exercise a `.mp4` attachment with an injected thumbnail generator that writes a JPEG. Assert the reply receives both the video and the generated JPEG.

**Step 2: Verify RED**

Run:

```bash
make build_dev
docker run --rm --env-file .env comanditabot:latest python -m pytest tests/test_media_handler.py -q
```

Expected: the video reply does not receive a thumbnail.

**Step 3: Implement the minimum behaviour**

Add a small `VideoThumbnailGenerator` that calls `ffmpeg` without a shell, seeks to one second, captures one scaled JPEG, and returns its path only when successful. For video replies, open the JPEG within the existing temporary-directory scope and pass it as `thumbnail`. Catch generator failures and send the video normally.

**Step 4: Verify GREEN**

Run the Task 1 command and then `make test`.

**Step 5: Commit**

```bash
git add media_downloads/handler.py tests/test_media_handler.py
git commit -m "feat: add video thumbnails"
```

