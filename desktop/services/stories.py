"""Creating stories (shared by the dashboard and the scheduler)."""
from desktop.core import db
from desktop.services import story_ai


def create_story(title, content, style, talking_style, aspect_ratio, cfg, yt=None, **extra) -> int:
    """Split into scenes (AI image prompts) and save. Blocking: call off the GUI thread."""
    scenes = story_ai.split_scenes(content, style, talking_style, cfg)
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
