"""App settings in <data>/settings.json (replaces the Laravel .env)."""
import json
import shutil
from pathlib import Path

from desktop.core import paths

DEFAULTS = {
    "ai_provider": "deepseek",          # deepseek | groq
    "deepseek_api_key": "",
    "groq_api_key": "",
    "pexels_api_key": "",
    "pixabay_api_key": "",
    "pollinations_token": "",
    "image_sources": "pexels,pixabay,openverse,pollinations,loremflickr",
    "voice_engine": "chatterbox",       # chatterbox | edge | stub (tests)
    "voice_sample": "",
    "background_music": True,
    "render_preset": "slow",
    "image_provider": "free",           # free | gemini
    "gemini_api_key": "",
    "gemini_image_model": "gemini-nano-banana-2.1",
    "gemini_image_size": "2K",
    "youtube_client_id": "",
    "youtube_client_secret": "",
}

# Laravel .env key -> settings key
ENV_MAP = {
    "AI_STORY_PROVIDER": "ai_provider",
    "DEEPSEEK_API_KEY": "deepseek_api_key",
    "GROQ_API_KEY": "groq_api_key",
    "PEXELS_API_KEY": "pexels_api_key",
    "PIXABAY_API_KEY": "pixabay_api_key",
    "POLLINATIONS_TOKEN": "pollinations_token",
    "IMAGE_SOURCES": "image_sources",
    "GEMINI_API_KEY": "gemini_api_key",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    p = paths.settings_path()
    if p.exists():
        cfg.update(json.loads(p.read_text()))
    return cfg


def save(cfg: dict) -> None:
    p = paths.settings_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    tmp.replace(p)


def get(key: str):
    return load()[key]


def _parse_env(env_path: Path) -> dict:
    out = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.split(" #")[0].strip().strip('"').strip("'")
    return out


def seed_from_env(env_path: Path) -> bool:
    """First run only: copy keys and the voice sample from the Laravel project. Returns True if seeded."""
    env_path = Path(env_path)
    if paths.settings_path().exists() or not env_path.exists():
        return False
    env = _parse_env(env_path)
    cfg = dict(DEFAULTS)
    for env_key, key in ENV_MAP.items():
        if env.get(env_key):
            cfg[key] = env[env_key]
    sample = env_path.parent / "public" / "audio" / "my-voice.wav"
    if sample.exists():
        dest = paths.data_dir() / "voice" / "sample.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(sample, dest)
        cfg["voice_sample"] = str(dest)
    save(cfg)
    return True
