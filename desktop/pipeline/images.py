"""Scene images from free sources. Ported from ai_worker/worker.py; every result records its source."""
import base64
import random
import re
import shutil
import time
import urllib.parse
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

HEADERS = {"User-Agent": "video-creator/1.0 (+https://github.com/sagor110090/video-creator)"}

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
    'when', 'where', 'how', 'who', 'why', 'which', 'this', 'that', 'these',
    'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves',
    'imagine', 'picture', 'think', 'consider', 'suppose', 'visualize',
    'look', 'see', 'watch', 'notice', 'observe', 'video', 'scene', 'clip',
    'image', 'photo', 'shot', 'frame', 'screen', 'camera',
    'know', 'can', 'could', 'would', 'should', 'will', 'shall',
    'just', 'only', 'very', 'really', 'too', 'quite', 'rather', 'much',
    'so', 'here', 'heres', 'question', 'answer', 'ask', 'asking'
}


# Image styles. stock_words go in front of stock-photo searches; ai_suffix describes the look to the AI
# generator; prefer_ai puts AI generation first (stock sites rarely have a cartoon of a specific scene);
# guidance tells the AI writer what kind of image search phrases to produce.
IMAGE_STYLES = {
    "auto": {"label": "Auto (match the story)"},
    "photo": {"label": "Realistic photos", "openverse_category": "photograph",
              "ai_suffix": "realistic photo, natural lighting",
              "guidance": "Real-world photographs of real places, objects and people."},
    "cartoon": {"label": "Cartoon / kids", "prefer_ai": True, "stock_words": "cartoon",
                "pixabay_type": "illustration", "openverse_category": "illustration",
                "ai_suffix": "cute colorful cartoon illustration for children, storybook style, simple shapes, bright",
                "guidance": "Cute, friendly cartoon scenes for kids: smiling characters, animals, bright simple "
                            "places. Nothing scary or violent."},
    "anime": {"label": "Anime", "prefer_ai": True, "stock_words": "anime",
              "pixabay_type": "illustration", "openverse_category": "illustration",
              "ai_suffix": "anime style illustration, vibrant colors, detailed background",
              "guidance": "Anime-style scenes with expressive characters and detailed backgrounds."},
    "3d": {"label": "3D animation", "prefer_ai": True, "stock_words": "3d render",
           "pixabay_type": "illustration",
           "ai_suffix": "3D animated movie still, soft lighting, expressive cute characters, high detail",
           "guidance": "Scenes like a 3D animated family movie: expressive characters, soft lighting."},
    "science": {"label": "Science & tech", "stock_words": "science",
                "ai_suffix": "scientific illustration, detailed, educational, clean background",
                "guidance": "Scientific visuals: labs, microscopes, space, cells, molecules, technology, "
                            "nature close-ups, diagrams."},
    "fashion": {"label": "Models & fashion", "stock_words": "fashion model", "openverse_category": "photograph",
                "ai_suffix": "fashion photography, professional model, studio lighting, editorial",
                "guidance": "Fashion and model photography: people posing, outfits, runway, studio portraits."},
    "cinematic": {"label": "Cinematic", "openverse_category": "photograph",
                  "ai_suffix": "cinematic film still, dramatic lighting, shallow depth of field",
                  "guidance": "Dramatic, movie-like shots with strong lighting and mood."},
}
AI_SOURCES = {"pollinations", "gemini", "openrouter"}
PAID_PROVIDERS = {"gemini": "Gemini", "openrouter": "OpenRouter"}


def resolve_style(image_style: str | None, content_style: str | None = None) -> str:
    """'auto' picks a style from the content style (science shorts get science images)."""
    style = image_style if image_style in IMAGE_STYLES else "auto"
    if style == "auto" and content_style == "science_short":
        return "science"
    if style == "auto" and content_style == "kids_story":
        return "cartoon"
    return style


@dataclass
class ImageHit:
    source: str
    url: str | None = None
    license: str | None = None
    note: str | None = None      # e.g. why Gemini was skipped and a free source used instead


def target_size(aspect_ratio: str) -> tuple[int, int]:
    return (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)


def extract_keywords(text: str, limit: int = 6) -> str:
    words = re.sub(r"[^\w\s]", " ", text).lower().split()
    out = []
    for w in words:
        if w not in STOPWORDS and len(w) > 2 and w not in out:
            out.append(w)
    return " ".join(out[:limit])


