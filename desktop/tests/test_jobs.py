from pathlib import Path

import pytest

from desktop.core import db
from desktop.pipeline import jobs, voice

CFG = {"image_sources": "placeholder", "voice_engine": "stub", "background_music": False,
       "render_preset": "ultrafast"}


@pytest.fixture
def story_id(Session):
    with Session() as s:
        st = db.Story(title="T", content="x", aspect_ratio="16:9")
        st.scenes = [db.Scene(order=0, narration="first scene words", image_prompt="sea"),
                     db.Scene(order=1, narration="second scene here", image_prompt="sky")]
        s.add(st)
        s.commit()
        return st.id


def _run(Session, story_id, engine=None):
    events = []
    jobs.render_story(Session, story_id, events.append, CFG, engine or voice.StubEngine())
    return events


def test_render_story_all_stages(Session, story_id):
    events = _run(Session, story_id)
    with Session() as s:
        st = s.get(db.Story, story_id)
        assert st.status == "done" and Path(st.final_path).exists()
        for sc in st.scenes:
            assert (sc.image_status, sc.voice_status, sc.clip_status) == ("done",) * 3
            assert sc.image_source == "placeholder" and sc.voice_engine == "stub"
            assert sc.duration_s > 0
    assert events[0] == {"type": "story", "story_id": story_id, "status": "rendering"}
    assert events[-1]["type"] == "story" and events[-1]["status"] == "done"
    stage_events = [e for e in events if e["type"] == "stage"]
    assert len(stage_events) == 2 * 3 * 2      # 2 scenes x 3 stages x (running, done)


def test_rerun_skips_done_stages(Session, story_id):
    _run(Session, story_id)
    events = _run(Session, story_id)
    assert not [e for e in events if e["type"] == "stage" and e["status"] == "running"]


def test_voice_failure_marks_story_failed(Session, story_id, monkeypatch):
    real = voice.make_voice

    def flaky(out, text, **kw):
        if text.startswith("second"):
            raise voice.VoiceError("boom")
        return real(out, text, **kw)
    monkeypatch.setattr(jobs.voice, "make_voice", flaky)
    _run(Session, story_id)
    with Session() as s:
        st = s.get(db.Story, story_id)
        assert st.status == "failed" and "1 of 2" in st.error
        a, b = st.scenes
        assert a.clip_status == "done"
        assert (b.image_status, b.voice_status, b.clip_status) == ("done", "failed", "pending")
        assert "boom" in b.voice_error


def test_redo_scene_voice_only(Session, story_id):
    _run(Session, story_id)
    with Session() as s:
        scene_id = s.get(db.Story, story_id).scenes[1].id
    events = []
    jobs.redo_scene(Session, scene_id, "voice", events.append, CFG, voice.StubEngine())
    ran = {(e["scene_id"], e["stage"]) for e in events if e["type"] == "stage" and e["status"] == "running"}
    assert ran == {(scene_id, "voice"), (scene_id, "clip")}
    with Session() as s:
        assert s.get(db.Story, story_id).status == "done"


def test_story_voice_sample_overrides_default(Session, story_id, monkeypatch, data_dir):
    used = []

    class FakeChatterbox(voice.StubEngine):
        name = "chatterbox"

        def __init__(self, sample_path=None):
            self.sample_path = sample_path

        def synthesize(self, text, out_wav, *a, **k):
            used.append(self.sample_path)
            super().synthesize(text, out_wav, *a, **k)

    monkeypatch.setattr(voice, "ChatterboxEngine", FakeChatterbox)
    own = data_dir / "mine.wav"
    own.write_bytes(b"x")
    with Session() as s:
        s.get(db.Story, story_id).voice_sample = str(own)
        s.commit()
    cfg = CFG | {"voice_engine": "chatterbox", "voice_sample": "/default.wav"}
    jobs.render_story(Session, story_id, lambda e: None, cfg, voice.get_engine(cfg))
    assert used == [str(own), str(own)]


def test_default_voice_sample_comes_from_current_settings(Session, story_id, monkeypatch):
    used = []

    class FakeChatterbox(voice.StubEngine):
        name = "chatterbox"

        def __init__(self, sample_path=None):
            self.sample_path = sample_path

        def synthesize(self, text, out_wav, *a, **k):
            used.append(self.sample_path)
            super().synthesize(text, out_wav, *a, **k)

    monkeypatch.setattr(voice, "ChatterboxEngine", FakeChatterbox)
    stale_engine = FakeChatterbox("/old-default.wav")         # built when the worker started
    cfg = CFG | {"voice_engine": "chatterbox", "voice_sample": "/new-default.wav"}
    jobs.render_story(Session, story_id, lambda e: None, cfg, stale_engine)
    assert used == ["/new-default.wav", "/new-default.wav"]
