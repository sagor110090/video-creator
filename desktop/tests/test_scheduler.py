from datetime import date, datetime, time, timedelta

import pytest

from desktop.core import db
from desktop.services import scheduler, stats

NOW = datetime(2026, 11, 7, 9, 30)


def _schedule(Session, t="09:00", last_run=None, status="active", style="story", channel_id=None):
    with Session() as s:
        sch = db.Schedule(topic="space", style=style, aspect_ratio="9:16", scheduled_time=time.fromisoformat(t),
                          last_run_at=last_run, status=status, channel_id=channel_id)
        s.add(sch)
        s.commit()
        return sch.id


def test_due_schedules(Session):
    due = _schedule(Session, "09:00")
    _schedule(Session, "10:00")                                  # later today
    _schedule(Session, "08:00", last_run=NOW.date())             # already ran today
    yesterday = _schedule(Session, "08:00", last_run=NOW.date() - timedelta(days=1))
    _schedule(Session, "08:00", status="paused")
    assert sorted(scheduler.due_schedules(Session, NOW)) == sorted([due, yesterday])


@pytest.fixture
def fake_ai(monkeypatch):
    calls = {}

    def story(cfg, topic, style, ar, ts):
        calls["topic"] = topic
        return {"title": "Space Title", "content": "Stars are far away from us. Planets orbit the sun slowly.",
                "youtube_title": "YT", "youtube_description": "D", "youtube_tags": "a,b"}
    monkeypatch.setattr(scheduler.story_ai, "generate_story", story)
    monkeypatch.setattr(scheduler.story_ai, "generate_image_prompts", lambda cfg, n: ["p"] * len(n))
    monkeypatch.setattr(scheduler.story_ai, "search_news",
                        lambda cfg, q, style: [{"title": "Big News", "snippet": "Details here"}])
    return calls


def test_run_schedule_creates_story(Session, fake_ai):
    with Session() as s:
        ch = db.Channel(channel_id="UC1", title="C")
        s.add(ch)
        s.commit()
        ch_id = ch.id
    sid = _schedule(Session, channel_id=ch_id)
    story_id = scheduler.run_schedule({}, Session, sid, NOW)
    with Session() as s:
        st = s.get(db.Story, story_id)
        assert (st.title, st.schedule_id, st.channel_id, st.aspect_ratio) == ("Space Title", sid, ch_id, "9:16")
        assert st.youtube_title == "YT" and st.publish_at == NOW and len(st.scenes) == 2
        sch = s.get(db.Schedule, sid)
        assert sch.last_run_at == NOW.date() and sch.last_error is None
    assert fake_ai["topic"] == "space"


def test_news_styles_use_news(Session, fake_ai):
    sid = _schedule(Session, style="hollywood_hype")
    scheduler.run_schedule({}, Session, sid, NOW)
    assert fake_ai["topic"].startswith("Create a video about this news: Big News")


def test_run_schedule_failure_recorded_and_not_retried_today(Session, monkeypatch):
    def boom(*a):
        raise scheduler.story_ai.StoryAIError("No API key")
    monkeypatch.setattr(scheduler.story_ai, "generate_story", boom)
    sid = _schedule(Session)
    with pytest.raises(scheduler.story_ai.StoryAIError):
        scheduler.run_schedule({}, Session, sid, NOW)
    with Session() as s:
        sch = s.get(db.Schedule, sid)
        assert sch.last_error == "No API key" and sch.last_run_at == NOW.date()
    assert scheduler.due_schedules(Session, NOW) == []


def test_due_uploads_and_publishes(Session):
    with Session() as s:
        ch = db.Channel(channel_id="UC1", title="C")
        s.add(ch)
        s.flush()
        mk = lambda **kw: db.Story(content="c", channel_id=ch.id, **kw)
        stories = [
            mk(status="done", publish_at=NOW - timedelta(minutes=1)),                       # upload
            mk(status="done", publish_at=NOW + timedelta(hours=1)),                         # upload (private)
            mk(status="rendering", publish_at=NOW),                                         # not rendered
            mk(status="done", publish_at=NOW, youtube_upload_status="completed"),           # already
            mk(status="done", publish_at=NOW - timedelta(minutes=5), youtube_upload_status="scheduled"),  # publish
            mk(status="done", publish_at=NOW + timedelta(hours=2), youtube_upload_status="scheduled"),    # later
            db.Story(content="c", status="done", publish_at=NOW),                           # no channel
        ]
        s.add_all(stories)
        s.commit()
        ids = [x.id for x in stories]
    assert scheduler.due_uploads(Session, NOW) == ids[0:2]
    assert scheduler.due_publishes(Session, NOW) == [ids[4]]


def test_stats(Session):
    with Session() as s:
        s.add(db.Channel(channel_id="UC1", title="C"))
        s.add_all([
            db.Story(content="c", status="done", created_at=NOW, rendered_at=NOW, uploaded_at=NOW,
                     youtube_upload_status="completed"),
            db.Story(content="c", status="failed", created_at=NOW - timedelta(days=1)),
            db.Story(content="c", status="done", created_at=NOW - timedelta(days=40), rendered_at=NOW - timedelta(days=40)),
        ])
        s.commit()
    sm = stats.summary(Session)
    assert (sm["stories"], sm["done"], sm["failed"], sm["uploaded"], sm["channels"]) == (3, 2, 1, 1, 1)
    rows = stats.daily(Session, days=30, today=NOW.date())
    assert len(rows) == 30 and rows[0]["date"] == NOW.date()
    assert (rows[0]["created"], rows[0]["rendered"], rows[0]["uploaded"]) == (1, 1, 1)
    assert rows[1]["created"] == 1
