from pathlib import Path


def test_runtime_image_installs_ffmpeg_and_starts_the_bot():
    dockerfile = Path("Dockerfile").read_text()

    assert "ffmpeg" in dockerfile
    assert 'CMD ["python", "-m", "comandita"]' in dockerfile
