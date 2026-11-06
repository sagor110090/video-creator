from sqlalchemy import create_engine, text

from desktop.core import db, paths


def _story(s, n_scenes=2):
    story = db.Story(title="T", content="A. B.", aspect_ratio="16:9")
    for i in range(n_scenes):
        story.scenes.append(db.Scene(order=i, narration=f"n{i}", image_prompt=f"p{i}"))
    s.add(story)
    s.commit()
    return story


def test_story_with_ordered_scenes(Session):
    with Session() as s:
        story = _story(s)
        sid = story.id
    with Session() as s:
        story = s.get(db.Story, sid)
        assert story.status == "draft"
        assert [sc.order for sc in story.scenes] == [0, 1]
        assert story.scenes[0].image_status == "pending"


def test_reset_from_voice_keeps_image(Session):
    with Session() as s:
        story = _story(s, 1)
        sc = story.scenes[0]
        for st in db.STAGES:
            setattr(sc, f"{st}_status", "done")
        story.final_path = "/x/final.mp4"
        sc.reset_from("voice")
        s.commit()
        assert (sc.image_status, sc.voice_status, sc.clip_status) == ("done", "pending", "pending")
        assert story.final_path is None


def test_second_engine_can_write(Session):
    with Session() as s:
        _story(s, 1)
    other = create_engine(f"sqlite:///{paths.db_path()}", connect_args={"timeout": 5})
    with other.begin() as c:
        c.execute(text("update stories set status='rendering'"))
    with Session() as s:
        assert s.query(db.Story).one().status == "rendering"


def test_init_db_adds_missing_columns(data_dir):
    import sqlite3
    con = sqlite3.connect(paths.db_path())
    con.execute("create table stories (id integer primary key, title varchar, content text not null, "
                "status varchar not null default 'draft')")
    con.execute("insert into stories (content) values ('old row')")
    con.commit()
    con.close()
    db.reset_engine()
    db.init_db()
    cols = {r[1] for r in sqlite3.connect(paths.db_path()).execute("pragma table_info(stories)")}
    assert {"uploaded_at", "rendered_at", "publish_at", "final_path"} <= cols
    with db.Session() as s:
        assert s.query(db.Story).one().content == "old row"
