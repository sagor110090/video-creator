import random

import pytest

from desktop.services import prompts

ALL_STYLES = list(prompts.STYLES)


@pytest.mark.parametrize("style", ALL_STYLES)
@pytest.mark.parametrize("talking", list(prompts.TALKING_STYLES))
def test_no_fake_research_or_forced_catchphrases(style, talking):
    p = prompts.build_story_prompt("the moon", style, "9:16", talking, rng=random.Random(1))
    assert "researching this for" not in p
    assert "MANDATORY FIRST WORDS" not in p
    assert "{" not in p.split("Format your response")[0]       # no unfilled template fields
    # stock phrases appear only in the "never use" list, not as instructions to use them
    assert p.count("Trust me on this") <= 1 and "AVOID" in p


def test_hook_type_varies():
    hooks = {prompts.pick_hook(random.Random(i)) for i in range(40)}
    assert len(hooks) >= 5


def test_kids_style_is_gentle_and_simple():
    p = prompts.build_story_prompt("a lost puppy", "kids_story", "9:16", "none", rng=random.Random(2))
    low = p.lower()
    assert "ages 4" in low and "simple words" in low and "lesson" in low and "scary" in low


def test_channel_name_only_when_set_and_not_for_kids():
    p = prompts.build_story_prompt("x", "story", "9:16", "none", channel_name="The 60s Lab", rng=random.Random(3))
    assert "The 60s Lab" in p
    assert "The 60s Lab" not in prompts.build_story_prompt("x", "kids_story", "9:16", "none",
                                                           channel_name="The 60s Lab", rng=random.Random(3))
    assert "channel name" not in prompts.build_story_prompt("x", "story", "9:16", "none", rng=random.Random(3)).lower()


def test_nonfiction_styles_require_accuracy():
    for style in ("history", "facts", "science_short"):
        p = prompts.build_story_prompt("x", style, "16:9", "none", rng=random.Random(4)).lower()
        assert "only facts" in p and "invent" in p


def test_news_facts_are_quoted_and_bound():
    news = [{"title": "Studio confirms sequel", "snippet": "The studio confirmed a sequel on Monday.",
             "source": "Variety", "published": "Mon, 02 Nov 2026"}]
    p = prompts.build_story_prompt("new movie", "hollywood_hype", "9:16", "none", news=news, rng=random.Random(5))
    assert "Studio confirms sequel" in p and "Variety" in p
    assert "only these" in p.lower()


def test_bollywood_is_hindi():
    p = prompts.build_story_prompt("x", "bollywood_masala", "9:16", "vlog", rng=random.Random(6))
    assert "HINDI" in p and "Devanagari" in p


def test_word_targets():
    assert prompts.word_target("9:16") == (130, 160)
    assert prompts.word_target("16:9") == (500, 650)
