"""Filesystem locations. Everything the app writes lives under data_dir()."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    override = os.environ.get("VC_DATA_DIR")
    d = Path(override) if override else Path.home() / "Library" / "Application Support" / "VideoCreator"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "videocreator.db"


def settings_path() -> Path:
    return data_dir() / "settings.json"


def story_dir(story_id: int) -> Path:
    d = data_dir() / "stories" / str(story_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def scene_dir(story_id: int, scene_id: int) -> Path:
    d = story_dir(story_id) / "scenes" / str(scene_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def assets_dir() -> Path:
    return PACKAGE_DIR / "assets"
