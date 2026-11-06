import io
import re

import responses
from PIL import Image

from desktop.pipeline import images

CFG = {"image_sources": "pexels,pixabay,openverse,pollinations,loremflickr",
       "pexels_api_key": "", "pixabay_api_key": "", "pollinations_token": ""}


def _jpeg(w=1600, h=900, fmt="JPEG"):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (30, 90, 160)).save(buf, fmt)
    return buf.getvalue()


def _fail_all():
    for url in [re.compile(r"https://api\.openverse\.org/.*"),
                re.compile(r"https://image\.pollinations\.ai/.*"),
                re.compile(r"https://loremflickr\.com/.*")]:
        responses.add(responses.GET, url, status=500)


@responses.activate
def test_openverse_hit_saved_as_jpeg(tmp_path):
    responses.add(responses.GET, re.compile(r"https://api\.openverse\.org/v1/images/.*"), json={
        "results": [{"url": "https://img.example/a.webp", "width": 1600, "license": "cc0",
                     "foreign_landing_url": "https://src.example/a"}]})
    responses.add(responses.GET, "https://img.example/a.webp", body=_jpeg(fmt="WEBP"))
    out = tmp_path / "image.jpg"
    hit = images.fetch_scene_image("lighthouse sunset", out, "16:9", CFG)
    assert (hit.source, hit.license, hit.url) == ("openverse", "cc0", "https://src.example/a")
    assert out.read_bytes()[:3] == b"\xff\xd8\xff"
    # no key -> pexels/pixabay never called
    assert not any("pexels" in c.request.url or "pixabay" in c.request.url for c in responses.calls)


@responses.activate
def test_falls_back_to_previous_scene(tmp_path):
    _fail_all()
    prev = tmp_path / "prev.jpg"
    prev.write_bytes(_jpeg())
    out = tmp_path / "image.jpg"
    hit = images.fetch_scene_image("anything", out, "16:9", CFG, previous_image=prev)
    assert hit.source == "previous_scene"
    assert out.read_bytes() == prev.read_bytes()


@responses.activate
def test_placeholder_when_everything_fails(tmp_path):
    _fail_all()
    out = tmp_path / "image.jpg"
    hit = images.fetch_scene_image("anything", out, "9:16", CFG)
    assert hit.source == "placeholder"
    assert Image.open(out).size == (1080, 1920)


def test_placeholder_only_source_makes_no_requests(tmp_path):
    out = tmp_path / "image.jpg"
    hit = images.fetch_scene_image("x", out, "16:9", {**CFG, "image_sources": "placeholder"})
    assert hit.source == "placeholder"


@responses.activate
def test_openverse_narrows_long_query(tmp_path):
    def handler(req):
        q = req.params["q"]
        if len(q.split()) > 3:
            return (200, {}, '{"results": []}')
        return (200, {}, '{"results": [{"url": "https://img.example/b.jpg", "width": 1600, "license": "pdm"}]}')
    responses.add_callback(responses.GET, re.compile(r"https://api\.openverse\.org/v1/images/.*"), callback=handler)
    responses.add(responses.GET, "https://img.example/b.jpg", body=_jpeg())
    # Pollinations accepts any prompt; Openverse is earlier in the order so it must still win.
    responses.add(responses.GET, re.compile(r"https://image\.pollinations\.ai/.*"), body=_jpeg())
    cfg = {**CFG, "image_sources": "openverse,pollinations"}
    hit = images.fetch_scene_image("old lighthouse stood alone rocky", tmp_path / "i.jpg", "16:9", cfg)
    assert hit.source == "openverse"
    assert not any("pollinations" in c.request.url for c in responses.calls)


def test_extract_keywords():
    assert images.extract_keywords("So the old man walked to the sea", 3) == "old man walked"


def test_cartoon_style_prefers_ai_with_style_words(tmp_path, monkeypatch):
    seen = []

    def fake(name):
        def fn(q, out, ar, cfg):
            seen.append((name, q, cfg.get("_ai_suffix"), cfg.get("_openverse_category"), cfg.get("_pixabay_type")))
            return images.placeholder(out, ar) if name == "openverse" else None
        return fn
    for n in ("pexels", "pixabay", "openverse", "pollinations", "loremflickr"):
        monkeypatch.setitem(images.SOURCES, n, fake(n))
    cfg = {**CFG, "image_sources": "pexels,openverse,pollinations"}
    images.fetch_scene_image("lighthouse on a cliff", tmp_path / "i.jpg", "16:9", cfg, image_style="cartoon")
    names = [s[0] for s in seen]
    assert names[:2] == ["pollinations", "pexels"]          # AI first for illustration styles
    poll, pex, ov = seen[0], seen[1], seen[2]
    assert "cartoon" in poll[2] and poll[1] == "lighthouse on a cliff"   # AI gets the style as a suffix
    assert pex[1] == "cartoon lighthouse on a cliff"                     # stock search gets style words first
    assert ov[3] == "illustration" and pex[4] == "illustration"


def test_auto_style_resolves_from_content_style():
    assert images.resolve_style("auto", "science_short") == "science"
    assert images.resolve_style("auto", "story") == "auto"
    assert images.resolve_style("cartoon", "science_short") == "cartoon"
    assert images.resolve_style("nonsense", "story") == "auto"
