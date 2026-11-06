from datetime import datetime, time, timedelta

from PySide6.QtCore import QTime

from desktop.core import db, settings
import pytest


@pytest.fixture
def bridge():
    from desktop.tests.test_ui import FakeBridge
    return FakeBridge()


def _channel(Session, title="My Channel"):
    with Session() as s:
        ch = db.Channel(channel_id="UC1", title=title, access_token="t")
        s.add(ch)
        s.commit()
        return ch.id


# ------------------------------------------------------------------ schedules

def test_schedules_add_pause_delete(qtbot, Session, bridge):
    from desktop.ui.schedules_page import SchedulesPage
    ch = _channel(Session)
    page = SchedulesPage(bridge)
    qtbot.addWidget(page)
    page.refresh()
    page.topic.setText("space facts")
    page.style.setCurrentIndex(page.style.findData("science_short"))
    page.shorts.setChecked(True)
    page.time.setTime(QTime(9, 15))
    page.channel.setCurrentIndex(page.channel.findData(ch))
    page.add_btn.click()
    assert page.table.rowCount() == 1
    with Session() as s:
        sch = s.query(db.Schedule).one()
        assert (sch.topic, sch.style, sch.aspect_ratio, sch.scheduled_time, sch.channel_id) == \
               ("space facts", "science_short", "9:16", time(9, 15), ch)
    page.table.selectRow(0)
    page.pause_btn.click()
    with Session() as s:
        assert s.query(db.Schedule).one().status == "paused"
    page.delete_btn.click()
    with Session() as s:
        assert s.query(db.Schedule).count() == 0


def test_schedule_run_now_renders(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import schedules_page
    with Session() as s:
        s.add(db.Schedule(topic="x", scheduled_time=time(23, 0)))
        s.commit()
    monkeypatch.setattr(schedules_page.scheduler, "run_schedule", lambda cfg, S, sid, now: 42)
    page = schedules_page.SchedulesPage(bridge)
    qtbot.addWidget(page)
    page.refresh()
    page.table.selectRow(0)
    page.run_btn.click()
    qtbot.waitUntil(lambda: bridge.renders == [42], timeout=5000)


# ------------------------------------------------------------------ background runner

def test_runner_tick_runs_due_work(qtbot, Session, bridge, monkeypatch):
    from desktop.ui import scheduler_runner as sr
    uploads, publishes = [], []
    monkeypatch.setattr(sr.scheduler, "due_schedules", lambda S, now: [1])
    monkeypatch.setattr(sr.scheduler, "run_schedule", lambda cfg, S, sid, now: 7)
    monkeypatch.setattr(sr.scheduler, "due_uploads", lambda S, now: [5])
    monkeypatch.setattr(sr.scheduler, "due_publishes", lambda S, now: [6])
    monkeypatch.setattr(sr.youtube, "upload", lambda cfg, S, sid, progress=None: uploads.append(sid))
    monkeypatch.setattr(sr.youtube, "publish", lambda cfg, S, sid: publishes.append(sid))
    runner = sr.SchedulerRunner(bridge, interval_ms=60000)
    runner.tick()
    qtbot.waitUntil(lambda: bridge.renders == [7] and uploads == [5] and publishes == [6], timeout=5000)
    qtbot.waitUntil(lambda: not runner.in_flight, timeout=5000)
    runner.tick()   # in-flight ids were released, so the next tick can run them again
    qtbot.waitUntil(lambda: len(bridge.renders) == 2, timeout=5000)


# ------------------------------------------------------------------ channels + statistics

def test_channels_connect_and_remove(qtbot, Session, monkeypatch):
    from desktop.ui import channels_page
    settings.save(settings.load() | {"youtube_client_id": "cid"})

    def fake_connect(cfg, S, **kw):
        return _channel(Session, "Connected One")
    monkeypatch.setattr(channels_page.youtube, "connect_channel", fake_connect)
    page = channels_page.ChannelsPage()
    qtbot.addWidget(page)
    page.refresh()
    assert page.list.count() == 0
    page.connect_btn.click()
    qtbot.waitUntil(lambda: page.list.count() == 1, timeout=5000)
    assert "Connected One" in page.list.item(0).text()
    page.list.setCurrentRow(0)
    monkeypatch.setattr(channels_page.QMessageBox, "question", lambda *a, **k: channels_page.QMessageBox.Yes)
    page.remove_btn.click()
    assert page.list.count() == 0


def test_channels_without_client_id_explains(qtbot, Session):
    from desktop.ui.channels_page import ChannelsPage
    page = ChannelsPage()
    qtbot.addWidget(page)
    page.refresh()
    assert not page.connect_btn.isEnabled()
    assert "Desktop app" in page.help.text()


def test_statistics_page(qtbot, Session):
    from desktop.ui.statistics_page import StatisticsPage
    with Session() as s:
        s.add(db.Story(content="c", status="done", rendered_at=datetime.now()))
        s.commit()
    page = StatisticsPage()
    qtbot.addWidget(page)
    page.refresh()
    assert page.tiles["stories"].text() == "1" and page.tiles["done"].text() == "1"
    assert page.table.rowCount() == 30
    assert page.table.item(0, 2).text() == "1"


# ------------------------------------------------------------------ story view YouTube panel

def test_story_view_youtube_upload(qtbot, Session, bridge, monkeypatch, data_dir):
    from desktop.ui import story_view
    ch = _channel(Session)
    final = data_dir / "final.mp4"
    final.write_bytes(b"x")
    with Session() as s:
        st = db.Story(title="T", content="c", status="done", final_path=str(final))
        st.scenes = [db.Scene(order=0, narration="n", image_prompt="p")]
        s.add(st)
        s.commit()
        sid = st.id
    uploaded = []
    monkeypatch.setattr(story_view.youtube, "upload", lambda cfg, S, story_id, progress=None: uploaded.append(story_id) or "vid1")
    view = story_view.StoryView(bridge, back=lambda: None)
    qtbot.addWidget(view)
    view.show_story(sid)
    yt = view.yt
    assert not yt.upload_btn.isEnabled()    # collapsed group box disables its contents
    yt.setChecked(True)                     # user expands the YouTube section
    yt.channel.setCurrentIndex(yt.channel.findData(ch))
    yt.title.setText("My YouTube Title")
    yt.tags.setText("a, b")
    yt.later.setChecked(True)
    when = datetime.now().replace(second=0, microsecond=0) + timedelta(days=1)
    yt.when.setDateTime(when)
    yt.upload_btn.click()
    qtbot.waitUntil(lambda: uploaded == [sid], timeout=5000)
    with Session() as s:
        st = s.get(db.Story, sid)
        assert (st.channel_id, st.youtube_title, st.youtube_tags) == (ch, "My YouTube Title", "a, b")
        assert st.publish_at == when