def _clean_query(query: str) -> str:
    q = query.replace('"', "").strip()
    for word in ["highly detailed", "8k", "4k", "photorealistic", "masterpiece", "stock photo", "premium"]:
        q = re.sub(rf"\b{word}\b", "", q, flags=re.IGNORECASE)
    return " ".join(q.split()[:8])


def _save(content: bytes, out: Path) -> bool:
    """Validate and save as JPEG (sources may return WebP/PNG)."""
    try:
        img = Image.open(BytesIO(content))
        img.load()
        if img.width < 300 or img.height < 300:
            return False
        img.convert("RGB").save(out, "JPEG", quality=92)
        return True
    except Exception:
        return False


def _fetch(url: str, out: Path, headers=None, timeout=20) -> bool:
    res = requests.get(url, headers=headers or HEADERS, timeout=timeout)
    return res.status_code == 200 and _save(res.content, out)


def _pexels(q, out, ar, cfg):
    key = cfg.get("pexels_api_key")
    if not key:
        return None
    res = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key}, timeout=10,
                       params={"query": q, "per_page": 1,
                               "orientation": "landscape" if ar == "16:9" else "portrait"})
    photos = res.json().get("photos", []) if res.status_code == 200 else []
    if photos and _fetch(photos[0]["src"]["large2x"], out):
        return ImageHit("pexels", photos[0].get("url"), "pexels")
    return None


def _pixabay(q, out, ar, cfg):
    key = cfg.get("pixabay_api_key")
    if not key:
        return None
    min_w, min_h = (1280, 720) if ar == "16:9" else (720, 1280)
    res = requests.get("https://pixabay.com/api/", timeout=10, params={
        "key": key, "q": q[:100], "image_type": cfg.get("_pixabay_type", "photo"), "safesearch": "true", "per_page": 3,
        "orientation": "horizontal" if ar == "16:9" else "vertical", "min_width": min_w, "min_height": min_h})
    for hit in (res.json().get("hits", []) if res.status_code == 200 else []):
        if _fetch(hit.get("largeImageURL"), out):
            return ImageHit("pixabay", hit.get("pageURL"), "pixabay")
    return None


def _openverse(q, out, ar, cfg):
    """Openverse matches every word, so long queries often return nothing: narrow 5 -> 3 -> 2 words."""
    words = q.split()
    for n in dict.fromkeys(x for x in (len(words), 3, 2) if 0 < x <= len(words)):
        hit = _openverse_once(" ".join(words[:n]), out, ar, cfg)
        if hit:
            return hit
    return None


def _openverse_once(q, out, ar, cfg):
    params = {"q": q, "license": cfg.get("openverse_licenses", "cc0,pdm"),
              "aspect_ratio": "wide" if ar == "16:9" else "tall",
              "size": "large", "mature": "false", "page_size": 10}
    if cfg.get("_openverse_category"):
        params["category"] = cfg["_openverse_category"]
    api = "https://api.openverse.org/v1/images/"
    res = requests.get(api, params=params, headers=HEADERS, timeout=15)
    results = res.json().get("results", []) if res.status_code == 200 else []
    if not results:  # clips are scale+cropped to fill, so any aspect ratio works
        params.pop("aspect_ratio")
        res = requests.get(api, params=params, headers=HEADERS, timeout=15)
        results = res.json().get("results", []) if res.status_code == 200 else []
    min_w = 1280 if ar == "16:9" else 720
    for r in results:
        if (r.get("width") or 0) < min_w:
            continue
        try:
            if _fetch(r["url"], out, timeout=25):
                return ImageHit("openverse", r.get("foreign_landing_url") or r["url"], r.get("license"))
        except requests.RequestException:
            continue
    return None


def _pollinations(q, out, ar, cfg):
    """AI-generated. Anonymous: 1 image / 45s per IP and a small logo; a free token removes both."""
    w, h = target_size(ar)
    headers = dict(HEADERS)
    if cfg.get("pollinations_token"):
        headers["Authorization"] = f"Bearer {cfg['pollinations_token']}"
    suffix = cfg.get("_ai_suffix") or "cinematic photo, natural lighting"
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(q + ', ' + suffix)}"
    params = {"width": w, "height": h, "model": "flux", "nologo": "true", "seed": random.randint(1, 10**6)}
    for attempt in range(2):
        res = requests.get(url, params=params, headers=headers, timeout=90)
        if res.status_code == 200:
            return ImageHit("pollinations", None, "ai-generated") if _save(res.content, out) else None
        if res.status_code in (402, 429) and attempt == 0:
            m = re.search(r"Retry after (\d+)s", res.text)
            time.sleep(min(int(m.group(1)) + 2 if m else 47, 50))
            continue
        return None
    return None


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_API_REVISION = "2026-05-20"
GEMINI_MODELS = {"gemini-nano-banana-2.1": "Nano Banana 2.1 — best (recommended)",
                 "gemini-3.1-flash-lite-image": "Nano Banana 2 Lite — fastest, cheapest",
                 "gemini-3-pro-image": "Nano Banana Pro — most detailed"}


