"""Voice sample library: audio files in <data>/voice/ that Chatterbox can clone."""
import re
import shutil
from pathlib import Path

from desktop.core import paths

AUDIO = {".wav", ".mp3", ".m4a", ".flac", ".aiff"}


def library_dir() -> Path:
    d = paths.data_dir() / "voice"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_samples() -> list[Path]:
    return sorted((p for p in library_dir().iterdir() if p.suffix.lower() in AUDIO), key=lambda p: p.name.lower())


def add_sample(src) -> Path:
    """Copy an audio file into the library (unique, filesystem-safe name). Returns the new path."""
    src = Path(src)
    stem = re.sub(r"[^\w\- ]+", "", src.stem).strip() or "voice"
    dest = library_dir() / f"{stem}{src.suffix.lower()}"
    n = 2
    while dest.exists():
        if dest.read_bytes() == src.read_bytes():
            return dest           # same file added twice
        dest = library_dir() / f"{stem} {n}{src.suffix.lower()}"
        n += 1
    shutil.copy(src, dest)
    return dest


def display_name(path) -> str:
    return Path(path).stem.replace("_", " ").replace("-", " ").strip() or Path(path).name
