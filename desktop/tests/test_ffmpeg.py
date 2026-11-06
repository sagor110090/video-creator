import pytest

from desktop.pipeline import ffmpeg


def test_run_and_probe(tmp_path):
    out = tmp_path / "s.wav"
    ffmpeg.run(["-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(out)])
    assert abs(ffmpeg.probe_duration(out) - 1.0) < 0.05


def test_bad_args_raise(tmp_path):
    with pytest.raises(ffmpeg.FFmpegError):
        ffmpeg.run(["-i", str(tmp_path / "missing.mp4"), str(tmp_path / "o.mp4")])