class PaidImageError(RuntimeError):
    """A paid image provider failed; the scene falls back to free sources and keeps this as a note."""
    provider = "Paid images"


class GeminiError(PaidImageError):
    provider = "Gemini"


class OpenRouterError(PaidImageError):
    provider = "OpenRouter"


def _styled_prompt(q, cfg) -> str:
    style = cfg.get("_ai_suffix") or "realistic photo, natural lighting"
    return f"{q}. Visual style: {style}. A single image for a video scene, with no text, captions, logos or watermarks."


def _find_image_b64(obj):
    """Find base64 image bytes in a Gemini response, whatever its exact shape."""
    if isinstance(obj, dict):
        mime = obj.get("mime_type") or obj.get("mimeType") or ""
        if isinstance(obj.get("data"), str) and (obj.get("type") == "image" or mime.startswith("image/")):
            return obj["data"]
        for key in ("output_image", "inlineData", "inline_data"):
            if isinstance(obj.get(key), dict) and isinstance(obj[key].get("data"), str):
                return obj[key]["data"]
        values = obj.values()
    elif isinstance(obj, list):
        values = obj
    else:
        return None
    for v in values:
        found = _find_image_b64(v)
        if found:
            return found
    return None


def _gemini(q, out, ar, cfg):
    """Google Gemini image generation (paid; needs an API key). Raises GeminiError with the API's reason."""
    key = cfg.get("gemini_api_key", "").strip()
    if not key:
        raise GeminiError("no Gemini API key in Settings")
    prompt = _styled_prompt(q, cfg)
    body = {"model": cfg.get("gemini_image_model") or "gemini-nano-banana-2.1",
            "input": [{"type": "text", "text": prompt}],
            "response_format": {"type": "image", "aspect_ratio": "16:9" if ar == "16:9" else "9:16",
                                "image_size": cfg.get("gemini_image_size") or "2K", "mime_type": "image/jpeg"}}
    res = requests.post(GEMINI_URL, json=body, timeout=180, headers={
        "x-goog-api-key": key, "Content-Type": "application/json", "Api-Revision": GEMINI_API_REVISION})
    if res.status_code != 200:
        try:
            msg = res.json().get("error", {}).get("message") or res.text[:200]
        except ValueError:
            msg = res.text[:200]
        if res.status_code == 429 and "limit: 0" in msg and "free tier" in msg.lower():
            raise GeminiError("this Google account is on the free tier, which allows no image generation. "
                              "Enable billing for the key's project in Google AI Studio")
        raise GeminiError(f"HTTP {res.status_code}: {msg}")
    data = _find_image_b64(res.json())
    if not data:
        raise GeminiError("no image in the response (the prompt may have been blocked)")
    if not _save(base64.b64decode(data), out):
        raise GeminiError("the returned image could not be read")
    return ImageHit("gemini", None, "ai-generated (Gemini, SynthID)")


OPENROUTER_URL = "https://openrouter.ai/api/v1/images"
OPENROUTER_MODELS = {"google/gemini-2.5-flash-image": "Nano Banana (Gemini 2.5 Flash Image) — about $0.04 / image"}


