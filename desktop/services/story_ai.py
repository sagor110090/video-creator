"""AI writing: stories, topics, YouTube metadata, news, image prompts and scene splitting.
Ported from app/Services/AiStoryService.php and ProcessStoryJob::parseStory (prompts kept verbatim)."""
import json
import random
import re
from datetime import date

import requests

PROVIDERS = {
    "deepseek": ("https://api.deepseek.com/chat/completions", "deepseek-chat", "deepseek_api_key"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile", "groq_api_key"),
}

STYLES = {"story": "General Story", "science_short": "60s Lab (Science)", "hollywood_hype": "Hollywood",
          "bollywood_masala": "Bollywood (Hindi)", "trade_wave": "TradeWave (Finance)"}
TALKING_STYLES = {"none": "None", "opinion": "Opinion", "storytime": "Storytime", "educational": "Educational",
                  "reaction": "Reaction", "vlog": "Vlog"}

# Appended (not prepended) so Openverse's word-narrowing keeps the scene subject.
STYLE_HINTS = {"science_short": "science technology", "hollywood_hype": "news celebrity",
               "bollywood_masala": "indian cinema bollywood colorful", "trade_wave": "finance business"}


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
TOPIC_FALLBACKS = {"science_short": "Black Holes", "hollywood_hype": "Celebrity News",
                   "bollywood_masala": "SRK New Movie", "trade_wave": "Bitcoin Update", "story": "The Hidden Library"}


def generate_topic(cfg, context: str, style: str = "story") -> str:
    prompt = TOPIC_PROMPTS.get(style, TOPIC_PROMPTS["story"]).format(d=date.today()) + f"\n\nChannel Context: {context}"
    try:
        return chat(cfg, "You are a content researcher. Output ONLY the topic name.", prompt,
                    0.7, json_mode=False, timeout=60).strip().strip('"').strip()
    except StoryAIError:
        return TOPIC_FALLBACKS.get(style, "Interesting Story")


# ---------------------------------------------------------------- story

PERSPECTIVES = [
    "Focus on the hidden secrets and unknown facts that most people miss.",
    "Analyze the future implications and what this means for the next generation.",
    "Tell it from the perspective of an expert insider with behind-the-scenes knowledge.",
    "Make it slightly controversial and challenge the popular mainstream opinion.",
    "Focus on the emotional human impact and personal stories related to this.",
    "Break it down for a complete beginner using simple but powerful analogies.",
]


def _style_prompts(duration, words, perspective):
    return {
        "science_short": ("60s Lab", f"""Write a fast-paced, mind-blowing science script for a {duration}. {perspective}
- Word count: {words} words.
- Start with a hook that challenges common knowledge.
- Use 'Did you know...' or 'Imagine if...'
- Explain complex concepts using simple, punchy analogies.
- End with a thought-provoking question about the future.""",
                          "Hook -> The Mystery -> The Science -> The 'Wow' Factor -> Future Question"),
        "hollywood_hype": ("Hollywood", f"""Write a high-energy, 'spilling the tea' celebrity news script for a {duration}. {perspective}
- Word count: {words} words.
- Start with 'Okay, we NEED to talk about...' or 'Y'all, did you see this?'
- Use internet slang naturally (tea, shook, living for it, iconic).
- Make it feel like a FaceTime call with a best friend.
- Focus on specific details, fan reactions, and rumors.
- End with 'What do you guys think? Let me know in the comments!'""",
                           "Breaking News -> The Juicy Details -> Fan Reactions -> Your Hot Take -> Engagement"),
        "bollywood_masala": ("Bollywood", f"""Write a high-energy, 'masala' Bollywood news script for a {duration} in PURE HINDI (Devanagari Script). {perspective}
- LANGUAGE: HINDI (Written in Devanagari script: 'नमस्ते, आज हम बात करेंगे...').
- Word count: {words} words.
- Start with 'अरे सुनो! तुम्हें पता है क्या हुआ?' or 'भाई, यह क्या हो गया!'
- Use Bollywood slang naturally (धमाल, ब्लॉकबस्टर, सीन, बवाल).
- Make it feel like a chat with a filmy friend.
- Focus on specific details, box office numbers, and spicy rumors.
- End with 'तुम्हारा क्या ख्याल है? कमेंट्स में बताओ!'""",
                             "Breaking News (Dhamaka) -> The Juicy Details (Masala) -> Fan Reactions (Public Ka Mood) -> Your Hot Take -> Engagement"),
        "trade_wave": ("TradeWave", f"""Write a sharp, professional yet accessible market analysis script for a {duration}. {perspective}
- Word count: {words} words.
- Start with 'The markets are moving, and here's why...'
- Use trader terminology (bullish, resistance, liquidity, breakout) but explain it simply.
- Provide actionable insights or things to watch.
- Mention specific tickers or coins if relevant.
- End with a disclaimer and a call to watch the charts.""",
                       "Market State -> Key Data/Chart Pattern -> Why it Matters -> What to Watch -> Disclaimer"),
        "story": ("General Story", f"""Write a compelling, immersive narrative script for a {duration}. {perspective}
- Word count: {words} words.
- Start in the middle of the action.
- Use vivid sensory details (smell, sound, feeling).
- Build tension and have a clear emotional payoff.
- Use natural, conversational storytelling like you're around a campfire.
- End with a thought-provoking resolution.""",
                  "The Hook -> Building Tension -> The Climax -> The Twist/Reveal -> Resolution"),
    }


TALKING_PATTERNS = {
    "vlog": ("MANDATORY FIRST WORDS: 'Okay, we NEED to talk about...' (exactly these words, no variations). Example: 'Okay, we NEED to talk about Taylor Swift's new album.'",
             "Hook announcement → Shock/reaction → Behind-the-scenes research → Fan/audience perspective → Personal opinion → Call to action",
             "Casual, conversational, energetic. Use phrases like: 'I'm shook', 'wait, hold on', 'the tea is hot', 'living for this', 'trust me on this', 'the crazy part is'. Make it feel like you FaceTiming a best friend."),
    "reaction": ("MANDATORY FIRST WORDS: Either 'WAIT. Hold on a second.' OR 'Okay, stop everything.' followed immediately by 'Did you see this?!'. Example: 'WAIT. Hold on a second. Did you see this?!'",
                 "Immediate shock → What happened → First thoughts → Emotional reaction → Breaking down the details → Final reaction",
                 "High energy, shocked, authentic. Use: 'no way no way no way', 'I literally can't', 'this is insane', 'I'm screaming', 'you won't believe this'. React as if seeing it for the first time right now."),
    "storytime": ("MANDATORY FIRST WORDS: Either 'Okay so storytime...' OR 'So this actually happened...' (exactly these phrases). Example: 'Okay so storytime... I was at the concert when...'",
                  "Setting the scene → The event → The drama/twist → What happened next → The resolution → Lesson/takeaway",
                  "Narrative, detailed, engaging. Use: 'let me tell you exactly what went down', 'and get this', 'the craziest part', 'so you're not gonna believe'. Tell it like a real story with dialogue and sensory details."),
    "opinion": ("MANDATORY FIRST WORDS: Either 'Okay, I need to say something about...' OR 'Here's my take on...' (exactly these phrases). Example: 'Okay, I need to say something about this new movie.'",
                "Bold opinion → Your reasoning → Addressing counterarguments → Why you're right → Strong closing stance",
                "Confident, unapologetic, strong stance. Use: 'honestly', 'I don't care who gets offended', 'here's the thing', 'people might say', 'but let me explain'. Make it a hot take, not neutral."),
    "educational": ("MANDATORY FIRST WORDS: Either 'Alright, so you've probably heard about...' OR 'Let me break this down for you...' (exactly these phrases). Example: 'Alright, so you've probably heard about Bitcoin ETFs.'",
                    "What people think → What's actually true → Simple explanation → Real-world example → Key takeaway",
                    "Clear, simple, teacher-like but casual. Use: 'think of it like', 'basically', 'the bottom line is', 'here's what you need to know', 'imagine if'. Break complex things into simple terms."),
}
BOLLYWOOD_PATTERNS = {
    "vlog": ("MANDATORY FIRST WORDS: 'अरे सुनो! तुम्हें पता है क्या हुआ?' (Use exactly this). Example: 'अरे सुनो! तुम्हें पता है क्या हुआ रणवीर के साथ?'",
             "Casual, conversational Hindi (Devanagari). Use phrases like: 'यार, मैं तो हिल गया', 'भाई, सीन सेट है', 'मतलब कुछ भी हो रहा है'. Make it feel like a filmy gossip session."),
    "reaction": ("MANDATORY FIRST WORDS: 'ओए होए! यह क्या देख लिया मैंने?!' OR 'रुको रुको! सच में?!'. Example: 'ओए होए! यह क्या देख लिया मैंने?!'",
                 "High energy, shocked, filmy drama. Use: 'भाई साहब!', 'उफ्फ, यह तो नेक्स्ट लेवल है', 'कसम से, मज़ा आ गया'. React like a true Bollywood fan."),
    "storytime": ("MANDATORY FIRST WORDS: 'सुनो, एक किस्सा सुनाता हूँ...' OR 'भाई, एक ज़बरदस्त बात बताता हूँ...'.",
                  "Narrative, masala style. Use: 'कहानी में ट्विस्ट तब आया जब...', 'और फिर जो हुआ...', 'तुम मानोगे नहीं'."),
    "opinion": ("MANDATORY FIRST WORDS: 'मेरी बात लिख के ले लो...' OR 'सच बोलूँ तो...'.",
                "Confident, dabangg style. Use: 'दुनिया कुछ भी बोले', 'अपना तो सीधा हिसाब है'."),
    "educational": ("MANDATORY FIRST WORDS: 'चलो, आज का ज्ञान लेते हैं...' OR 'इसका असली सच क्या है...'.",
                    "Simple, clear Hindi. Explain like you're talking to a friend at a chai tapri."),
}

STORY_SYSTEM = """You are an expert human content creator. You write scripts that sound exactly like a real person talking, not an AI.
Your writing is authentic, conversational, and completely avoids all AI tropes, clichés, and overused AI vocabulary.
You use natural speech patterns, contractions, and a relaxed, engaging tone.
You always output valid JSON."""

JSON_FORMAT = """Format your response as a JSON object:
{
  "title": "A short, punchy 3-5 word title",
  "content": "The full script text here...",
  "youtube_title": "A viral, click-worthy YouTube title",
  "youtube_description": "A description with a summary and hashtags",
  "youtube_tags": "15 relevant tags separated by commas"
}"""


def _common_rules(channel, words):
    return f"""
THE '70 RULE' FOR YPP APPROVAL (CRITICAL):
- UNIQUE ANGLE: Do not just state facts. Include a strong personal opinion, a witty joke, or a non-mainstream theory related to the topic.
- HUMAN PROOF: At least once in the script, include a 'Researcher's Insight' phrase like: "When I was researching this for {channel}, I was actually shocked to find..." or "I spent hours digging into this, and the thing that really got me was..." or "In my opinion, this is exactly why...". This proves a human did the research.
- PERSONALITY: Inject a distinct 'creator' personality. Use phrases like "Trust me on this," or "I know what you're thinking, but hear me out."

CRITICAL RULES FOR HUMAN-LIKE WRITING:
- TONE: 100% human-like. Use contractions (it's, can't, won't).
- VOCABULARY: Use simple, everyday words. Avoid complex AI-sounding words like 'delve', 'unleash', 'uncover', 'comprehensive', 'testament', 'vibrant', 'embark'.
- NO ROBOT TALK: NEVER use phrases like 'In this video', 'Welcome back', 'Let's dive in', 'Today we are going to', 'In conclusion', 'Furthermore', 'Moreover'.
- AUTHENTICITY: Write as if you're speaking to a friend. Use occasional filler words like 'so', 'actually', 'you see', 'the thing is'.
- VARIATION: Vary sentence length. Some short. Some a bit longer. Use fragments for emphasis.
- LENGTH: EXACTLY {words} words. Do not be shorter or longer.
- FORMAT: Conversational, rhythmic, and engaging."""


def build_story_prompt(topic, style="story", aspect_ratio="16:9", talking_style="none") -> str:
    shorts = aspect_ratio == "9:16"
    words = "140-160" if shorts else "500-600"
    duration = "60-second vertical Short" if shorts else "3-4 minute landscape video"
    styles = _style_prompts(duration, words, random.choice(PERSPECTIVES))
    channel, instruction, structure = styles.get(style, styles["story"])
    rules = _common_rules(channel, words)
    if not talking_style or talking_style == "none" or talking_style not in TALKING_PATTERNS:
        return f"""You are a master scriptwriter for YouTube. Write a script for a {duration} about: '{topic}'.

STYLE: {channel}
INSTRUCTIONS:
{instruction}

STRUCTURE:
{structure}
{rules}

Topic: {topic}

{JSON_FORMAT}"""
    opening, t_structure, tone = TALKING_PATTERNS[talking_style]
    language = ""
    if style == "bollywood_masala":
        opening, tone = BOLLYWOOD_PATTERNS[talking_style]
        language = "LANGUAGE: HINDI (Written in Devanagari script). Use authentic Bollywood slang (e.g., 'धमाल', 'बवाल')."
    return f"""You are a master scriptwriter for YouTube. Write a script for a {duration} about: '{topic}'.

TALKING STYLE: {talking_style.upper()} (THIS IS CRITICAL)
{language}

MANDATORY OPENING (MUST USE EXACTLY):
{opening}

STRUCTURE (STRICT - MUST FOLLOW):
{t_structure}

TONE INSTRUCTIONS:
{tone}

WORD COUNT: EXACTLY {words} words. No more, no less.

CRITICAL RULES:
1. The opening MUST match the talking style exactly. Do not use openings from other styles.
2. The entire script must follow the {talking_style} pattern - not the base {channel} style.
3. Each talking style has a unique personality - maintain it throughout.
4. Never mix talking styles (e.g., don't use vlog openings with reaction tone).
5. The opening is the most important - it MUST start with the exact phrase for {talking_style} style.

{rules}

Topic: {topic}

{JSON_FORMAT}"""


def generate_story(cfg, topic, style="story", aspect_ratio="16:9", talking_style="none") -> dict:
    data = _json(chat(cfg, STORY_SYSTEM, build_story_prompt(topic, style, aspect_ratio, talking_style), 0.85))
    title = data.get("title") or topic
    return {"title": title, "content": data.get("content", ""),
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
    if style == "trade_wave":
        context = "Focus on: stock market movements, crypto prices, economic news, trading opportunities, market analysis, financial reports."
    elif style == "bollywood_masala":
        context = "Focus on: Bollywood celebrity gossip, Hindi movie releases, box office numbers, Indian music industry, Mumbai film industry news, viral Indian pop culture."
    else:
        context = "Focus on: celebrity gossip, movie releases, box office news, TV shows, music industry, awards, Hollywood drama, entertainment viral moments."
    prompt = f"""Today is {date.today()}. Query: '{query}'.
{context}

Provide 5 trending news items. Each needs:
- 'title': Catchy headline
- 'snippet': 2-3 sentence summary with specific details

Return JSON: {{"news": [{{"title": "...", "snippet": "..."}}, ...]}}"""
    try:
        data = _json(chat(cfg, "You are a news API. Return ONLY valid JSON. No markdown.", prompt, 0.85,
                          timeout=45, max_tokens=1500))
    except StoryAIError:
        return []
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict) and "title" in d][:5]
    for key in ("news", "results", "items", "data", "articles", "stories"):
        if isinstance(data.get(key), list):
            return data[key][:5]
    return [data] if "title" in data and "snippet" in data else []


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


def generate_image_prompts(cfg, narrations: list[str]) -> list[str]:
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
- Output specific keywords (e.g. 'Golden retriever running grass' instead of 'A dog running').

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


def split_scenes(content: str, style: str = "story", talking_style: str = "none", cfg=None,
                 max_scenes: int = 50) -> list[dict]:
    """Sentences (>= 10 chars) become scenes; image prompts come from the AI, with a cleaned-text fallback."""
    text = re.sub(r"[\r\n]+", " ", content)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", text) if len(s.strip()) >= 10][:max_scenes]
    prompts = generate_image_prompts(cfg, sentences) if cfg and sentences else [clean_image_prompt(s) for s in sentences]
    hint = STYLE_HINTS.get(style, "")
    if not hint and talking_style and talking_style != "none":
        hint = "person talking lifestyle"
    return [{"narration": s, "image_prompt": f"{p}, {hint}" if hint else p} for s, p in zip(sentences, prompts)]
