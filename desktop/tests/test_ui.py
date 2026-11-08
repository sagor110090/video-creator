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
        self.renders, self.redos, self.reviews = [], [], []
        self.state, self.current_story, self.busy = "idle", None, False

    def submit_render(self, story_id):
        self.renders.append(story_id)

    def submit_redo(self, story_id, scene_id, from_stage, image_provider=None):
        self.redos.append((story_id, scene_id, from_stage) + ((image_provider,) if image_provider is not None else ()))

    def submit_review(self, story_id):
        self.reviews.append(story_id)

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
                        lambda cfg, topic, style, ar, ts, news_story=None: {"title": "AI Title", "content": "The alpha scene happens right here today. The beta scene follows right after that."})
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts", lambda cfg, n, *style: [f"prompt {i}" for i in range(len(n))])
    opened = []
    page = dashboard.DashboardPage(bridge, open_story=opened.append)
    qtbot.addWidget(page)
    page.topic.setText("lighthouse")
    page.write_btn.click()
    qtbot.waitUntil(lambda: page.script.toPlainText() == "The alpha scene happens right here today. The beta scene follows right after that.", timeout=5000)
    assert page.title.text() == "AI Title"
    page.create_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        st = s.get(db.Story, opened[0])
        assert st.title == "AI Title" and len(st.scenes) == 1
        assert st.scenes[0].image_prompt == "prompt 0"
    assert bridge.renders == [opened[0]]
    assert page.stories.count() == 1


