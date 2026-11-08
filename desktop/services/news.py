"""Real headlines from Google News RSS (free, no key) for the news-based content styles.

The AI writer cannot browse the web, so news styles are written only from these headlines."""
import base64
import html as html_lib
import re
import xml.etree.ElementTree as ET

import requests
from googlenewsdecoder import gnewsdecoder

EDITIONS = {"bollywood_masala": ("hi", "IN", "IN:hi")}
DEFAULT_EDITION = ("en-US", "US", "US:en")

_BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_TAG_BLOCK = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_P_TAG = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_ANY_TAG = re.compile(r"<[^>]+>")

_GOOGLE_ARTICLE = re.compile(r"news\.google\.com/rss/articles/([^?/&]+)")
_URL_IN_PROTO = re.compile(rb"https?://[^\s\"'<>\\]+")
_SENTENCE_END = re.compile(r"[.!?।]")


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


def _resolve(link: str) -> str:
    """Google News RSS links are JS redirects, not HTTP ones. Old ids carry the publisher URL
    base64-packed (protobuf: \\x08\\x13\\x22 <len> <url>); new ids (AU_yqL...) need Google's
    batchexecute endpoint, which gnewsdecoder handles. Direct links pass through."""
    m = _GOOGLE_ARTICLE.search(link)
    if not m:
        return link
    try:                                                  # fast path: URL packed in the id itself
        raw = base64.urlsafe_b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        hit = _URL_IN_PROTO.search(raw)
        if hit:
            return hit.group(0).decode("ascii", "ignore")
    except (ValueError, TypeError):
        pass
    try:                                                  # new-format ids: ask Google to decode
        return (gnewsdecoder(link, interval=0) or {}).get("decoded_url") or ""
    except Exception:
        return ""


def article(link: str, max_words: int = 150, title: str = "") -> str:
    """First ~max_words of an article's body text, for a headline the user picked. '' whenever the
    page can't be read (blocked, timeout, JS-rendered, paywalled) — the AI then writes from the
    headline alone. With `title`, text that never mentions the headline's subject is treated as
    nav junk and dropped, so garbage never reaches the prompt as 'facts'."""
    target = _resolve(link)
    if not target:
        return ""
    try:
        res = requests.get(target, timeout=10, headers={"User-Agent": _BROWSER_UA})
        res.raise_for_status()
    except requests.RequestException:
        return ""
    try:                                                  # readability: main-content node, nav dropped structurally
        from readability import Document
        raw = html_lib.unescape(_ANY_TAG.sub(" ", Document(res.text).summary(html_partial=True)))
        raw = " ".join(re.sub(r"\s+", " ", raw).split())
        # ...then sentence-shaped text only (nav crumb runs never end a sentence)
        text = " ".join(s.strip() for s in re.split(r"(?<=[.!?।])\s+", raw)
                        if len(s.split()) >= 8 and _SENTENCE_END.search(s))
    except Exception:
        text = ""
    if len(text.split()) < 10:                            # readability whiffed or JS-rendered page
        try:                                              # fallback: real <p> sentences only
            from selectolax.parser import HTMLParser
            paras = [p.text(separator=" ", strip=True) for p in HTMLParser(res.text).css("p")]
        except Exception:
            paras = [html_lib.unescape(_ANY_TAG.sub(" ", p))
                     for p in _P_TAG.findall(_TAG_BLOCK.sub(" ", res.text))]
        # body sentences only: 8+ words AND ending punctuation; nav menus are crumb lists
        text = " ".join(p for p in paras if len(p.split()) >= 8 and _SENTENCE_END.search(p))
    if len(text.split()) < 10:
        return ""                                         # nothing worth feeding the AI as 'facts'
    text = " ".join(re.sub(r"\s+", " ", text).split()[:400])
    if title:                                             # quality gate: the story must be about the headline
        strip = "।,.:;\"'()[]?!‘’“”-"
        key = {w.strip(strip) for w in title.lower().split() if len(w) > 3}
        seen = {w.strip(strip) for w in text.lower().split()}
        if key and not key & seen:
            return ""
    return " ".join(text.split()[:max_words])
