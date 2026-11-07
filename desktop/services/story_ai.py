"""AI writing: stories, topics, YouTube metadata, image prompts and scene splitting.
Story prompts live in prompts.py; real news comes from news.py (Google News RSS)."""
import json
import random
import re
from datetime import date

import requests

PROVIDERS = {
    "deepseek": ("https://api.deepseek.com/chat/completions", "deepseek-chat", "deepseek_api_key"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile", "groq_api_key"),
}

from desktop.services import news, prompts

STYLES = {k: v["label"] for k, v in prompts.STYLES.items()}
TALKING_STYLES = {k: v["label"] for k, v in prompts.TALKING_STYLES.items()}

# Appended (not prepended) so Openverse's word-narrowing keeps the scene subject.
STYLE_HINTS = {"science_short": "science technology", "hollywood_hype": "news celebrity",
               "bollywood_masala": "indian cinema bollywood colorful", "trade_wave": "finance business",
               "history": "historical", "mystery": "dark mysterious", "motivation": "inspiring"}


class StoryAIError(RuntimeError):
    pass


def chat(cfg, system, user, temperature=0.7, json_mode=True, timeout=120, max_tokens=None) -> str:
    provider = cfg.get("ai_provider", "deepseek")
    url, model, key_name = PROVIDERS.get(provider, PROVIDERS["deepseek"])
    key = cfg.get(key_name)
    if not key:
        raise StoryAIError(f"No API key for {provider}. Add it in Settings.")
    payload = {"model": model, "temperature": temperature,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    try:
        res = requests.post(url, json=payload, timeout=timeout, headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise StoryAIError(f"{provider} request failed: {e}") from e
    if res.status_code != 200:
        raise StoryAIError(f"{provider} error {res.status_code}: {res.text[:300]}")
    try:
        return res.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise StoryAIError(f"unexpected {provider} response: {res.text[:300]}") from e


def _json(text: str):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except ValueError as e:
        raise StoryAIError(f"AI returned invalid JSON: {text[:200]}") from e


# ---------------------------------------------------------------- topic

TOPIC_PROMPTS = {
    "science_short": """Generate ONE specific, high-interest science or technology topic. Today's date is {d}.
- Focus on: Astrophysics, Quantum Physics, Deep Sea, AI, or Future Tech.
- Examples: 'The James Webb Space Telescope', 'Quantum Entanglement', 'Mariana Trench Secrets'.
- Return ONLY the topic name (2-5 words). No punctuation.""",
    "hollywood_hype": """Generate ONE trending Hollywood or Celebrity topic. Today's date is {d}.
- Focus on: A-list stars, major movie releases, or viral pop culture moments happening RIGHT NOW.
- Examples: 'Dakota Johnson Movie Rumors', 'Oscars Best Picture Controversy', 'Celebrity Fashion Trends'.
- Ensure the topic is fresh and highly relevant to the current week.
- Return ONLY the topic name (2-5 words). No punctuation.""",
    "bollywood_masala": """Generate ONE trending Bollywood or Indian Celebrity topic. Today's date is {d}.
- Focus on: Top stars (SRK, Salman, Deepika, Alia), major movie releases, or viral Indian pop culture moments.
- Examples: 'Pathaan Box Office Records', 'Alia Bhatt New Movie', 'Virat Kohli News'.
- Ensure the topic is fresh and highly relevant.
- Return ONLY the topic name (2-5 words). No punctuation.""",
    "trade_wave": """Generate ONE high-impact Trading or Finance topic. Today's date is {d}.
- Focus on: Bitcoin/Crypto, S&P 500, Tech Stocks, or Global Economy.
- Examples: 'Bitcoin Spot ETF Impact', 'AI Stock Market Rally', 'Interest Rate Decisions'.
- Focus on current market sentiment and breaking financial news.
- Return ONLY the topic name (2-5 words). No punctuation.""",
    "story": """Generate ONE intriguing story concept.
- Focus on: Mystery, Adventure, Sci-Fi, or Historical Secret.
- Examples: 'The Lost City of Z', 'Time Travel Paradox', 'The Whispering Woods'.
- Return ONLY the topic name (2-5 words). No punctuation.""",
}
TOPIC_PROMPTS.update({
    "kids_story": """Generate ONE gentle, fun story idea for children ages 4-8.
- A friendly character (animal, kid, toy) with a small problem to solve.
- Examples: 'The Bunny Who Lost Her Hop', 'Milo and the Moon Lantern', 'The Kindest Little Cloud'.
- Return ONLY the title (2-6 words). No punctuation.""",
    "history": """Generate ONE fascinating, real and verifiable history topic (a person, event or discovery).
- Examples: 'The Man Who Sold the Eiffel Tower', 'The Great Molasses Flood', 'The Night London Went Dark'.
- Return ONLY the topic (2-7 words). No punctuation.""",
    "mystery": """Generate ONE eerie mystery or spooky story idea (suspense, not gore).
- Examples: 'The Lighthouse That Kept Ringing', 'The Room With No Door', 'The Last Train Passenger'.
- Return ONLY the title (2-6 words). No punctuation.""",
    "facts": """Generate ONE topic that works as a 'Top 5 surprising facts' video.
- Examples: 'Octopus Intelligence', 'The Human Heart', 'Ancient Egypt Daily Life'.
- Return ONLY the topic (2-5 words). No punctuation.""",
    "motivation": """Generate ONE practical motivation topic for a short video.
- Examples: 'Starting Before You Feel Ready', 'Why Small Wins Matter', 'Beating Phone Addiction'.
- Return ONLY the topic (2-6 words). No punctuation.""",
})
TOPIC_FALLBACKS = {"kids_story": "The Brave Little Turtle", "history": "The Great Molasses Flood",
                   "mystery": "The Room With No Door", "facts": "Octopus Intelligence",
                   "motivation": "Why Small Wins Matter","science_short": "Black Holes", "hollywood_hype": "Celebrity News",
                   "bollywood_masala": "SRK New Movie", "trade_wave": "Bitcoin Update", "story": "The Hidden Library"}


def generate_topic(cfg, context: str, style: str = "story") -> str:
    prompt = TOPIC_PROMPTS.get(style, TOPIC_PROMPTS["story"]).format(d=date.today()) + f"\n\nChannel Context: {context}"
    try:
        return chat(cfg, "You are a content researcher. Output ONLY the topic name.", prompt,
                    0.7, json_mode=False, timeout=60).strip().strip('"').strip()
    except StoryAIError:
        return TOPIC_FALLBACKS.get(style, "Interesting Story")


# ---------------------------------------------------------------- story

def build_story_prompt(topic, style="story", aspect_ratio="16:9", talking_style="none", channel_name="",
                       news_items=None, rng=random) -> str:
    return prompts.build_story_prompt(topic, style, aspect_ratio, talking_style, channel_name=channel_name,
                                      news=news_items, rng=rng)


def _expand(cfg, content, style, aspect_ratio) -> str:
    """One retry when a script comes back well under the target length."""
    lo, hi = prompts.word_target(aspect_ratio)
    label = prompts.STYLES.get(style, prompts.STYLES["story"])["label"]
    user = (f"This {label} script is only {len(content.split())} words. Rewrite it to {lo}-{hi} words: keep the "
            "same story, voice, facts and opening line; add vivid detail rather than filler; one idea per sentence. "
            f'Return JSON: {{"content": "..."}}\n\nSCRIPT:\n{content}')
    try:
        longer = _json(chat(cfg, prompts.STORY_SYSTEM, user, 0.7)).get("content", "")
    except StoryAIError:
        return content
    return longer if len(longer.split()) > len(content.split()) else content


def generate_story(cfg, topic, style="story", aspect_ratio="16:9", talking_style="none", news_items=None) -> dict:
    spec = prompts.STYLES.get(style, prompts.STYLES["story"])
    if spec["kind"] == "news" and news_items is None:
        news_items = news.headlines(topic, style)        # real headlines; [] if offline
    prompt = build_story_prompt(topic, style, aspect_ratio, talking_style,
                                channel_name=(cfg.get("channel_name") or "").strip(), news_items=news_items)
    data = _json(chat(cfg, prompts.STORY_SYSTEM, prompt, 0.9))
    content = (data.get("content") or "").strip()
    lo, _hi = prompts.word_target(aspect_ratio)
    if content and len(content.split()) < lo * 0.75:
        content = _expand(cfg, content, style, aspect_ratio)
    title = data.get("title") or topic
    return {"title": title, "content": content,
            "youtube_title": data.get("youtube_title") or title,
            "youtube_description": data.get("youtube_description", ""),
            "youtube_tags": data.get("youtube_tags", "")}


# ---------------------------------------------------------------- metadata / news

def generate_metadata(cfg, content: str) -> dict:
    prompt = f"""Generate viral YouTube metadata for the following video script.

SCRIPT:
{content}

IMPORTANT FOR MONETIZATION:
- Include a professional AI Disclosure in the description (e.g., 'This video features AI-enhanced narration and visuals to bring you a more immersive experience.').
- Ensure the title is click-worthy but not 'clickbait' that violates YouTube policies.

Format your response as a JSON object:
{{
  "youtube_title": "A viral, click-worthy YouTube title",
  "youtube_description": "A description with a summary, hashtags, and the required AI disclosure",
  "youtube_tags": "15 relevant tags separated by commas"
}}"""
    try:
        return _json(chat(cfg, "You are a YouTube SEO expert. Output ONLY valid JSON.", prompt, 0.7, timeout=60))
    except StoryAIError:
        return {"youtube_title": "Amazing Story", "youtube_description": "Check out this amazing AI-generated story!",
                "youtube_tags": "ai, story, animation"}


def search_news(cfg, query: str, style: str = "hollywood_hype") -> list[dict]:
    """Real, recent headlines (Google News). The AI is never asked to invent news."""
    return news.headlines(query, style)


# ---------------------------------------------------------------- scenes / image prompts

FILLERS = ["so here is my question", "so heres my question", "here is my question", "heres my question",
           "believe it or not", "it turns out", "as a result", "in the end", "picture this", "did you know",
           "think about", "imagine if", "what if", "in fact", "you see", "i mean", "imagine", "actually",
           "basically", "literally", "interestingly", "however", "moreover", "furthermore", "consequently",
           "if we", "so"]
_FILLER_RE = re.compile(r"\b(?:" + "|".join(re.escape(f) for f in FILLERS) + r")\b,?", re.IGNORECASE)


def clean_image_prompt(text: str) -> str:
    """Strip conversational filler so the text works as an image search (whole words only)."""
    clean = _FILLER_RE.sub("", text)
    clean = re.sub(r"\b(really|very|just|only|maybe|perhaps|probably)\b", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"[?!.,;:\"']", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean if len(clean) >= 5 else re.sub(r"[?!.,;:\"']", "", text).strip()


def generate_image_prompts(cfg, narrations: list[str], image_style: str = "auto") -> list[str]:
    from desktop.pipeline.images import IMAGE_STYLES
    style = IMAGE_STYLES.get(image_style, IMAGE_STYLES["auto"])
    style_rule = (f"\n- VISUAL STYLE: {style['label']}. {style['guidance']} Describe each scene so it fits this style."
                  if style.get("guidance") else "")
    out = []
    for start in range(0, len(narrations), 20):
        chunk = narrations[start:start + 20]
        prompt = f"""You are a visual director for a video production.
For each of the following narration segments, generate a precise, high-quality image search query.
- The query will be used to search for stock footage/photos (Pexels, Unsplash).
- Extract the main visual subject.
- Focus on nouns, setting, and action.
- REMOVE conversational filler (e.g. 'Imagine if', 'So', 'Basically').
- If the text is abstract, provide a metaphorical visual (e.g. 'Stock market crash' -> 'Red graph arrow going down').
- Output specific keywords (e.g. 'Golden retriever running grass' instead of 'A dog running').{style_rule}

INPUT NARRATIONS:
{json.dumps(chunk, ensure_ascii=False)}

Format your response as a JSON object where keys are the indices (0, 1, 2...) matching the input array order, and values are the search prompts.
Example:
{{
    "0": "futuristic city skyline night",
    "1": "scientist looking at microscope",
    "2": "bitcoin gold coin pile"
}}"""
        try:
            data = _json(chat(cfg, "You are an expert visual prompt engineer. Output ONLY valid JSON.", prompt, 0.7))
        except StoryAIError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        for i, text in enumerate(chunk):
            p = data.get(str(i)) or data.get(i)
            out.append(p.strip() if isinstance(p, str) and p.strip() else clean_image_prompt(text))
    return out


_QUOTE_PAIRS = {'"': '"', "“": "”", "‘": "’", "'": "'"}


def _sentences(text: str) -> list[str]:
    """Split into sentences, but never inside quoted speech ('Put. It. Down.' stays together)."""
    out, buf, closer, i = [], [], None, 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)
        prev = text[i - 1] if i else " "
        nxt = text[i + 1] if i + 1 < len(text) else " "
        if closer is None and ch in _QUOTE_PAIRS and (prev.isspace() or prev in "(:—-") and not nxt.isspace():
            closer = _QUOTE_PAIRS[ch]                      # opening quote (not an apostrophe)
        elif closer is not None and ch == closer and not nxt.isalnum():
            closer = None                                  # closing quote
            if buf[-2:-1] and buf[-2] in ".!?।" and nxt.isspace():
                out.append("".join(buf).strip())
                buf = []
        elif closer is None and ch in ".!?।" and nxt.isspace():
            out.append("".join(buf).strip())
            buf = []
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return [s for s in out if s]


def _merge_short(sentences: list[str], min_words: int = 6, max_words: int = 40) -> list[str]:
    """Tiny sentences ('I sped up.') become part of the next one so no scene is a 1-second flash."""
    scenes, carry = [], ""
    for s in sentences:
        cur = f"{carry} {s}".strip() if carry else s
        if len(cur.split()) < min_words:
            carry = cur
            continue
        scenes.append(cur)
        carry = ""
    if carry:
        if scenes and len(scenes[-1].split()) + len(carry.split()) <= max_words:
            scenes[-1] = f"{scenes[-1]} {carry}"
        else:
            scenes.append(carry)
    return scenes


def split_scenes(content: str, style: str = "story", talking_style: str = "none", cfg=None,
                 max_scenes: int = 50, image_style: str = "auto") -> list[dict]:
    """Sentences become scenes (short ones merged, quotes kept whole); image prompts come from the AI."""
    text = re.sub(r"\s+", " ", content).strip()
    sentences = _merge_short([s for s in _sentences(text) if len(s) >= 2])[:max_scenes]
    prompts_ = (generate_image_prompts(cfg, sentences, image_style) if cfg and sentences
                else [clean_image_prompt(s) for s in sentences])
    hint = STYLE_HINTS.get(style, "") if image_style in (None, "auto") else ""
    return [{"narration": s, "image_prompt": f"{p}, {hint}" if hint else p} for s, p in zip(sentences, prompts_)]
