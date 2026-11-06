"""SQLite models. Both the UI process and the worker process open this DB (WAL mode)."""
from datetime import datetime

from sqlalchemy import (Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time,
                        create_engine, event)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from desktop.core import paths

STAGES = ("image", "voice", "clip")
STAGE_STATUSES = ("pending", "running", "done", "failed")
STORY_STATUSES = ("draft", "queued", "rendering", "done", "failed")


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[str | None] = mapped_column(String)
    title: Mapped[str | None] = mapped_column(String)
    thumbnail: Mapped[str | None] = mapped_column(String)
    access_token: Mapped[str] = mapped_column(Text, default="")
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str | None] = mapped_column(String, default="ok")   # ok | reconnect
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String)
    style: Mapped[str] = mapped_column(String, default="story")
    talking_style: Mapped[str | None] = mapped_column(String)
    aspect_ratio: Mapped[str] = mapped_column(String, default="16:9")
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id", ondelete="SET NULL"))
    scheduled_time = mapped_column(Time, nullable=False)
    last_run_at = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    last_error: Mapped[str | None] = mapped_column(Text)
    voice_sample: Mapped[str | None] = mapped_column(String)   # None = Settings default
    image_style: Mapped[str | None] = mapped_column(String, default="auto")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Story(Base):
    __tablename__ = "stories"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    style: Mapped[str] = mapped_column(String, default="story")
    talking_style: Mapped[str | None] = mapped_column(String)
    aspect_ratio: Mapped[str] = mapped_column(String, default="16:9")
    voice_sample: Mapped[str | None] = mapped_column(String)   # None = Settings default
    image_style: Mapped[str | None] = mapped_column(String, default="auto")
    status: Mapped[str] = mapped_column(String, default="draft")
    error: Mapped[str | None] = mapped_column(Text)
    final_path: Mapped[str | None] = mapped_column(String)
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("schedules.id", ondelete="SET NULL"))
    # YouTube
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id", ondelete="SET NULL"))
    youtube_title: Mapped[str | None] = mapped_column(String)
    youtube_description: Mapped[str | None] = mapped_column(Text)
    youtube_tags: Mapped[str | None] = mapped_column(Text)
    youtube_video_id: Mapped[str | None] = mapped_column(String)
    youtube_upload_status: Mapped[str | None] = mapped_column(String)
    youtube_error: Mapped[str | None] = mapped_column(Text)
    publish_at: Mapped[datetime | None] = mapped_column(DateTime)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)
    rendered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="story", order_by="Scene.order", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"))
    order: Mapped[int] = mapped_column(Integer)
    narration: Mapped[str] = mapped_column(Text)
    image_prompt: Mapped[str] = mapped_column(Text, default="")

    image_status: Mapped[str] = mapped_column(String, default="pending")
    image_path: Mapped[str | None] = mapped_column(String)
    image_error: Mapped[str | None] = mapped_column(Text)
    image_source: Mapped[str | None] = mapped_column(String)
    image_source_url: Mapped[str | None] = mapped_column(String)
    image_license: Mapped[str | None] = mapped_column(String)

    voice_status: Mapped[str] = mapped_column(String, default="pending")
    voice_path: Mapped[str | None] = mapped_column(String)
    voice_error: Mapped[str | None] = mapped_column(Text)
    voice_engine: Mapped[str | None] = mapped_column(String)
    duration_s: Mapped[float | None] = mapped_column(Float)

    clip_status: Mapped[str] = mapped_column(String, default="pending")
    clip_path: Mapped[str | None] = mapped_column(String)
    clip_error: Mapped[str | None] = mapped_column(Text)

    story: Mapped[Story] = relationship(back_populates="scenes")

    def reset_from(self, stage: str) -> None:
        """Mark `stage` and every later stage as needing a re-run; the final video is now stale."""
        for st in STAGES[STAGES.index(stage):]:
            setattr(self, f"{st}_status", "pending")
            setattr(self, f"{st}_error", None)
        if self.story is not None:
            self.story.final_path = None


_engine = None
Session = sessionmaker(expire_on_commit=False)


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{paths.db_path()}", connect_args={"timeout": 30})

        @event.listens_for(_engine, "connect")
        def _pragmas(conn, _):
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        Session.configure(bind=_engine)
    return _engine


def init_db() -> None:
    Base.metadata.create_all(engine())
    _add_missing_columns()


def _add_missing_columns() -> None:
    """Tiny forward-only migration: add columns that newer code defines but an older DB lacks."""
    from sqlalchemy import inspect, text
    eng = engine()
    insp = inspect(eng)
    with eng.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name not in existing:
                    ddl = col.type.compile(dialect=eng.dialect)
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {ddl}'))


def reset_engine() -> None:
    """Drop the cached engine (tests, or after VC_DATA_DIR changes)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
