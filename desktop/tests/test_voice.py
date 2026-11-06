import pytest

from desktop.pipeline import ffmpeg, voice


def test_detect_language():
    assert voice.detect_language("नमस्ते दुनिया") == "hi"
    assert voice.detect_language("hello world") == "en"


def test_stub_engine_duration(tmp_path):
    out = tmp_path / "voice.wav"
    engine, dur = voice.make_voice(out, "one two three four", engine=voice.StubEngine())
    assert engine == "stub"
    assert out.exists()
    assert abs(dur - 1.2) < 0.1
    assert abs(ffmpeg.probe_duration(out) - dur) < 0.05


def test_falls_back_to_edge(tmp_path, monkeypatch):
    class Broken:
        name = "chatterbox"

        def synthesize(self, *a, **k):
            raise RuntimeError("model exploded")

    class FakeEdge(voice.StubEngine):
        name = "edge"

    monkeypatch.setattr(voice, "EdgeEngine", FakeEdge)
    engine, _ = voice.make_voice(tmp_path / "voice.wav", "hi there", engine=Broken())
    assert engine == "edge"


def test_both_engines_fail_raises(tmp_path, monkeypatch):
    class Broken:
        name = "x"

        def synthesize(self, *a, **k):
            raise RuntimeError("nope")

    monkeypatch.setattr(voice, "EdgeEngine", lambda: Broken())
    with pytest.raises(voice.VoiceError):
        voice.make_voice(tmp_path / "voice.wav", "hi", engine=Broken())
