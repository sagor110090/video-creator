"""One-time import of the Laravel app's SQLite data and rendered media."""
import shutil
import sqlite3
from datetime import date, datetime, time
from pathlib import Path

from desktop.core import db, paths
from desktop.pipeline import ffmpeg

STATUS_MAP = {"completed": "done", "failed": "failed"}  # pending/processing -> draft


def _dt(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", ""))
    except ValueError:
        return None


def _rows(con, table):
    try:
        return [dict(r) for r in con.execute(f"select * from {table}")]
    except sqlite3.OperationalError:
        return []


def import_laravel(laravel_root, Session) -> dict | None:
    """Returns counts, or None if already imported (marker file present)."""
    laravel_root = Path(laravel_root)
    marker = paths.data_dir() / ".imported_laravel"
    if marker.exists():
        return None
    con = sqlite3.connect(laravel_root / "database" / "database.sqlite")
    con.row_factory = sqlite3.Row
    media_root = laravel_root / "storage" / "app" / "public"
    counts = {"channels": 0, "schedules": 0, "stories": 0, "scenes": 0}
    with Session() as s:
        channels, schedules = {}, {}
        for r in _rows(con, "youtube_tokens"):
            ch = db.Channel(channel_id=r.get("channel_id"), title=r.get("channel_title"),
                            thumbnail=r.get("channel_thumbnail"), access_token=r.get("access_token") or "",
                            refresh_token=r.get("refresh_token"), expires_at=_dt(r.get("expires_at")))
            s.add(ch)
            s.flush()
            channels[r["id"]] = ch.id
            counts["channels"] += 1
        for r in _rows(con, "video_schedules"):
            sch = db.Schedule(topic=r["topic"], style=r.get("style") or "story",
                              talking_style=r.get("talking_style"), aspect_ratio=r.get("aspect_ratio") or "16:9",
                              channel_id=channels.get(r.get("youtube_token_id")),
                              scheduled_time=time.fromisoformat(str(r["scheduled_time"])[:8]),
                              last_run_at=date.fromisoformat(r["last_run_at"]) if r.get("last_run_at") else None,
                              status="active", last_error=r.get("last_error"))
            s.add(sch)
            s.flush()
            schedules[r["id"]] = sch.id
            counts["schedules"] += 1
        scenes_by_story = {}
        for r in _rows(con, "scenes"):
            scenes_by_story.setdefault(r["story_id"], []).append(r)
        for r in _rows(con, "stories"):
            st = db.Story(title=r.get("title"), content=r["content"], style=r.get("style") or "story",
                          talking_style=r.get("talking_style"), aspect_ratio=r.get("aspect_ratio") or "16:9",
                          status=STATUS_MAP.get(r.get("status"), "draft"),
                          schedule_id=schedules.get(r.get("video_schedule_id")),
                          channel_id=channels.get(r.get("youtube_token_id")),
                          youtube_title=r.get("youtube_title"), youtube_description=r.get("youtube_description"),
                          youtube_tags=r.get("youtube_tags"), youtube_video_id=r.get("youtube_video_id"),
                          youtube_upload_status=r.get("youtube_upload_status"), youtube_error=r.get("youtube_error"),
                          publish_at=_dt(r.get("scheduled_for")), created_at=_dt(r.get("created_at")) or datetime.now())
            rows = sorted(scenes_by_story.get(r["id"], []), key=lambda x: x["order"])
            st.scenes = [db.Scene(order=x["order"], narration=x["narration"], image_prompt=x.get("image_prompt") or "")
                         for x in rows]
            s.add(st)
            s.flush()
            counts["stories"] += 1
            counts["scenes"] += len(rows)
            _copy_media(st, media_root / "videos" / str(r["id"]), media_root / (r.get("video_path") or ""))
        s.commit()
    con.close()
    marker.write_text(datetime.now().isoformat())
    return counts


def _copy_media(story, old_dir: Path, old_final: Path) -> None:
    """Old worker named files by scene position: scene_<i>_{img.jpg,aud.mp3,vid.mp4}."""
    if not old_dir.is_dir():
        return
    for i, sc in enumerate(story.scenes):
        d = paths.scene_dir(story.id, sc.id)
        img, aud, vid = (old_dir / f"scene_{i}_{n}" for n in ("img.jpg", "aud.mp3", "vid.mp4"))
        if img.exists():
            shutil.copy(img, d / "image.jpg")
            sc.image_path, sc.image_status, sc.image_source = str(d / "image.jpg"), "done", "imported"
        if aud.exists():
            try:
                ffmpeg.run(["-i", aud, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", d / "voice.wav"])
                sc.voice_path, sc.voice_status, sc.voice_engine = str(d / "voice.wav"), "done", "imported"
                sc.duration_s = ffmpeg.probe_duration(d / "voice.wav")
            except ffmpeg.FFmpegError:
                pass
        if vid.exists() and sc.voice_status == "done" and sc.image_status == "done":
            shutil.copy(vid, d / "clip.mp4")
            sc.clip_path, sc.clip_status = str(d / "clip.mp4"), "done"
    if old_final.is_file():
        dest = paths.story_dir(story.id) / "final.mp4"
        shutil.copy(old_final, dest)
        story.final_path = str(dest)
