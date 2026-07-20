from pathlib import Path


def test_runtime_image_installs_ffmpeg_and_starts_the_bot():
    dockerfile = Path("Dockerfile").read_text()

    assert "ffmpeg" in dockerfile
    assert 'CMD ["python", "-m", "comandita"]' in dockerfile


def test_youtube_pot_provider_image_is_pinned():
    dockerfile = Path("youtube-pot-provider/Dockerfile").read_text()

    assert "brainicism/bgutil-ytdlp-pot-provider:1.3.1-node" in dockerfile


def test_build_workflow_publishes_both_comandita_images():
    workflow = Path(".github/workflows/deploy.yml").read_text()

    assert "apps/comanditabot" in workflow
    assert "apps/comanditabot-youtube-pot-provider" in workflow
    assert "matrix" in workflow
    assert "youtube-pot-provider" in workflow
