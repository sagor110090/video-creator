"""Copy finished videos to the user's output folder (Settings → Video → Output folder)."""
import re
import shutil
from pathlib import Path

from desktop.core import db


def filename(story_id: int, title: str | None) -> str:
    """'<Title> (<id>).mp4' — readable, filesystem-safe, and unique per story."""
    clean = re.sub(r"[\\/]+", " ", title or "")
    clean = re.sub(r"[^\w\s'&,.-]", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" .") or "Untitled"
    return f"{clean[:80]} ({story_id}).mp4"


def export_story(story, output_dir) -> Path | None:
    """Copy the story's final video into output_dir; replaces this story's previous copy. Returns the new path."""
    if not output_dir or not story.final_path or not Path(story.final_path).is_file():
        return None
    out_dir = Path(output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / filename(story.id, story.title)
    old = Path(story.export_path) if story.export_path else None
    shutil.copy2(story.final_path, dest)
    if old and old != dest and old.is_file() and old.name.endswith(f"({story.id}).mp4"):
        old.unlink()          # renamed story: drop the copy with the old name
    story.export_path = str(dest)
    return dest


def export_all(Session, output_dir) -> int:
    """Copy every finished video into output_dir (used when the folder is first chosen). Returns the count."""
    n = 0
    with Session() as s:
        for st in s.query(db.Story).filter(db.Story.status == "done"):
            if export_story(st, output_dir):
                n += 1
        s.commit()
    return n
