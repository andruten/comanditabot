import subprocess
from pathlib import Path

from media_downloads.handler import VideoCompressor

MIB = 1024 * 1024
LIMIT = 45 * MIB


class FakeFfmpeg:
    def __init__(self, *, duration="60.0", output_sizes=(), probe_error=False):
        self.duration = duration
        self.output_sizes = list(output_sizes)
        self.probe_error = probe_error
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        if command[0] == "ffprobe":
            if self.probe_error:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0, stdout=self.duration)
        size = self.output_sizes.pop(0) if self.output_sizes else None
        if size is None:
            raise subprocess.CalledProcessError(1, command)
        Path(command[-1]).write_bytes(b"x" * size)
        return subprocess.CompletedProcess(command, 0)


def make_video(tmp_path, name="clip.mp4", size=46 * MIB):
    video_path = tmp_path / name
    video_path.write_bytes(b"x" * size)
    return video_path


def test_files_that_fit_are_returned_unchanged(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg()
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path, size=MIB)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    assert result == video_path
    assert ffmpeg.commands == []


def test_non_video_files_are_returned_unchanged(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg()
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    image_path = make_video(tmp_path, name="image.jpg")

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(image_path)

    assert result == image_path
    assert ffmpeg.commands == []


def test_rate_capped_encoding_targets_the_configured_size(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg(duration="60.0", output_sizes=[40 * MIB])
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    assert ffmpeg.commands[0][0] == "ffprobe"
    assert len(ffmpeg.commands) == 2
    encode_command = ffmpeg.commands[1]
    assert encode_command[encode_command.index("-preset") + 1] == "superfast"
    assert encode_command[encode_command.index("-vf") + 1] == "scale=-2:'min(720,ih)'"
    assert encode_command[encode_command.index("-crf") + 1] == "23"
    assert encode_command[encode_command.index("-maxrate") + 1] == "5915k"
    assert encode_command[encode_command.index("-bufsize") + 1] == "11830k"
    assert "-pass" not in encode_command
    assert "-b:v" not in encode_command
    assert encode_command[encode_command.index("-b:a") + 1] == "96k"
    assert encode_command[-1] == str(tmp_path / "clip.compressed.mp4")
    assert "-movflags" in encode_command
    assert result == tmp_path / "clip.compressed.mp4"


def test_returns_none_when_encoding_fails(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg(duration="60.0")
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    assert result is None


def test_returns_none_when_the_compressed_video_still_exceeds_the_limit(
    tmp_path, monkeypatch
):
    ffmpeg = FakeFfmpeg(duration="60.0", output_sizes=[46 * MIB])
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    assert result is None


def test_output_between_target_and_limit_is_still_sent(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg(duration="60.0", output_sizes=[int(44.5 * MIB)])
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    assert result == tmp_path / "clip.compressed.mp4"


def test_falls_back_to_constant_quality_without_a_known_duration(tmp_path, monkeypatch):
    ffmpeg = FakeFfmpeg(probe_error=True, output_sizes=[40 * MIB])
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    fallback_run = ffmpeg.commands[1]
    assert fallback_run[fallback_run.index("-crf") + 1] == "23"
    assert fallback_run[fallback_run.index("-preset") + 1] == "superfast"
    assert fallback_run[fallback_run.index("-vf") + 1] == "scale=-2:'min(720,ih)'"
    assert "-pass" not in fallback_run
    assert result == tmp_path / "clip.compressed.mp4"


def test_retries_with_lower_quality_when_the_fallback_still_exceeds(
    tmp_path, monkeypatch
):
    ffmpeg = FakeFfmpeg(probe_error=True, output_sizes=[46 * MIB, 40 * MIB])
    monkeypatch.setattr("media_downloads.handler.subprocess.run", ffmpeg)
    video_path = make_video(tmp_path)

    result = VideoCompressor(max_file_size_bytes=LIMIT).compress_if_needed(video_path)

    crfs = [run[run.index("-crf") + 1] for run in ffmpeg.commands[1:] if "-crf" in run]
    assert crfs == ["23", "28"]
    assert result == tmp_path / "clip.compressed.mp4"
