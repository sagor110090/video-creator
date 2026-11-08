"""Character reference photos: one face photo per video, kept in every AI-generated scene."""
import re
import shutil
from pathlib import Path

from desktop.core import paths

IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def library_dir() -> Path:
    d = paths.data_dir() / "character"
    d.mkdir(parents=True, exist_ok=True)
    return d


def add_image(src) -> Path:
    """Copy an image into the library (unique, filesystem-safe name). Returns the new path."""
    src = Path(src)
    stem = re.sub(r"[^\w\- ]+", "", src.stem).strip() or "character"
    dest = library_dir() / f"{stem}{src.suffix.lower()}"
    n = 2
    while dest.exists():
        if dest.read_bytes() == src.read_bytes():
            return dest           # same image added twice
        dest = library_dir() / f"{stem} {n}{src.suffix.lower()}"
        n += 1
    shutil.copy(src, dest)
    return dest
