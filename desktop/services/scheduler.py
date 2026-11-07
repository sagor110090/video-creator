"""Recurring schedules and timed YouTube uploads/publishing. Pure functions; the UI calls them on a timer.
Ported from ProcessVideoSchedulesCommand and ProcessScheduledUploadsCommand."""
from datetime import datetime

from sqlalchemy import or_

from desktop.core import db
from desktop.services import story_ai
from desktop.services.stories import create_story

NEWS_STYLES = ("hollywood_hype", "bollywood_masala", "trade_wave")


def due_schedules(Session, now: datetime) -> list[int]:
    with Session() as s:
        q = s.query(db.Schedule.id).filter(
            db.Schedule.status == "active",
            db.Schedule.scheduled_time <= now.time(),
            or_(db.Schedule.last_run_at.is_(None), db.Schedule.last_run_at < now.date()))
        return [r[0] for r in q.order_by(db.Schedule.scheduled_time)]


def run_schedule(cfg, Session, schedule_id: int, now: datetime) -> int:
    """Generate today's story for a schedule. Marks it as run first so a failure is not retried in a loop."""
    with Session() as s:
        sch = s.get(db.Schedule, schedule_id)
        sch.last_run_at, sch.last_error = now.date(), None
        s.commit()
        topic, style, talking, ar, channel, sample, img_style = (
            sch.topic, sch.style, sch.talking_style or "none", sch.aspect_ratio, sch.channel_id,
            sch.voice_sample, sch.image_style or "auto")
    try:
        # news styles fetch real headlines inside generate_story
        data = story_ai.generate_story(cfg, topic or "a random interesting story", style, ar, talking)
        return create_story(data.get("title") or topic, data["content"], style, talking, ar, cfg, yt=data,
                            schedule_id=schedule_id, channel_id=channel, publish_at=now,
                            voice_sample=sample, image_style=img_style)
    except Exception as e:
        with Session() as s:
            s.get(db.Schedule, schedule_id).last_error = str(e)
            s.commit()
        raise


def due_uploads(Session, now: datetime) -> list[int]:
    """Rendered stories with a channel whose publish time has come (or is set for later: uploaded private)."""
    with Session() as s:
        q = s.query(db.Story.id).filter(db.Story.status == "done", db.Story.channel_id.isnot(None),
                                        db.Story.publish_at.isnot(None), db.Story.youtube_upload_status.is_(None))
        return [r[0] for r in q.order_by(db.Story.id)]


def due_publishes(Session, now: datetime) -> list[int]:
    with Session() as s:
        q = s.query(db.Story.id).filter(db.Story.youtube_upload_status == "scheduled",
                                        db.Story.publish_at <= now)
        return [r[0] for r in q.order_by(db.Story.id)]
