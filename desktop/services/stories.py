"""Creating stories (shared by the dashboard and the scheduler) and marking manual uploads."""
import re
from datetime import datetime

from desktop.core import db
from desktop.services import story_ai


def create_story(title, content, style, talking_style, aspect_ratio, cfg, yt=None, **extra) -> int:
    """Split into scenes (AI image prompts) and save. Blocking: call off the GUI thread."""
    from desktop.pipeline.images import resolve_style
    image_style = extra.get("image_style") or "auto"
    scenes = story_ai.split_scenes(content, style, talking_style, cfg,
                                   image_style=resolve_style(image_style, style))
    if not scenes:
        raise story_ai.StoryAIError("The script has no sentences long enough to become scenes.")
    yt = yt or {}
    with db.Session() as s:
        st = db.Story(title=title or "Untitled", content=content, style=style, talking_style=talking_style,
                      aspect_ratio=aspect_ratio, youtube_title=yt.get("youtube_title"),
                      youtube_description=yt.get("youtube_description"), youtube_tags=yt.get("youtube_tags"),
                      **extra)
        st.scenes = [db.Scene(order=i, narration=x["narration"], image_prompt=x["image_prompt"])
                     for i, x in enumerate(scenes)]
        s.add(st)
        s.commit()
        return st.id


_YT_ID = re.compile(r"(?:youtu\.be/|[?&]v=|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")


def youtube_id(url_or_id: str | None) -> str | None:
    """Video id from a YouTube link (watch, youtu.be, shorts, embed) or a bare 11-character id."""
    text = (url_or_id or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", text):
        return text
    m = _YT_ID.search(text)
    return m.group(1) if m else None


def mark_uploaded(story_id: int, url: str | None = None) -> None:
    """The user uploaded this video themselves. Stops automatic uploading and counts it as uploaded."""
    with db.Session() as s:
        st = s.get(db.Story, story_id)
        st.youtube_upload_status = "manual"
        st.youtube_video_id = youtube_id(url) or st.youtube_video_id
        st.youtube_error = None
        st.uploaded_at = st.uploaded_at or datetime.now()
        s.commit()


def unmark_uploaded(story_id: int) -> None:
    """Undo mark_uploaded. Uploads the app made itself are left alone."""
    with db.Session() as s:
        st = s.get(db.Story, story_id)
        if st.youtube_upload_status != "manual":
            return
        st.youtube_upload_status = st.youtube_video_id = st.uploaded_at = None
        s.commit()
