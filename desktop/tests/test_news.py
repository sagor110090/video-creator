import re

import responses

from desktop.services import news

RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Studio confirms sequel - Variety</title><source>Variety</source>
<pubDate>Mon, 02 Nov 2026 10:00:00 GMT</pubDate><link>https://news.google.com/a</link>
<description>&lt;a href="x"&gt;Studio confirms sequel&lt;/a&gt;</description></item>
<item><title>Star spotted in Paris - People.com</title><source>People.com</source>
<pubDate>Tue, 03 Nov 2026 10:00:00 GMT</pubDate><link>https://news.google.com/b</link></item>
</channel></rss>"""


@responses.activate
def test_headlines_parsed_and_source_stripped():
    responses.add(responses.GET, re.compile(r"https://news\.google\.com/rss/search.*"), body=RSS)
    items = news.headlines("new movie", "hollywood_hype")
    assert [i["title"] for i in items] == ["Studio confirms sequel", "Star spotted in Paris"]
    assert items[0]["source"] == "Variety" and items[0]["published"] == "Mon, 02 Nov 2026"
    q = responses.calls[0].request.params
    assert q["hl"] == "en-US" and "when:7d" in q["q"]


@responses.activate
def test_bollywood_uses_hindi_edition():
    responses.add(responses.GET, re.compile(r"https://news\.google\.com/rss/search.*"), body=RSS)
    news.headlines("SRK", "bollywood_masala")
    q = responses.calls[0].request.params
    assert (q["hl"], q["gl"], q["ceid"]) == ("hi", "IN", "IN:hi")


@responses.activate
def test_network_failure_returns_empty():
    responses.add(responses.GET, re.compile(r"https://news\.google\.com/rss/search.*"), status=503)
    assert news.headlines("x", "trade_wave") == []


ARTICLE_HTML = """<html><head><title>t</title><style>.x{color:red}</style>
<script>var junk = 1;</script></head><body><nav>Home News Sports Opinion</nav>
<article><div class="story-body">
<p>Salman &amp; the studio confirmed the trailer launches tomorrow in theaters nationwide.</p>
<p>The second paragraph adds box office detail for the opening weekend.</p>
<p>A third paragraph notes fan reactions pouring in within hours of the announcement.</p>
</div></article>
</body></html>"""


@responses.activate
def test_article_extracts_paragraphs_decodes_entities_and_truncates():
    responses.add(responses.GET, "https://example.com/a", body=ARTICLE_HTML)
    text = news.article("https://example.com/a")
    assert text.startswith("Salman & the studio")          # nav/script/style text gone, entity decoded
    assert "second paragraph" in text and "Home News" not in text and "junk" not in text
    assert len(text.split()) <= 150

    responses.replace(responses.GET, "https://example.com/a", body=ARTICLE_HTML)
    assert len(news.article("https://example.com/a", max_words=8).split()) == 8


@responses.activate
def test_article_without_p_tags_falls_back_to_stripped_text():
    responses.add(responses.GET, "https://example.com/b",
                  body="<html><body>Just one bare line of body text that is long enough to look like a sentence here.</body></html>")
    assert news.article("https://example.com/b").startswith("Just one bare line")


@responses.activate
def test_article_blocked_or_broken_returns_empty():
    responses.add(responses.GET, "https://example.com/403", status=403)
    assert news.article("https://example.com/403") == ""
    assert news.article("") == ""                            # no link at all
    assert news.article("https://offline.example/x") == ""   # unmocked -> connection error


def _google_link(target: str) -> str:
    """Build a Google News /rss/articles/ link that embeds `target` the way real ones do."""
    import base64
    raw = b'\x08\x13"' + bytes([len(target)]) + target.encode()
    return "https://news.google.com/rss/articles/" + base64.urlsafe_b64encode(raw).decode() + "?hl=hi"


@responses.activate
def test_google_news_links_resolve_to_the_publisher_article():
    responses.add(responses.GET, "https://example.com/story", body=ARTICLE_HTML)
    text = news.article(_google_link("https://example.com/story"))
    assert text.startswith("Salman & the studio")          # fetched the publisher, not the interstitial


@responses.activate
def test_undecodable_google_link_returns_empty(monkeypatch):
    monkeypatch.setattr(news, "gnewsdecoder", lambda link, interval=0: {"decoded_url": None})
    assert news.article("https://news.google.com/rss/articles/!!!notbase64!!!") == ""


NAV_JUNK = "<html><body><p>Home</p><p>Videos Sports Cricket Entertainment</p><p>Epaper</p></body></html>"


@responses.activate
def test_nav_junk_page_falls_back_to_headline_when_title_does_not_match():
    responses.add(responses.GET, "https://example.com/nav", body=NAV_JUNK)
    assert news.article("https://example.com/nav", title="Salman Khan trailer launch") == ""
    assert news.article("https://example.com/nav") == ""    # all-crumbs page: nothing worth feeding the AI
