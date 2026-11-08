"""Script-writing prompts: content styles, talking styles, hooks and shared writing rules.

Design notes (from reviewing real output):
- No fake "I researched this" lines and no required catchphrases: they repeated in every video.
- Openings vary: each script gets a random hook type; talking-style openings are examples, never mandatory.
- Non-fiction styles must only state facts; news styles may only use the real headlines passed in.
- One idea per sentence, 8-20 words: every sentence becomes a scene, so this keeps scenes watchable.
"""
import random

STYLES = {
    "story": {
        "label": "General Story", "kind": "fiction",
        "voice": "an immersive storyteller telling a gripping story around a campfire",
        "rules": ["Start in the middle of the action.",
                  "Use vivid sensory details (sound, smell, texture) the viewer can picture.",
                  "Build tension toward one clear turning point and an emotional payoff."],
        "structure": "Hook -> Rising tension -> Turning point -> Twist or reveal -> Resolution",
    },
    "kids_story": {
        "label": "Kids Story", "kind": "kids",
        "voice": "a warm, cheerful storyteller reading a picture book to children",
        "rules": ["For children ages 4-8: use simple words and short, clear sentences.",
                  "Friendly characters (animals, kids, toys) with a small, gentle problem they solve.",
                  "Nothing scary, violent, sad-for-too-long or sarcastic. No brands, no grown-up jokes.",
                  "Repeat a fun phrase or sound once or twice so kids can join in.",
                  "End with a clear, kind lesson in one short sentence."],
        "structure": "Meet the hero -> A small problem -> Trying and failing -> A kind or clever idea -> Happy ending + lesson",
    },
    "history": {
        "label": "History & True Story", "kind": "nonfiction",
        "voice": "a documentary narrator who makes real history feel alive",
        "rules": ["Tell a real event or real person's story with dates and places.",
                  "Bring it to life with scene-setting, but every claim must be true."],
        "structure": "Hook moment -> Who and when -> What happened -> The surprising part -> Why it still matters",
    },
    "mystery": {
        "label": "Mystery & Horror", "kind": "fiction",
        "voice": "a calm narrator telling a chilling story late at night",
        "rules": ["Build suspense with atmosphere and small strange details, not gore.",
                  "Plant one clue early that pays off in the ending.",
                  "End with a twist or an unsettling question that lingers."],
        "structure": "Eerie hook -> Something is wrong -> It escalates -> The reveal -> Lingering twist",
    },
    "facts": {
        "label": "Facts & Top 5", "kind": "nonfiction",
        "voice": "an energetic host counting down mind-blowing facts",
        "rules": ["A countdown of 5 surprising, verifiable facts about the topic (5 to 1, best last).",
                  "Each fact: one line stating it, one line on why it's surprising."],
        "structure": "Hook -> Fact 5 -> Fact 4 -> Fact 3 -> Fact 2 -> Fact 1 (the best) -> Quick wrap-up",
    },
    "science_short": {
        "label": "60s Lab (Science)", "kind": "nonfiction",
        "voice": "a curious science explainer who loves 'wait, really?' moments",
        "rules": ["Challenge a common belief, then explain the real science with a simple analogy.",
                  "End with a thought-provoking question about the future."],
        "structure": "Hook -> The mystery -> The science -> The wow factor -> Future question",
    },
    "motivation": {
        "label": "Motivation", "kind": "nonfiction",
        "voice": "a grounded coach talking straight to one person",
        "rules": ["Speak to the viewer as 'you'. Use one concrete real-life example, not clichés.",
                  "Avoid empty hype words; make it practical.",
                  "End with one small action the viewer can take today."],
        "structure": "Hard truth -> Relatable struggle -> The shift in thinking -> Example -> One action today",
    },
    "hollywood_hype": {
        "label": "Hollywood", "kind": "news",
        "voice": "a fun entertainment reporter chatting with a friend",
        "rules": ["Casual and lively, with natural slang (tea, iconic, shook) used sparingly.",
                  "Focus on the specific details and fan reactions in the provided news."],
        "structure": "The news -> The juicy details -> How fans reacted -> A fair hot take -> Ask viewers' opinion",
    },
    "bollywood_masala": {
        "label": "Bollywood (Hindi)", "kind": "news", "language": "hindi",
        "voice": "a filmy friend sharing the latest Bollywood gossip",
        "rules": ["Natural Bollywood slang (धमाल, ब्लॉकबस्टर, सीन, बवाल), used sparingly.",
                  "Focus on the specific details in the provided news."],
        "structure": "धमाका (the news) -> मसाला (details) -> पब्लिक का मूड -> Your take -> Ask viewers",
    },
    "trade_wave": {
        "label": "TradeWave (Finance)", "kind": "news",
        "voice": "a sharp but friendly market analyst",
        "rules": ["Explain trader terms (bullish, resistance, liquidity) in plain words.",
                  "Say what to watch next; never promise profits or give personal financial advice.",
                  "End with a one-line 'not financial advice' disclaimer."],
        "structure": "Market state -> Key move -> Why it matters -> What to watch -> Disclaimer",
    },
}

