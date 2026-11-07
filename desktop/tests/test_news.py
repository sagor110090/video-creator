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
