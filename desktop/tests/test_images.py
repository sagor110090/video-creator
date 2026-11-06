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


def test_extract_keywords():
    assert images.extract_keywords("So the old man walked to the sea", 3) == "old man walked"
