"""Numbers for the Statistics page."""
from datetime import date, timedelta

from sqlalchemy import func

from desktop.core import db


def summary(Session) -> dict:
    with Session() as s:
        count = lambda *f: s.query(func.count(db.Story.id)).filter(*f).scalar()
        seconds = (s.query(func.coalesce(func.sum(db.Scene.duration_s), 0))
                   .join(db.Story).filter(db.Story.status == "done").scalar())
        return {"stories": count(), "done": count(db.Story.status == "done"),
                "failed": count(db.Story.status == "failed"),
                "uploaded": count(db.Story.youtube_upload_status.in_(["completed", "scheduled", "manual"])),
                "channels": s.query(func.count(db.Channel.id)).scalar(),
                "minutes": round(seconds / 60, 1)}


def daily(Session, days: int = 30, today: date | None = None) -> list[dict]:
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    rows = {start + timedelta(days=i): {"created": 0, "rendered": 0, "uploaded": 0} for i in range(days)}
    with Session() as s:
        for col, key in ((db.Story.created_at, "created"), (db.Story.rendered_at, "rendered"),
                         (db.Story.uploaded_at, "uploaded")):
            for (value,) in s.query(col).filter(col.isnot(None)):
                d = value.date()
                if d in rows:
                    rows[d][key] += 1
    return [{"date": d, **rows[d]} for d in sorted(rows, reverse=True)]
