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
    assert "140-160" in body["messages"][1]["content"]


@responses.activate
def test_talking_style_prompt_uses_opening():
    _reply({"title": "T", "content": "c"})
    story_ai.generate_story(CFG, "x", "story", "16:9", "vlog")
    prompt = json.loads(responses.calls[0].request.body)["messages"][1]["content"]
    assert "Okay, we NEED to talk about" in prompt and "500-600" in prompt


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
    scenes = story_ai.split_scenes("Wow. The star arrived at the gala tonight! Fans went totally wild outside.",
                                   "hollywood_hype", "none", CFG)
    assert [s["narration"] for s in scenes] == ["The star arrived at the gala tonight!",
                                                 "Fans went totally wild outside."]
    assert scenes[0]["image_prompt"] == "celebrity red carpet, news celebrity"


@responses.activate
def test_news_unwraps_and_errors_return_empty():
    _reply({"news": [{"title": "A", "snippet": "s"}]})
    assert story_ai.search_news(CFG, "q", "hollywood_hype") == [{"title": "A", "snippet": "s"}]
    _reply("", status=500)
    assert story_ai.search_news(CFG, "q", "hollywood_hype") == []


@responses.activate
def test_topic_fallback():
    _reply("", status=500)
    assert story_ai.generate_topic(CFG, "", "science_short") == "Black Holes"
