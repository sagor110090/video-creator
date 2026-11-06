from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt, Signal

from desktop.core import db, settings
from desktop.pipeline import images


class FakeBridge(QObject):
    event = Signal(dict)
    storyChanged = Signal(int)
    sceneChanged = Signal(int, int)
    stateChanged = Signal(str)
    workerCrashed = Signal(str)

    def __init__(self):
        super().__init__()
        self.renders, self.redos = [], []
        self.state, self.current_story, self.busy = "idle", None, False

    def submit_render(self, story_id):
        self.renders.append(story_id)

    def submit_redo(self, story_id, scene_id, from_stage):
        self.redos.append((story_id, scene_id, from_stage))

    def stop(self):
        pass


@pytest.fixture
def bridge():
    return FakeBridge()


@pytest.fixture
def seeded(Session, data_dir):
    """Story with one finished scene and one whose voice failed."""
    with Session() as s:
        st = db.Story(title="Seeded", content="a. b.", aspect_ratio="16:9", status="failed",
                      error="1 of 2 scenes failed")
        st.scenes = [db.Scene(order=0, narration="The first scene is fine.", image_prompt="sea"),
                     db.Scene(order=1, narration="The second one broke.", image_prompt="sky")]
        s.add(st)
        s.flush()
        a, b = st.scenes
        img = data_dir / "img.jpg"
        images.placeholder(img, "16:9")
        a.image_status = a.voice_status = a.clip_status = "done"
        a.image_path, a.image_source, a.image_license = str(img), "openverse", "cc0"
        b.image_status, b.image_path, b.image_source = "done", str(img), "pollinations"
        b.voice_status, b.voice_error = "failed", "VoiceError: boom"
        s.commit()
        return st.id, a.id, b.id


# ------------------------------------------------------------------ dashboard

