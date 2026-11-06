"""Thin ffmpeg/ffprobe wrappers that raise instead of returning False."""
import os
import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def _find(name: str) -> str:
    return shutil.which(name) or next(
        (p for p in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}") if os.path.exists(p)), name)


FFMPEG = _find("ffmpeg")
FFPROBE = _find("ffprobe")


def run(args: list, timeout: float | None = None) -> None:
    """Run ffmpeg with `args` (without the leading 'ffmpeg'). Overwrites outputs."""
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *map(str, args)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        raise FFmpegError(res.stderr.strip()[-1500:] or f"ffmpeg exited {res.returncode}")


def probe_duration(path: str | Path) -> float:
    res = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except ValueError as e:
        raise FFmpegError(f"cannot read duration of {path}: {res.stderr.strip()}") from e