def test_dashboard_shows_error_without_crashing(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard

    def fail(*a, **k):
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


def test_settings_openrouter_choice(qtbot):
    from desktop.ui.settings_page import SettingsPage
    page = SettingsPage()
    qtbot.addWidget(page)
    page.load()
    page.provider_openrouter.setChecked(True)
    assert not page.openrouter_box.isHidden() and page.gemini_box.isHidden()
    page.fields["openrouter_api_key"].setText("sk-or-test")
    page.save_btn.click()
    cfg = settings.load()
    assert (cfg["image_provider"], cfg["openrouter_api_key"], cfg["openrouter_image_model"]) == \
           ("openrouter", "sk-or-test", "google/gemini-2.5-flash-image")
    page.load()
    assert page.provider_openrouter.isChecked()


def test_dashboard_next_starts_review(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts", lambda cfg, n, *style: ["p"] * len(n))
    opened = []
    page = dashboard.DashboardPage(bridge, open_story=opened.append)
    qtbot.addWidget(page)
    page.image_source.setCurrentIndex(page.image_source.findData("openrouter"))
    page.script.setPlainText("The first scene happens right here today. The second scene follows right after it.")
    page.next_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        st = s.get(db.Story, opened[0])
        assert st.image_provider == "openrouter" and len(st.scenes) == 1
    assert bridge.reviews == [opened[0]] and bridge.renders == []


def test_dashboard_default_image_source_stays_unset(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts", lambda cfg, n, *style: ["p"] * len(n))
    settings.save(settings.load() | {"image_provider": "gemini"})
    opened = []
    page = dashboard.DashboardPage(bridge, open_story=opened.append)
    qtbot.addWidget(page)
    assert page.image_source.currentData() == "" and page.image_source.currentText() == "Default · Gemini (paid)"
    page.script.setPlainText("Only one scene in this story.")
    page.create_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        assert s.get(db.Story, opened[0]).image_provider is None


def test_review_editor_steps_and_build(qtbot, Session, seeded, bridge):
    from desktop.ui.story_view import StoryView
    sid, a_id, b_id = seeded
    with Session() as s:
        st = s.get(db.Story, sid)
        st.status, st.error = "review", None
        s.commit()
    view = StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    assert not view.steps.isHidden() and "Review images" in view.steps.text()
    assert view.render_btn.text() == "Build video" and view.render_btn.isEnabled()
    # pick a paid source for one scene and ask for a new image
    row = view.rows[a_id]
    row.source_pick.setCurrentIndex(row.source_pick.findData("openrouter"))
    row.refetch_btn.click()
    assert bridge.redos == [(sid, a_id, "image", "openrouter")]
    view.render_btn.click()
    assert bridge.renders == [sid]


def test_built_story_hides_steps(qtbot, Session, seeded, bridge):
    from desktop.ui.story_view import StoryView
    sid = seeded[0]
    with Session() as s:
        s.get(db.Story, sid).status = "done"
        s.commit()
    view = StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    assert view.steps.isHidden()


def test_story_cards_show_upload_badge(qtbot, Session, bridge):
    from desktop.ui import dashboard
    with Session() as s:
        for title, up in [("Up", "completed"), ("Later", "scheduled"), ("Broken", "failed"), ("Local", None)]:
            s.add(db.Story(title=title, content="c", status="done", youtube_upload_status=up))
        s.commit()
    page = dashboard.DashboardPage(bridge, open_story=lambda i: None)
    qtbot.addWidget(page)
    cards = {page.stories.itemWidget(page.stories.item(i)).title.text(): page.stories.itemWidget(page.stories.item(i))
             for i in range(page.stories.count())}
    assert cards["Up"].upload_badge.text() == "Uploaded"
    assert cards["Later"].upload_badge.text() == "Scheduled"
    assert cards["Broken"].upload_badge.text() == "Upload failed"
    assert cards["Local"].upload_badge.isHidden()


def test_settings_channel_name(qtbot):
    from desktop.ui.settings_page import SettingsPage
    page = SettingsPage()
    qtbot.addWidget(page)
    page.load()
    page.fields["channel_name"].setText("The 60s Lab")
    page.save_btn.click()
    assert settings.load()["channel_name"] == "The 60s Lab"


def test_shorts_is_default_format(qtbot, Session, bridge):
    from desktop.ui.dashboard import DashboardPage
    from desktop.ui.schedules_page import SchedulesPage
    page = DashboardPage(bridge, open_story=lambda i: None)
    qtbot.addWidget(page)
    assert page.shorts.isChecked() and page.aspect_ratio == "9:16"
    page.landscape.click()
    assert page.aspect_ratio == "16:9"
    sp = SchedulesPage(bridge)
    qtbot.addWidget(sp)
    assert sp.shorts.isChecked()


def test_create_panel_stacks_when_narrow(qtbot, Session, bridge):
    from desktop.ui.dashboard import DashboardPage
    page = DashboardPage(bridge, open_story=lambda i: None)
    qtbot.addWidget(page)
    page.relayout_create(900)
    assert page.field_cols == 2
    row_style = page.field_grid.getItemPosition(page.field_grid.indexOf(page.style))[0]
    row_talk = page.field_grid.getItemPosition(page.field_grid.indexOf(page.talking))[0]
    assert row_style == row_talk                                    # side by side
    page.relayout_create(420)
    assert page.field_cols == 1
    row_style = page.field_grid.getItemPosition(page.field_grid.indexOf(page.style))[0]
    row_talk = page.field_grid.getItemPosition(page.field_grid.indexOf(page.talking))[0]
    assert row_talk > row_style                                     # stacked
    rows = {page.action_grid.getItemPosition(page.action_grid.indexOf(b))[0]
            for b in (page.write_btn, page.next_btn, page.create_btn)}
    assert len(rows) == 2                                           # buttons wrap onto two rows


@pytest.mark.parametrize("w,h", [(1100, 700), (1000, 600), (1440, 900)])
def test_create_fields_never_squashed(qtbot, Session, bridge, w, h):
    """Short windows scroll the form; inputs keep their real height."""
    from desktop.ui.main_window import MainWindow
    win = MainWindow(bridge)
    qtbot.addWidget(win)
    win.runner.timer.stop()
    win.resize(w, h)
    win.show()
    qtbot.waitExposed(win)
    qtbot.wait(50)
    d = win.dashboard
    for widget in (d.style, d.talking, d.image_style, d.image_source, d.shorts, d.landscape, d.topic):
        assert widget.height() >= widget.minimumSizeHint().height() - 1, widget
    assert d.script.height() >= 100


@pytest.mark.parametrize("w,h", [(1000, 680), (1100, 780)])
def test_create_form_fits_width(qtbot, Session, bridge, w, h):
    from desktop.ui.main_window import MainWindow
    win = MainWindow(bridge)
    qtbot.addWidget(win)
    win.runner.timer.stop()
    win.resize(w, h)
    win.show()
    qtbot.waitExposed(win)
    qtbot.wait(50)
    d = win.dashboard
    viewport = d.form_scroll.viewport().width()
    assert d.form_scroll.widget().width() <= viewport + 1          # nothing cut off on the right
    for b in (d.shorts, d.landscape):
        assert b.width() >= b.sizeHint().width() - 1               # format labels not truncated


def test_news_pick_shows_chip_and_write_uses_story(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import dashboard
    page = dashboard.DashboardPage(bridge, open_story=lambda _id: None)
    qtbot.addWidget(page)
    assert page._news_story is None and page.news_chip.isHidden()

    page._news_selected({"title": "Salman trailer drops tomorrow", "source": "Dainik Bhaskar",
                         "published": "Sat, 07 Nov 2026", "link": "https://x"})
    assert page._news_story["source"] == "Dainik Bhaskar"
    assert not page.news_chip.isHidden() and "Salman" in page.news_label.text()

    seen = {}
    monkeypatch.setattr(dashboard.story_ai, "generate_story",
                        lambda cfg, topic, style, ar, ts, news_story=None:
                        seen.update(topic=topic, news_story=news_story)
                        or {"title": "T", "content": "a fine script body with enough words inside"})
    page.write_btn.click()                                    # topic field is empty — the chip is the topic
    qtbot.waitUntil(lambda: "news_story" in seen, timeout=5000)
    assert seen["topic"] == "Salman trailer drops tomorrow"  # headline filled the empty topic
    assert seen["news_story"]["link"] == "https://x"

    page.news_clear.click()
    assert page._news_story is None and page.news_chip.isHidden()


def test_write_still_requires_topic_without_story(qtbot, Session, bridge):
    from desktop.ui import dashboard
    page = dashboard.DashboardPage(bridge, open_story=lambda _id: None)
    qtbot.addWidget(page)
    page.write_btn.click()
    assert "topic" in page.error.text().lower()


def test_news_picker_dialog_search_and_pick(qtbot, monkeypatch):
    from desktop.ui import dashboard
    monkeypatch.setattr(dashboard.news, "headlines",
                        lambda q, style, limit=5, days=7: [
                            {"title": "Salman trailer drops", "source": "Dainik Bhaskar",
                             "published": "Sat, 07 Nov 2026", "link": "https://x"},
                            {"title": "Second story", "source": "AajTak",
                             "published": "Fri, 06 Nov 2026", "link": "https://y"}])
    dlg = dashboard.NewsPickerDialog(initial="salman", style_key="bollywood_masala")
    qtbot.addWidget(dlg)
    qtbot.waitUntil(lambda: dlg.list.count() == 2, timeout=5000)     # initial search auto-ran
    assert "2 stories" in dlg.status.text()
    dlg.list.setCurrentRow(0)
    assert dlg.selected()["title"] == "Salman trailer drops"


def test_create_passes_character_picker_value(qtbot, Session, bridge, monkeypatch, tmp_path):
    import io
    from PIL import Image
    from desktop.ui import dashboard
    seen = {}
    monkeypatch.setattr(dashboard, "create_story", lambda *a, **k: seen.update(k) or 1)
    page = dashboard.DashboardPage(bridge, open_story=lambda _id: None)
    qtbot.addWidget(page)
    assert page.character.value() is None                      # off by default: news videos stay clean

    ref = tmp_path / "host.jpg"
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), (9, 90, 9)).save(buf, "JPEG")
    ref.write_bytes(buf.getvalue())
    page.character.setValue(str(ref))
    page.script.setPlainText("A fine little script for one scene.")
    page.create_btn.click()
    qtbot.waitUntil(lambda: "character_image" in seen, timeout=5000)
    assert seen["character_image"] == str(ref)

def test_schedule_add_saves_character(qtbot, Session, bridge, tmp_path):
    import io
    from PIL import Image
    from desktop.ui.schedules_page import SchedulesPage
    sp = SchedulesPage(bridge)
    qtbot.addWidget(sp)
    ref = tmp_path / "host.jpg"
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), (9, 90, 9)).save(buf, "JPEG")
    ref.write_bytes(buf.getvalue())
    sp.character.setValue(str(ref))
    sp.topic.setText("space")
    sp._add()
    with Session() as s:
        assert s.query(db.Schedule).one().character_image == str(ref)


def test_schedule_add_saves_image_provider(qtbot, Session, bridge):
    from desktop.ui.schedules_page import SchedulesPage
    sp = SchedulesPage(bridge)
    qtbot.addWidget(sp)
    sp.image_source.setCurrentIndex(sp.image_source.findData("openrouter"))
    sp.topic.setText("space")
    sp._add()
    with Session() as s:
        assert s.query(db.Schedule).one().image_provider == "openrouter"


def test_news_chip_title_is_selectable_and_copyable(qtbot, Session, bridge):
    from PySide6.QtGui import QGuiApplication
    from desktop.ui import dashboard
    page = dashboard.DashboardPage(bridge, open_story=lambda _id: None)
    qtbot.addWidget(page)
    story = {"title": "Salman trailer drops tomorrow", "source": "Dainik Bhaskar",
             "published": "Sat, 07 Nov 2026", "link": "https://x"}
    page._news_selected(story)
    assert page.news_label.textInteractionFlags() & Qt.TextSelectableByMouse
    assert "Salman trailer drops tomorrow" in page.news_label.toolTip()
    page.news_copy.click()
    assert QGuiApplication.clipboard().text() == "Salman trailer drops tomorrow"
