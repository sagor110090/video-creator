from datetime import datetime

import pytest

from desktop.core import db
from desktop.services import scheduler, stats, stories


@pytest.fixture
def sid(Session):
    with Session() as s:
        ch = db.Channel(channel_id="UC1", title="C")
        s.add(ch)
        s.flush()
        st = db.Story(title="T", content="c", status="done", channel_id=ch.id, publish_at=datetime(2026, 1, 1))
        s.add(st)
        s.commit()
        return st.id


@pytest.mark.parametrize("url,vid", [
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=3s", "dQw4w9WgXcQ"),
    ("https://youtube.com/shorts/dQw4w9WgXcQ?feature=share", "dQw4w9WgXcQ"),
    ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("", None), ("not a link", None)])
def test_parse_video_id(url, vid):
    assert stories.youtube_id(url) == vid


def test_mark_and_unmark(Session, sid):
    stories.mark_uploaded(sid, "https://youtu.be/dQw4w9WgXcQ")
    with Session() as s:
        st = s.get(db.Story, sid)
        assert (st.youtube_upload_status, st.youtube_video_id) == ("manual", "dQw4w9WgXcQ")
        assert st.uploaded_at is not None
    # a story the user uploaded themselves is never auto-uploaded, and counts as uploaded
    assert scheduler.due_uploads(Session, datetime.now()) == []
    assert stats.summary(Session)["uploaded"] == 1
    stories.unmark_uploaded(sid)
    with Session() as s:
        st = s.get(db.Story, sid)
        assert (st.youtube_upload_status, st.youtube_video_id, st.uploaded_at) == (None, None, None)


def test_unmark_does_not_touch_app_uploads(Session, sid):
    with Session() as s:
        st = s.get(db.Story, sid)
        st.youtube_upload_status, st.youtube_video_id = "completed", "realVideo01"
        s.commit()
    stories.unmark_uploaded(sid)
    with Session() as s:
        assert s.get(db.Story, sid).youtube_upload_status == "completed"


def test_card_menu_marks_uploaded(qtbot, Session, sid, monkeypatch):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    page = dashboard.DashboardPage(FakeBridge(), open_story=lambda i: None)
    qtbot.addWidget(page)
    card = page.stories.itemWidget(page.stories.item(0))
    labels = [a.text() for a in card.menu.actions() if a.text()]
    assert labels == ["Open story", "Mark as uploaded…", "Open folder"]
    monkeypatch.setattr(dashboard.QInputDialog, "getText",
                        lambda *a, **k: ("https://youtube.com/shorts/dQw4w9WgXcQ", True))
    card.action("Mark as uploaded…").trigger()
    qtbot.waitUntil(lambda: page.stories.itemWidget(page.stories.item(0)) is not card, timeout=3000)
    card = page.stories.itemWidget(page.stories.item(0))        # list was rebuilt
    assert card.upload_badge.text() == "Uploaded" and "dQw4w9WgXcQ" in card.upload_badge.toolTip()
    assert card.action("Mark as not uploaded") is not None
    old = card
    card.action("Mark as not uploaded").trigger()
    qtbot.waitUntil(lambda: page.stories.itemWidget(page.stories.item(0)) is not old, timeout=3000)
    card = page.stories.itemWidget(page.stories.item(0))
    assert card.upload_badge.isHidden()


def test_cancel_mark_dialog_changes_nothing(qtbot, Session, sid, monkeypatch):
    from desktop.tests.test_ui import FakeBridge
    from desktop.ui import dashboard
    page = dashboard.DashboardPage(FakeBridge(), open_story=lambda i: None)
    qtbot.addWidget(page)
    monkeypatch.setattr(dashboard.QInputDialog, "getText", lambda *a, **k: ("", False))
    page.stories.itemWidget(page.stories.item(0)).action("Mark as uploaded…").trigger()
    with Session() as s:
        assert s.get(db.Story, sid).youtube_upload_status is None


def test_youtube_panel_manual_mark(qtbot, Session, sid, monkeypatch):
    from desktop.ui import youtube_panel
    panel = youtube_panel.YouTubePanel()
    qtbot.addWidget(panel)
    panel.load(sid)
    panel.setChecked(True)
    assert panel.manual_btn.text() == "I uploaded it myself…"
    monkeypatch.setattr(youtube_panel.QInputDialog, "getText", lambda *a, **k: ("https://youtu.be/dQw4w9WgXcQ", True))
    panel.manual_btn.click()
    assert "Uploaded by you" in panel.status.text() and "dQw4w9WgXcQ" in panel.status.text()
    assert panel.manual_btn.text() == "Mark as not uploaded"
    panel.manual_btn.click()
    assert panel.status.text().startswith("Not uploaded")
