"""Real headlines from Google News RSS (free, no key) for the news-based content styles.

The AI writer cannot browse the web, so news styles are written only from these headlines."""
import xml.etree.ElementTree as ET

import requests

EDITIONS = {"bollywood_masala": ("hi", "IN", "IN:hi")}
DEFAULT_EDITION = ("en-US", "US", "US:en")


def headlines(query: str, style: str = "", limit: int = 5, days: int = 7) -> list[dict]:
    """Latest headlines for `query`: [{title, source, published, link, snippet}]. [] on any failure."""
    hl, gl, ceid = EDITIONS.get(style, DEFAULT_EDITION)
    try:
        res = requests.get("https://news.google.com/rss/search", timeout=15,
                           params={"q": f"{query} when:{days}d", "hl": hl, "gl": gl, "ceid": ceid},
                           headers={"User-Agent": "video-creator/1.0"})
        res.raise_for_status()
        root = ET.fromstring(res.content)
    except (requests.RequestException, ET.ParseError):
        return []
    out = []
    for it in root.findall("./channel/item")[:limit]:
        title, source = (it.findtext("title") or "").strip(), (it.findtext("source") or "").strip()
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3].strip()
        if not title:
            continue
        published = " ".join((it.findtext("pubDate") or "").split()[:4])
        out.append({"title": title, "source": source, "published": published,
                    "link": it.findtext("link") or "", "snippet": ""})
    return out