TALKING_STYLES = {
    "none": {"label": "None"},
    "opinion": {"label": "Opinion", "tone": "Confident and honest with a clear stance, but fair to the other side.",
                "structure": "Bold take -> Reasons -> The best counter-argument -> Why you still think so -> Ask viewers",
                "openings": ["Unpopular opinion: ...", "Here's my honest take on ...", "Everyone's wrong about ..."]},
    "storytime": {"label": "Storytime", "tone": "Personal and conversational, like telling a friend what happened.",
                  "structure": "Set the scene -> What happened -> The twist -> What happened next -> Takeaway",
                  "openings": ["So this actually happened ...", "I still can't believe ...", "It started with ..."]},
    "educational": {"label": "Educational", "tone": "Clear and friendly, like a great teacher; simple analogies.",
                    "structure": "What people think -> What's true -> Simple explanation -> Example -> Takeaway",
                    "openings": ["Most people get this wrong: ...", "Here's how ... actually works.",
                                 "You've probably heard of ..."]},
    "reaction": {"label": "Reaction", "tone": "Genuine surprise and energy, reacting as if seeing it right now.",
                 "structure": "Instant reaction -> What happened -> Breaking down details -> Final reaction",
                 "openings": ["Wait. Did that really just happen?", "No way. Look at this.", "I had to watch this twice."]},
    "vlog": {"label": "Vlog", "tone": "Casual and energetic, like a FaceTime call with a best friend.",
             "structure": "Hook -> Reaction -> Behind the scenes -> What people are saying -> Your opinion -> Ask viewers",
             "openings": ["Okay, we need to talk about ...", "You guys, ...", "So I just found out ..."]},
}

HOOKS = [
    "a surprising fact stated in under 12 words",
    "a question the viewer can't answer yet",
    "dropping the viewer into the middle of the action",
    "a bold claim that sounds impossible but is true to the story",
    "one vivid sensory moment (a sound, a smell, a texture)",
    "a 'what if' that makes the viewer imagine something",
    "the ending first, then 'here's how we got here'",
    "a tiny mystery: something that should not be there",
]

AVOID = ["Trust me on this", "I know what you're thinking", "hear me out", "Here's the thing", "Picture this",
         "Imagine this", "Buckle up", "In this video", "Welcome back", "Let's dive in", "In conclusion",
         "Furthermore", "Moreover", "delve", "unleash", "testament", "embark", "tapestry", "vibrant",
         "When I was researching", "I spent hours"]

STORY_SYSTEM = """You are a professional YouTube scriptwriter. Your scripts sound like a real person talking:
natural, specific and fresh, never generic or robotic. Every script is different from the last one.
You always output valid JSON."""

JSON_FORMAT = """Format your response as a JSON object:
{
  "title": "A short, punchy 3-6 word title",
  "content": "The full narration script as plain sentences (no headings, no stage directions, no emojis)",
  "youtube_title": "A click-worthy but honest YouTube title",
  "youtube_description": "2-3 sentence summary plus 3-5 relevant hashtags",
  "youtube_tags": "15 relevant tags separated by commas"
}"""