def test_dashboard_write_with_ai_and_create(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard
    monkeypatch.setattr(dashboard.story_ai, "generate_story",
                        lambda cfg, topic, style, ar, ts: {"title": "AI Title", "content": "Alpha scene here. Beta scene here."})
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts", lambda cfg, n, *style: [f"prompt {i}" for i in range(len(n))])
    opened = []
    page = dashboard.DashboardPage(bridge, open_story=opened.append)
    qtbot.addWidget(page)
    page.topic.setText("lighthouse")
    page.write_btn.click()
    qtbot.waitUntil(lambda: page.script.toPlainText() == "Alpha scene here. Beta scene here.", timeout=5000)
    assert page.title.text() == "AI Title"
    page.create_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        st = s.get(db.Story, opened[0])
        assert st.title == "AI Title" and len(st.scenes) == 2
        assert st.scenes[0].image_prompt == "prompt 0"
    assert bridge.renders == [opened[0]]
    assert page.stories.count() == 1


def test_dashboard_shows_error_without_crashing(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard

    def fail(*a):
        raise dashboard.story_ai.StoryAIError("No API key for deepseek. Add it in Settings.")
    monkeypatch.setattr(dashboard.story_ai, "generate_story", fail)
    page = dashboard.DashboardPage(bridge, open_story=lambda i: None)
    qtbot.addWidget(page)
    page.topic.setText("x")
    page.write_btn.click()
    qtbot.waitUntil(lambda: "API key" in page.error.text(), timeout=5000)
    assert page.write_btn.isEnabled()


# ------------------------------------------------------------------ story view

def test_story_view_rows_and_failed_tooltip(qtbot, seeded, bridge):
    from desktop.ui.story_view import StoryView
    sid, a_id, b_id = seeded
    view = StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    assert len(view.rows) == 2
    row_b = view.rows[b_id]
    assert row_b.chips["voice"].text() == "Voice: failed"
    assert "boom" in row_b.chips["voice"].toolTip()
    assert "Openverse" in view.rows[a_id].source.text() and "cc0" in view.rows[a_id].source.text()
    assert "1 of 2 scenes failed" in view.error.text()
    assert view.progress.value() == 4   # 3 + 1 of 6 stages done


def test_story_view_edit_narration_marks_voice_stale(qtbot, Session, seeded, bridge):
    from desktop.ui.story_view import StoryView
    sid, a_id, _ = seeded
    view = StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    row = view.rows[a_id]
    row.narration.setPlainText("A brand new line for the first scene.")
    row.save_btn.click()
    with Session() as s:
        sc = s.get(db.Scene, a_id)
        assert sc.narration == "A brand new line for the first scene."
        assert (sc.image_status, sc.voice_status, sc.clip_status) == ("done", "pending", "pending")


def test_story_view_redo_buttons_submit_jobs(qtbot, seeded, bridge):
    from desktop.ui.story_view import StoryView
    sid, a_id, b_id = seeded
    view = StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    view.rows[b_id].revoice_btn.click()
    view.rows[a_id].refetch_btn.click()
    assert bridge.redos == [(sid, b_id, "voice"), (sid, a_id, "image")]
    view.render_btn.click()
    assert bridge.renders == [sid]


def test_replace_image_from_file(qtbot, Session, seeded, bridge, tmp_path, monkeypatch):
    from desktop.ui import story_view
    sid, a_id, _ = seeded
    new = tmp_path / "mine.png"
    images.placeholder(tmp_path / "x.jpg", "9:16")
    Path(tmp_path / "x.jpg").rename(new)
    monkeypatch.setattr(story_view.QFileDialog, "getOpenFileName", lambda *a, **k: (str(new), ""))
    view = story_view.StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    view.rows[a_id].replace_btn.click()
    with Session() as s:
        sc = s.get(db.Scene, a_id)
        assert sc.image_source == "manual" and sc.image_status == "done"
        assert sc.clip_status == "pending" and sc.voice_status == "done"
        assert Path(sc.image_path).read_bytes()[:3] == b"\xff\xd8\xff"
    assert bridge.redos == [(sid, a_id, "clip")]


# ------------------------------------------------------------------ settings + window

def test_settings_page_round_trip(qtbot):
    from desktop.ui.settings_page import SettingsPage
    page = SettingsPage()
    qtbot.addWidget(page)
    page.load()
    page.fields["pexels_api_key"].setText("px-123")
    page.voice_engine.setCurrentIndex(page.voice_engine.findData("edge"))
    page.save_btn.click()
    cfg = settings.load()
    assert cfg["pexels_api_key"] == "px-123" and cfg["voice_engine"] == "edge"


def test_main_window_navigation(qtbot, Session, seeded, bridge):
    from desktop.ui.main_window import MainWindow
    win = MainWindow(bridge)
    qtbot.addWidget(win)
    assert win.stack.currentWidget() is win.dashboard
    win.nav_buttons["settings"].click()
    assert win.stack.currentWidget() is win.settings_page
    win.open_story(seeded[0])
    assert win.stack.currentWidget() is win.story_view
    bridge.stateChanged.emit("idle")
    assert win.worker_label.text() == "Worker idle"


def test_settings_gemini_choice(qtbot):
    from desktop.ui.settings_page import SettingsPage
    page = SettingsPage()
    qtbot.addWidget(page)
    page.load()
    assert page.provider_free.isChecked() and page.gemini_box.isHidden()
    page.provider_gemini.setChecked(True)
    assert not page.gemini_box.isHidden()
    page.fields["gemini_api_key"].setText("AIza-test")
    page.gemini_model.setCurrentIndex(page.gemini_model.findData("gemini-3.1-flash-lite-image"))
    page.size_buttons["1K"].setChecked(True)
    page.save_btn.click()
    cfg = settings.load()
    assert (cfg["image_provider"], cfg["gemini_api_key"], cfg["gemini_image_model"], cfg["gemini_image_size"]) == \
           ("gemini", "AIza-test", "gemini-3.1-flash-lite-image", "1K")
