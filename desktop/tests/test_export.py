from pathlib import Path

from desktop.core import db
from desktop.pipeline import export, jobs, voice

CFG = {"image_sources": "placeholder", "voice_engine": "stub", "background_music": False,
       "render_preset": "ultrafast"}


def _story(Session, title="Grandma's Cookie Jar: Talked Back!?"):
    with Session() as s:
        st = db.Story(title=title, content="x", aspect_ratio="16:9")
        st.scenes = [db.Scene(order=0, narration="one short scene here", image_prompt="sea")]
        s.add(st)
        s.commit()
        return st.id


def test_filename_is_safe_and_unique_per_story():
    assert export.filename(7, "Grandma's Cookie Jar: Talked Back!?") == "Grandma's Cookie Jar Talked Back (7).mp4"
    assert export.filename(3, "") == "Untitled (3).mp4"
    assert export.filename(3, "a/b\\c") == "a b c (3).mp4"


def test_render_copies_final_to_output_folder(Session, tmp_path):
    out_dir = tmp_path / "My Videos"
    sid = _story(Session)
    jobs.render_story(Session, sid, lambda e: None, CFG | {"output_dir": str(out_dir)}, voice.StubEngine())
    with Session() as s:
        st = s.get(db.Story, sid)
        assert st.status == "done"
        exported = Path(st.export_path)
    assert exported == out_dir / f"Grandma's Cookie Jar Talked Back ({sid}).mp4"
    assert exported.read_bytes() == Path(st.final_path).read_bytes()


def test_no_output_folder_no_copy(Session):
    sid = _story(Session)
    jobs.render_story(Session, sid, lambda e: None, CFG, voice.StubEngine())
    with Session() as s:
        assert s.get(db.Story, sid).export_path is None


def test_rebuild_after_rename_replaces_old_copy(Session, tmp_path):
    out_dir = tmp_path / "out"
    sid = _story(Session, "Old name")
    jobs.render_story(Session, sid, lambda e: None, CFG | {"output_dir": str(out_dir)}, voice.StubEngine())
    with Session() as s:
        st = s.get(db.Story, sid)
        st.title, st.final_path = "New name", None
        s.commit()
    jobs.render_story(Session, sid, lambda e: None, CFG | {"output_dir": str(out_dir)}, voice.StubEngine())
    assert sorted(p.name for p in out_dir.iterdir()) == [f"New name ({sid}).mp4"]


def test_export_all_existing(Session, tmp_path):
    a, b = _story(Session, "A"), _story(Session, "B")
    jobs.render_story(Session, a, lambda e: None, CFG, voice.StubEngine())
    out_dir = tmp_path / "later"
    assert export.export_all(Session, out_dir) == 1          # only finished videos
    assert (out_dir / f"A ({a}).mp4").exists()


def test_settings_output_folder(qtbot, Session, tmp_path, monkeypatch):
    from desktop.core import settings
    from desktop.ui import settings_page
    target = tmp_path / "Movies"
    target.mkdir()
    copied = []
    monkeypatch.setattr(settings_page.QFileDialog, "getExistingDirectory", lambda *a, **k: str(target))
    monkeypatch.setattr(settings_page.QMessageBox, "question", lambda *a, **k: settings_page.QMessageBox.Yes)
    monkeypatch.setattr(settings_page.export, "export_all", lambda S, d: copied.append(d) or 0)
    _story(Session)
    with Session() as s:
        s.query(db.Story).one().status = "done"
        s.commit()
    page = settings_page.SettingsPage()
    qtbot.addWidget(page)
    page.load()
    assert "Not set" in page.output_label.text() and not page.output_open_btn.isEnabled()
    page.output_choose_btn.click()
    assert page.output_label.text() == str(target)
    qtbot.waitUntil(lambda: copied == [str(target)], timeout=3000)
    page.save_btn.click()
    assert settings.load()["output_dir"] == str(target)
    page.output_clear_btn.click()
    page.save_btn.click()
    assert settings.load()["output_dir"] == ""


def test_story_view_show_video_prefers_export(qtbot, Session, tmp_path):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui.story_view import StoryView
    sid = _story(Session)
    jobs.render_story(Session, sid, lambda e: None, CFG | {"output_dir": str(tmp_path / "o")}, voice.StubEngine())
    view = StoryView(FakeBridge(), back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    assert view.reveal_btn.isEnabled() and view._video.startswith(str(tmp_path / "o"))
