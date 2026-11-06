import time

from desktop.core import db, settings
from desktop.pipeline import worker


def _story(Session, status="draft"):
    with Session() as s:
        st = db.Story(title="T", content="x", aspect_ratio="16:9", status=status)
        st.scenes = [db.Scene(order=0, narration="hello from the worker", image_prompt="sea")]
        s.add(st)
        s.commit()
        return st.id


def _wait(handle, pred, timeout=90):
    seen, end = [], time.time() + timeout
    while time.time() < end:
        for ev in handle.events():
            seen.append(ev)
            if pred(ev):
                return seen
        time.sleep(0.1)
    raise AssertionError(f"timed out; events: {seen}")


def test_worker_process_renders_story(Session, data_dir):
    cfg = settings.load() | {"voice_engine": "stub", "image_sources": "placeholder",
                             "background_music": False, "render_preset": "ultrafast"}
    settings.save(cfg)
    sid = _story(Session)
    h = worker.WorkerHandle(data_dir)
    h.start()
    try:
        job = h.submit("render_story", story_id=sid)
        seen = _wait(h, lambda e: e["type"] == "job_done" and e["job_id"] == job)
        assert {"type": "story", "story_id": sid, "status": "done"} in seen
        assert seen[0]["type"] == "worker_ready"
        with Session() as s:
            assert s.get(db.Story, sid).status == "done"
    finally:
        h.stop()
    assert not h.is_alive()


def test_unknown_job_reports_error(Session, data_dir):
    settings.save(settings.load() | {"voice_engine": "stub"})
    h = worker.WorkerHandle(data_dir)
    h.start()
    try:
        job = h.submit("nonsense")
        seen = _wait(h, lambda e: e["type"] == "job_done" and e["job_id"] == job)
        assert any(e["type"] == "job_error" and "nonsense" in e["error"] for e in seen)
    finally:
        h.stop()


def test_recover_interrupted(Session):
    sid = _story(Session, status="rendering")
    with Session() as s:
        s.get(db.Story, sid).scenes[0].voice_status = "running"
        s.commit()
    assert worker.recover_interrupted(Session) == 1
    with Session() as s:
        st = s.get(db.Story, sid)
        assert (st.status, st.error) == ("failed", "interrupted")
        assert st.scenes[0].voice_status == "pending"