def _openrouter(q, out, ar, cfg):
    """OpenRouter Image API (pay-as-you-go credits). Raises OpenRouterError with the API's reason."""
    key = cfg.get("openrouter_api_key", "").strip()
    if not key:
        raise OpenRouterError("no OpenRouter API key in Settings")
    body = {"model": cfg.get("openrouter_image_model") or "google/gemini-2.5-flash-image",
            "prompt": _styled_prompt(q, cfg), "n": 1, "aspect_ratio": "16:9" if ar == "16:9" else "9:16"}
    res = requests.post(OPENROUTER_URL, json=body, timeout=180, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "X-Title": "AI Video Creator"})
    if res.status_code != 200:
        try:
            msg = res.json().get("error", {}).get("message") or res.text[:200]
        except ValueError:
            msg = res.text[:200]
        if res.status_code == 402:
            raise OpenRouterError(f"not enough credits — add credits at openrouter.ai/settings/credits ({msg})")
        if res.status_code == 401:
            raise OpenRouterError("the API key was rejected — check it in Settings")
        raise OpenRouterError(f"HTTP {res.status_code}: {msg}")
    items = res.json().get("data") or []
    data = items[0].get("b64_json") if items else None
    if not data:
        raise OpenRouterError("no image in the response (the prompt may have been refused)")
    if not _save(base64.b64decode(data), out):
        raise OpenRouterError("the returned image could not be read")
    model = body["model"].split("/")[-1]
    return ImageHit("openrouter", None, f"ai-generated ({model} via OpenRouter)")


def _loremflickr(q, out, ar, cfg):
    w, h = target_size(ar)
    tag = urllib.parse.quote(q.split()[0] if q.strip() else "nature")
    url = f"https://loremflickr.com/{w}/{h}/{tag}"
    return ImageHit("loremflickr", url, "flickr-cc") if _fetch(url, out) else None


def placeholder(out: Path, aspect_ratio: str) -> ImageHit:
    Image.new("RGB", target_size(aspect_ratio), (18, 18, 28)).save(out, "JPEG", quality=90)
    return ImageHit("placeholder")


SOURCES = {"pexels": _pexels, "pixabay": _pixabay, "openverse": _openverse,
           "pollinations": _pollinations, "loremflickr": _loremflickr, "gemini": _gemini,
           "openrouter": _openrouter,
           # offline source for tests / no-network use; only used when listed explicitly
           "placeholder": lambda q, out, ar, cfg: placeholder(out, ar)}


def _source_order(cfg: dict) -> list[str]:
    names = [s.strip().lower() for s in cfg.get("image_sources", "").split(",")
             if s.strip() and s.strip().lower() not in PAID_PROVIDERS]
    if cfg.get("image_provider") in PAID_PROVIDERS:
        names = [cfg["image_provider"]] + names   # paid provider first; the free sources are the fallback
    if cfg.get("_prefer_ai"):
        names = [n for n in names if n in AI_SOURCES] + [n for n in names if n not in AI_SOURCES]
    return names


def _try_sources(query: str, out: Path, ar: str, cfg: dict) -> ImageHit | None:
    stock_words = cfg.get("_stock_words")
    for name in _source_order(cfg):
        fn = SOURCES.get(name)
        if fn is None:
            continue
        q = query if name in AI_SOURCES or not stock_words else f"{stock_words} {query}"
        try:
            hit = fn(q, out, ar, cfg)
            if hit:
                return hit
        except PaidImageError as e:
            cfg.setdefault("_errors", []).append(f"{e.provider} failed ({e}); used a free source instead")
        except Exception:
            continue
    return None


def fetch_scene_image(prompt: str, out, aspect_ratio: str, cfg: dict, previous_image=None,
                      image_style: str = "auto") -> ImageHit:
    """Never raises: sources → simpler query → generic query → previous scene's image → placeholder."""
    out = Path(out)
    st = IMAGE_STYLES.get(image_style, IMAGE_STYLES["auto"])
    cfg = dict(cfg, _prefer_ai=st.get("prefer_ai", False), _stock_words=st.get("stock_words"),
               _ai_suffix=st.get("ai_suffix"), _pixabay_type=st.get("pixabay_type", "photo"),
               _openverse_category=st.get("openverse_category"))
    queries = [_clean_query(prompt), extract_keywords(prompt, 3), "cinematic background"]
    def noted(hit):
        errors = list(dict.fromkeys(cfg.get("_errors", [])))
        hit.note = "; ".join(errors) or None
        return hit

    for q in dict.fromkeys(q for q in queries if q):
        hit = _try_sources(q, out, aspect_ratio, cfg)
        if hit:
            return noted(hit)
        if cfg.get("image_provider") in PAID_PROVIDERS and cfg.get("_errors"):
            cfg["image_provider"] = "free"   # don't pay for (or wait on) the same failure 3 times
    if previous_image and Path(previous_image).exists():
        shutil.copy(previous_image, out)
        return noted(ImageHit("previous_scene"))
    return noted(placeholder(out, aspect_ratio))
