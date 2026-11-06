import sqlite3
from pathlib import Path

from desktop.core import db, import_laravel
from desktop.pipeline import images, voice


def _laravel(tmp_path) -> Path:
    root = tmp_path / "laravel"
    (root / "database").mkdir(parents=True)
    con = sqlite3.connect(root / "database" / "database.sqlite")
    con.executescript("""
    create table youtube_tokens (id integer primary key, access_token text, refresh_token text,
        expires_at datetime, channel_id text, channel_title text, channel_thumbnail text);
    create table video_schedules (id integer primary key, topic text, style text, aspect_ratio text,
        youtube_token_id integer, status text, scheduled_time time, last_run_at date,
        talking_style text, last_error text);
    create table stories (id integer primary key, title text, content text, status text, video_path text,
        aspect_ratio text, style text, talking_style text, youtube_title text, youtube_description text,
        youtube_tags text, youtube_video_id text, youtube_upload_status text, youtube_token_id integer,
        youtube_error text, scheduled_for datetime, video_schedule_id integer, created_at datetime);
    create table scenes (id integer primary key, story_id integer, "order" integer, narration text,
        image_prompt text);
    insert into youtube_tokens values (1,'tok','ref','2026-01-01 00:00:00','UC1','My Channel',null);
    insert into video_schedules values (1,'space facts','science_short','9:16',1,'pending','09:00:00',
        '2026-11-01','none',null);
    insert into stories (id,title,content,status,video_path,aspect_ratio,style,youtube_token_id,
        video_schedule_id,created_at) values
        (1,'Done one','A. B.','completed','videos/1/final_video.mp4','16:9','story',1,1,'2026-11-01 10:00:00'),
        (2,'Stuck one','C.','processing',null,'9:16','story',null,null,'2026-11-02 10:00:00');
    insert into scenes values (10,1,0,'A.','sea'),(11,1,1,'B.','sky'),(12,2,0,'C.','city');
    """)
    con.commit()
    con.close()
    vids = root / "storage" / "app" / "public" / "videos" / "1"
    vids.mkdir(parents=True)
    images.placeholder(vids / "scene_0_img.jpg", "16:9")
    voice.make_voice(vids / "scene_0_aud.wav", "a b c", engine=voice.StubEngine())
    (vids / "scene_0_aud.wav").rename(vids / "scene_0_aud.mp3")  # ffmpeg sniffs content, name is enough
    (vids / "scene_0_vid.mp4").write_bytes(b"x")
    (vids / "final_video.mp4").write_bytes(b"final")
    return root


def test_import(Session, tmp_path):
    root = _laravel(tmp_path)
    counts = import_laravel.import_laravel(root, Session)
    assert counts == {"channels": 1, "schedules": 1, "stories": 2, "scenes": 3}
    with Session() as s:
        done, stuck = s.query(db.Story).order_by(db.Story.created_at).all()
        assert (done.status, stuck.status) == ("done", "draft")
        assert Path(done.final_path).read_bytes() == b"final"
        assert done.channel_id is not None and done.schedule_id is not None
        first, second = done.scenes
        assert (first.image_status, first.voice_status, first.clip_status) == ("done",) * 3
        assert first.image_source == "imported" and first.duration_s > 0
        assert Path(first.voice_path).suffix == ".wav"
        assert second.image_status == "pending"
        sch = s.query(db.Schedule).one()
        assert sch.topic == "space facts" and str(sch.scheduled_time) == "09:00:00"
    assert import_laravel.import_laravel(root, Session) is None  # idempotent
