import json

import pytest
import responses

from desktop.services import story_ai

URL = "https://api.deepseek.com/chat/completions"
CFG = {"ai_provider": "deepseek", "deepseek_api_key": "sk-test", "groq_api_key": ""}


def _reply(content, status=200):
    body = content if isinstance(content, str) else json.dumps(content)
    responses.add(responses.POST, URL, status=status,
                  json={"choices": [{"message": {"content": body}}]} if status == 200 else {"error": "x"})


@responses.activate
def test_generate_story():
    _reply({"title": "Lost City", "content": "It began at dawn.", "youtube_title": "YT",
            "youtube_description": "D", "youtube_tags": "a,b"})
    out = story_ai.generate_story(CFG, "lost city", "story", "9:16", "none")
    assert out["title"] == "Lost City" and out["content"] == "It began at dawn."
    req = responses.calls[0].request
    body = json.loads(req.body)
    assert req.headers["Authorization"] == "Bearer sk-test"
    assert body["model"] == "deepseek-chat" and body["response_format"] == {"type": "json_object"}
    assert "130-160 words" in body["messages"][1]["content"]


@responses.activate
def test_talking_style_prompt_uses_opening():
    _reply({"title": "T", "content": "c"})
    story_ai.generate_story(CFG, "x", "story", "16:9", "vlog")
    prompt = json.loads(responses.calls[0].request.body)["messages"][1]["content"]
    assert "TALKING STYLE: Vlog" in prompt and "never copy" in prompt and "500-650 words" in prompt
    assert "MANDATORY" not in prompt


def test_missing_key_raises():
    with pytest.raises(story_ai.StoryAIError, match="API key"):
        story_ai.chat({**CFG, "deepseek_api_key": ""}, "s", "u")


@responses.activate
def test_http_error_raises():
    _reply("", status=500)
    with pytest.raises(story_ai.StoryAIError):
        story_ai.generate_story(CFG, "x", "story", "16:9", "none")


@responses.activate
def test_image_prompts_map_indices_and_fall_back():
    _reply({"0": "red lighthouse cliff", "2": "storm boat waves"})
    out = story_ai.generate_image_prompts(CFG, ["The lighthouse.", "So, honestly, the keeper climbed.", "A boat."])
    assert out[0] == "red lighthouse cliff" and out[2] == "storm boat waves"
    assert out[1] == "honestly the keeper climbed"   # cleaned fallback ("So," removed)
    # fillers only match whole words ("also" must not lose its "so")
    assert story_ai.clean_image_prompt("He also ran, basically, home.") == "He also ran home"


@responses.activate
def test_split_scenes_drops_short_and_appends_style_hint():
    _reply({"0": "celebrity red carpet", "1": "movie premiere crowd"})
    scenes = story_ai.split_scenes("Wow. The star arrived at the gala tonight! Fans outside went totally wild "
                                   "for her.", "hollywood_hype", "none", CFG)
    assert [s["narration"] for s in scenes] == ["Wow. The star arrived at the gala tonight!",
                                                 "Fans outside went totally wild for her."]
    assert scenes[0]["image_prompt"] == "celebrity red carpet, news celebrity"


@responses.activate
def test_topic_fallback():
    _reply("", status=500)
    assert story_ai.generate_topic(CFG, "", "science_short") == "Black Holes"


@responses.activate
def test_image_prompts_follow_image_style():
    _reply({"0": "cute cartoon lighthouse"})
    story_ai.generate_image_prompts(CFG, ["The lighthouse stood alone."], image_style="cartoon")
    prompt = json.loads(responses.calls[0].request.body)["messages"][1]["content"]
    assert "cartoon" in prompt.lower() and "kids" in prompt.lower()


@responses.activate
def test_split_scenes_with_image_style_skips_content_hint():
    _reply({"0": "celebrity red carpet"})
    scenes = story_ai.split_scenes("The star arrived at the gala tonight!", "hollywood_hype", "none", CFG,
                                   image_style="fashion")
    assert scenes[0]["image_prompt"] == "celebrity red carpet"   # style words are added at search time


@responses.activate
def test_news_style_fetches_real_headlines(monkeypatch):
    monkeypatch.setattr(story_ai.news, "headlines",
                        lambda q, style, **k: [{"title": "Studio confirms sequel", "source": "Variety",
                                                "published": "Mon, 02 Nov 2026", "snippet": ""}])
    _reply({"title": "T", "content": " ".join(["word"] * 140)})
    story_ai.generate_story(CFG, "new movie", "hollywood_hype", "9:16", "none")
    prompt = json.loads(responses.calls[0].request.body)["messages"][1]["content"]
    assert "Studio confirms sequel" in prompt and "Variety" in prompt


@responses.activate
def test_short_script_gets_one_expand_pass():
    _reply({"title": "T", "content": "Too short a script."})
    _reply({"content": " ".join(["longer"] * 140)})
    out = story_ai.generate_story(CFG, "x", "story", "9:16", "none")
    assert len(out["content"].split()) == 140 and len(responses.calls) == 2
    assert "130-160 words" in json.loads(responses.calls[1].request.body)["messages"][1]["content"]


@responses.activate
def test_good_length_script_is_not_expanded():
    _reply({"title": "T", "content": " ".join(["ok"] * 135)})
    story_ai.generate_story(CFG, "x", "story", "9:16", "none")
    assert len(responses.calls) == 1


def test_channel_name_from_settings_reaches_prompt(monkeypatch):
    seen = {}
    monkeypatch.setattr(story_ai, "chat", lambda cfg, system, user, *a, **k: seen.setdefault("p", user) and
                        json.dumps({"title": "T", "content": " ".join(["w"] * 140)}))
    story_ai.generate_story({**CFG, "channel_name": "The 60s Lab"}, "x", "story", "9:16", "none")
    assert "The 60s Lab" in seen["p"]


def test_split_merges_short_sentences_and_keeps_quotes():
    text = ("Okay so storytime. I sped up. So did it. I slowed down. It slowed too. "
            "Then a voice, warm and muffled, said: 'Put. It. Down.' I froze right there in the kitchen.")
    scenes = [s["narration"] for s in story_ai.split_scenes(text)]
    assert all(len(s.split()) >= 6 for s in scenes[:-1])
    assert any("'Put. It. Down.'" in s for s in scenes)               # the quote is never split
    assert " ".join(scenes).split() == text.split()                   # nothing lost or reordered


def test_talking_style_adds_no_image_hint():
    scenes = story_ai.split_scenes("The teddy bear blinked at me in the dark room.", "story", "storytime")
    assert "person talking" not in scenes[0]["image_prompt"]