def word_target(aspect_ratio: str) -> tuple[int, int]:
    return (130, 160) if aspect_ratio == "9:16" else (500, 650)


def pick_hook(rng=random) -> str:
    return rng.choice(HOOKS)


def _bullets(items) -> str:
    return "\n".join(f"- {x}" for x in items)


def build_story_prompt(topic, style="story", aspect_ratio="16:9", talking_style="none", channel_name="",
                       news=None, news_story=None, rng=random) -> str:
    spec = STYLES.get(style, STYLES["story"])
    talk = TALKING_STYLES.get(talking_style or "none", TALKING_STYLES["none"])
    lo, hi = word_target(aspect_ratio)
    shorts = aspect_ratio == "9:16"
    fmt = "a vertical YouTube Short (about 50-60 seconds)" if shorts else "a landscape YouTube video (about 3-4 minutes)"
    kind = spec["kind"]

    voice, structure = spec["voice"], spec["structure"]
    talk_block = ""
    if talk.get("tone"):
        voice += f", in a {talk['label'].lower()} style"
        structure = talk["structure"]
        talk_block = (f"\nTALKING STYLE: {talk['label']}. {talk['tone']}\n"
                      f"Openings in this spirit (for inspiration only; write your own, never copy these): "
                      f"{' / '.join(talk['openings'])}\n")

    rules = list(spec["rules"])
    if kind == "nonfiction":
        rules.append("Accuracy: include only facts you are confident are true. Do not invent names, dates, "
                     "numbers or quotes; if unsure, leave it out.")
    if kind == "news":
        rules.append("Use only these provided news facts for any claim about real people or events. Do not invent "
                     "details, quotes or numbers. Attribute claims ('according to Variety...'). "
                     "If no news is provided, talk about the topic in general terms without specific claims.")
    if kind != "kids" and channel_name:
        rules.append(f"You may mention the channel name \"{channel_name}\" once, naturally, near the end. "
                     "Never claim you personally researched, saw or experienced anything.")
    elif kind != "kids":
        rules.append("Never claim you personally researched, saw or experienced anything.")

    language = ""
    if spec.get("language") == "hindi":
        language = "\nLANGUAGE: write the whole script in HINDI, in Devanagari script.\n"

    news_block = ""
    if news_story:      # the user picked this story; its context beats auto-fetched headlines
        line = f"- {news_story['title']} ({news_story.get('source') or 'news'}, " \
               f"{news_story.get('published') or 'recent'})"
        if news_story.get("text"):
            line += f": {news_story['text']}"
        news_block = "\nREAL NEWS (use only these facts):\n" + line + "\n"
    elif kind == "news" and news:
        lines = [f"- {n['title']} ({n.get('source') or 'news'}, {n.get('published') or 'recent'}): "
                 f"{n.get('snippet') or ''}".strip() for n in news[:5]]
        news_block = "\nREAL NEWS (use only these facts):\n" + "\n".join(lines) + "\n"

    ending = ("End warmly with the lesson." if kind == "kids" else
              "End with a line that loops back to the first sentence, so the Short replays smoothly."
              if shorts else "End with a satisfying payoff and one question for the comments.")

    return f"""Write a script for {fmt} about: "{topic}".

STYLE: {spec['label']}. Narrated by {voice}.
{language}{talk_block}{news_block}
RULES:
{_bullets(rules)}

STRUCTURE: {structure}

OPENING: the first sentence is a hook built on {pick_hook(rng)}. Max 12 words. No greeting, no channel intro.

WRITING:
- One idea per sentence, mostly 8-20 words. Each sentence becomes its own on-screen scene, so make each one
  something the viewer can picture.
- Natural spoken English with contractions; vary rhythm; occasional short punchy line.
- AVOID these overused phrases and words completely: {', '.join(AVOID)}.
- Length: {lo}-{hi} words.
- {ending}

{JSON_FORMAT}"""
