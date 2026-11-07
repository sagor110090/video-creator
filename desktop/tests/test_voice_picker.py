from datetime import time
from pathlib import Path

from desktop.core import db, settings, voices


def _wav(path: Path) -> Path:
    path.write_bytes(b"RIFF" + path.name.encode())
    return path


def test_library_add_dedupes(tmp_path):
    a = voices.add_sample(_wav(tmp_path / "My Voice!.wav"))
    assert a.name == "My Voice.wav" and a.parent == voices.library_dir()
    assert voices.add_sample(tmp_path / "My Voice!.wav") == a          # same content → same file
    other = tmp_path / "x" / "My Voice.wav"
    other.parent.mkdir()
    other.write_bytes(b"different")
    assert voices.add_sample(other).name == "My Voice 2.wav"
    assert [p.name for p in voices.list_samples()] == ["My Voice 2.wav", "My Voice.wav"]


def test_picker_default_library_and_add(qtbot, tmp_path, monkeypatch):
    from desktop.ui import voice_picker
    default = voices.add_sample(_wav(tmp_path / "sample.wav"))
    settings.save(settings.load() | {"voice_sample": str(default)})
    anna = voices.add_sample(_wav(tmp_path / "anna.wav"))
    picker = voice_picker.VoicePicker()
    qtbot.addWidget(picker)
    assert picker.value() is None
    assert picker.combo.itemText(0) == "Default voice (sample)"
    picker.set_value(str(anna))
    assert picker.value() == str(anna)
    new = _wav(tmp_path / "bob.wav")
    monkeypatch.setattr(voice_picker.QFileDialog, "getOpenFileName", lambda *a, **k: (str(new), ""))
    picker.combo.setCurrentIndex(picker.combo.findData(voice_picker.ADD))
    assert Path(picker.value()).name == "bob.wav"
    # cancelling the dialog keeps the previous choice
    monkeypatch.setattr(voice_picker.QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
    picker.combo.setCurrentIndex(picker.combo.findData(voice_picker.ADD))
    assert Path(picker.value()).name == "bob.wav"


def test_dashboard_create_uses_chosen_voice(qtbot, Session, monkeypatch, tmp_path):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts", lambda cfg, n, *style: ["p"] * len(n))
    anna = voices.add_sample(_wav(tmp_path / "anna.wav"))
    opened = []
    page = dashboard.DashboardPage(FakeBridge(), open_story=opened.append)
    qtbot.addWidget(page)
    page.voice.set_value(str(anna))
    page.script.setPlainText("The first scene happens right here today. The second scene follows right after it.")
    page.create_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        assert s.get(db.Story, opened[0]).voice_sample == str(anna)


def test_schedule_stores_voice(qtbot, Session, tmp_path):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui.schedules_page import SchedulesPage
    anna = voices.add_sample(_wav(tmp_path / "anna.wav"))
    page = SchedulesPage(FakeBridge())
    qtbot.addWidget(page)
    page.refresh()
    page.topic.setText("space")
    page.voice.set_value(str(anna))
    page.add_btn.click()
    with Session() as s:
        assert s.query(db.Schedule).one().voice_sample == str(anna)
    assert page.table.item(0, page.COLUMNS.index("Voice")).text() == "anna"


def test_dashboard_and_schedule_image_style(qtbot, Session, monkeypatch):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    from desktop.ui.schedules_page import SchedulesPage
    seen = {}
    monkeypatch.setattr(dashboard.story_ai, "generate_image_prompts",
                        lambda cfg, n, style="auto": seen.setdefault("style", style) and ["p"] * len(n))
    opened = []
    page = dashboard.DashboardPage(FakeBridge(), open_story=opened.append)
    qtbot.addWidget(page)
    page.image_style.setCurrentIndex(page.image_style.findData("cartoon"))
    page.script.setPlainText("A happy little bunny hops around the meadow. The bunny finds a giant orange carrot.")
    page.create_btn.click()
    qtbot.waitUntil(lambda: bool(opened), timeout=5000)
    with Session() as s:
        assert s.get(db.Story, opened[0]).image_style == "cartoon"
    assert seen["style"] == "cartoon"

    sp = SchedulesPage(FakeBridge())
    qtbot.addWidget(sp)
    sp.refresh()
    sp.topic.setText("bedtime stories")
    sp.image_style.setCurrentIndex(sp.image_style.findData("cartoon"))
    sp.add_btn.click()
    with Session() as s:
        assert s.query(db.Schedule).one().image_style == "cartoon"
    assert sp.table.item(0, sp.COLUMNS.index("Images")).text() == "Cartoon / kids"
