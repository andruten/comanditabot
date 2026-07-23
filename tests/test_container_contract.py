from pathlib import Path


def test_runtime_image_installs_ffmpeg_and_starts_the_bot():
    dockerfile = Path("Dockerfile").read_text()

    assert "ffmpeg" in dockerfile
    assert 'CMD ["python", "-m", "comandita"]' in dockerfile


def test_runtime_image_includes_the_youtube_challenge_solver():
    dockerfile = Path("Dockerfile").read_text()
    requirements = Path("requirements/pro.txt").read_text()

    assert "FROM node:22-bookworm-slim AS node" in dockerfile
    assert "COPY --from=node /usr/local/bin/node /usr/local/bin/node" in dockerfile
    assert "yt-dlp-ejs==0.8.0" in requirements


def test_youtube_pot_provider_image_is_pinned():
    dockerfile = Path("youtube-pot-provider/Dockerfile").read_text()

    assert "brainicism/bgutil-ytdlp-pot-provider:1.3.1-node" in dockerfile


def test_build_workflow_publishes_both_comandita_images():
    workflow = Path(".github/workflows/deploy.yml").read_text()

    assert "apps/comanditabot" in workflow
    assert "apps/comanditabot-youtube-pot-provider" in workflow
    assert "matrix" in workflow
    assert "youtube-pot-provider" in workflow
