from desktop.core import db, settings
from desktop.ui.bridge import WorkerBridge
from desktop.ui.tasks import run_async


def test_run_async_result_and_error(qtbot):
    got = {}
    with qtbot.waitSignal(run_async(lambda a, b: a + b, 2, 3, on_done=lambda r: got.update(r=r)).signals.finished,
                          timeout=5000):
        pass
    assert got["r"] == 5

    def boom():
        raise ValueError("bad")
    with qtbot.waitSignal(run_async(boom, on_error=lambda e: got.update(e=str(e))).signals.finished, timeout=5000):
        pass
    assert got["e"] == "bad"


def test_bridge_renders_and_signals(qtbot, Session, data_dir):
    settings.save(settings.load() | {"voice_engine": "stub", "image_sources": "placeholder",
                                     "background_music": False, "render_preset": "ultrafast"})
    with Session() as s:
        st = db.Story(title="T", content="x", aspect_ratio="16:9")
        st.scenes = [db.Scene(order=0, narration="bridge test scene", image_prompt="sea")]
        s.add(st)
        s.commit()
        sid, scene_id = st.id, st.scenes[0].id
    bridge = WorkerBridge(data_dir)
    scenes = []
    bridge.sceneChanged.connect(lambda story, scene: scenes.append(scene))
    try:
        bridge.start()
        bridge.submit_render(sid)
        with Session() as s:
            assert s.get(db.Story, sid).status == "queued"
        def done():
            with Session() as s:
                return s.get(db.Story, sid).status == "done"
        qtbot.waitUntil(done, timeout=90000)
        qtbot.waitUntil(lambda: bridge.state == "idle", timeout=5000)  # job_done arrives just after the DB write
        assert scene_id in scenes
    finally:
        bridge.stop()
