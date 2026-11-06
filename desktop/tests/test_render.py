import json
import subprocess

from desktop.pipeline import ffmpeg, images, render, voice
from desktop.core import paths


def _scene(tmp_path, name, words, ar="16:9"):
    img = tmp_path / f"{name}.jpg"
    images.placeholder(img, ar)
    wav = tmp_path / f"{name}.wav"
    voice.make_voice(wav, " ".join(["word"] * words), engine=voice.StubEngine())
    return img, wav


def _streams(path):
    out = subprocess.run([ffmpeg.FFPROBE, "-v", "error", "-show_entries", "stream=codec_type",
                          "-of", "json", str(path)], capture_output=True, text=True).stdout
    return sorted(s["codec_type"] for s in json.loads(out)["streams"])


def test_scene_clip(tmp_path):
    img, wav = _scene(tmp_path, "a", 4)          # 1.2s
    clip = tmp_path / "clip.mp4"
    render.render_scene_clip(img, wav, clip, "one two three four", 0, "16:9", preset="ultrafast")
    assert abs(ffmpeg.probe_duration(clip) - 1.2) < 0.15
    assert _streams(clip) == ["audio", "video"]


def test_assemble_two_clips_with_logo_and_music(tmp_path):
    clips = []
    for i, words in enumerate([4, 6]):           # 1.2s + 1.8s
        img, wav = _scene(tmp_path, f"s{i}", words, "9:16")
        c = tmp_path / f"c{i}.mp4"
        render.render_scene_clip(img, wav, c, "hello there", i, "9:16", preset="ultrafast")
        clips.append(c)
    out = tmp_path / "final.mp4"
    music = next((paths.assets_dir() / "music").glob("*.mp3"))
    render.assemble(clips, out, "9:16", music=music, logo=paths.assets_dir() / "logo.png", preset="ultrafast")
    assert abs(ffmpeg.probe_duration(out) - (3.0 - render.CROSSFADE)) < 0.25
    assert _streams(out) == ["audio", "video"]


def test_assemble_single_clip(tmp_path):
    img, wav = _scene(tmp_path, "a", 4)
    c = tmp_path / "c.mp4"
    render.render_scene_clip(img, wav, c, "x", 0, "16:9", preset="ultrafast")
    out = tmp_path / "final.mp4"
    render.assemble([c], out, "16:9", music=None, logo=None, preset="ultrafast")
    assert out.exists()
