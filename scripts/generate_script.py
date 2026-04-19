#!/usr/bin/env python3
import argparse, json, os, datetime, requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

CHANNEL_NAME = "DireWealth"

CHANNEL_PERSONALITY = (
    "You are the voice of DireWealth. "
    "You speak like a calm, deeply confident, wealthy wolf — "
    "a man who has mastered money, physique, and power through discipline. "
    "Your tone is slow, deep, authoritative, and motivating. "
    "You never use slang, hype, or filler words. "
    "Every sentence carries weight, like a billionaire giving rare advice to young men. "
    "You are not a hype man. You are a mentor. Calm. Powerful. Precise."
)

DAILY_TOPICS = {
    0: {"category": "fashion",  "topic": "how to dress like a wealthy powerful man on any budget"},
    1: {"category": "physique", "topic": "the disciplined workout routine of high achieving men"},
    2: {"category": "diet",     "topic": "what successful men eat to stay lean and sharp all day"},
    3: {"category": "finance",  "topic": "how to grow your money silently while others sleep"},
    4: {"category": "fashion",  "topic": "style secrets that make powerful men unforgettable"},
    5: {"category": "physique", "topic": "morning habits that separate wealthy men from the rest"},
    6: {"category": "finance",  "topic": "building passive income streams that work while you rest"},
}

LONG_VIDEO_TOPICS = [
    {"category": "finance",  "topic": "the complete wealth building blueprint for men starting from zero"},
    {"category": "physique", "topic": "the elite body transformation guide for disciplined men"},
    {"category": "fashion",  "topic": "the powerful man's complete style guide to commanding respect"},
    {"category": "diet",     "topic": "the high performance nutrition guide for men who want it all"},
]

SHORT_PROMPT = """You are the scriptwriter for DireWealth, a men's wealth and self-improvement YouTube channel.

Channel Voice:
{personality}

Write a 45-second voiceover script (90-110 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "title": "Powerful viral title under 58 chars. No hashtags. Sounds like a wealthy mentor.",
  "script": "Full voiceover only. No stage directions. No brackets. Start with one powerful statement that stops a man mid-scroll. End with: Follow DireWealth. Your future self will thank you.",
  "description": "180-word SEO description in DireWealth voice. Timestamps: [0:00 Opening] [0:15 The Truth] [0:40 Final Word]. End with: #DireWealth #WealthMindset #MensLifestyle #SelfImprovement #Finance",
  "tags": "DireWealth,wealth mindset,mens lifestyle,self improvement,{category},men motivation,financial freedom",
  "search_topic": "2-4 word Pexels footage search e.g. luxury businessman suit city",
  "thumbnail_text": "5 words max ALL CAPS powerful and curiosity-driven"
}}

Rules: Calm deep authoritative tone. No filler. No hype. No exclamation marks. Pure value."""

LONG_PROMPT = """You are the scriptwriter for DireWealth, a men's wealth and self-improvement YouTube channel.

Channel Voice:
{personality}

Write a full 8-10 minute video script (1100-1300 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "title": "Compelling powerful title under 58 chars. Authoritative and premium.",
  "script": "Full voiceover 1100-1300 words. Hook in first 20 seconds. 5 powerful insights. Close with: Subscribe to DireWealth. More is coming.",
  "description": "320-word SEO description. Timestamps: [0:00 Opening] [1:30 Insight One] [3:00 Insight Two] [5:00 Insight Three] [6:30 Insight Four] [8:00 The Close]. End with: #DireWealth #WealthMindset #MensLifestyle #SelfImprovement #Finance",
  "tags": "DireWealth,wealth mindset,mens lifestyle,self improvement,{category},men motivation,financial freedom,mens success",
  "search_topic": "3-5 word Pexels footage search for background visuals",
  "thumbnail_text": "5 words max ALL CAPS premium and powerful"
}}

Rules: Calm deep authoritative tone. Like a wealthy wolf mentoring young men. No weak words."""


def call_gemini(prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 12000,
            "responseMimeType": "application/json",
        },
    }
    resp = requests.post(GEMINI_URL, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip().split("```")[0].strip())
    except json.JSONDecodeError:
        # Try to salvage truncated JSON by finding last complete field
        raw = raw.strip()
        if not raw.endswith("}"):
            raw = raw[:raw.rfind('"')]
            raw = raw[:raw.rfind('"')]
            raw += '"}'
        return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type",   choices=["short", "long"], required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    today = datetime.datetime.utcnow()
    weekday = today.weekday()

    if args.type == "short":
        t = DAILY_TOPICS[weekday]
        prompt = SHORT_PROMPT.format(
            topic=t["topic"],
            category=t["category"],
            personality=CHANNEL_PERSONALITY
        )
        print(f"[DIREWEALTH] SHORT | {t['category']} | {t['topic']}")
    else:
        week_idx = today.isocalendar()[1] % len(LONG_VIDEO_TOPICS)
        t = LONG_VIDEO_TOPICS[week_idx]
        prompt = LONG_PROMPT.format(
            topic=t["topic"],
            category=t["category"],
            personality=CHANNEL_PERSONALITY
        )
        print(f"[DIREWEALTH] LONG | {t['category']} | {t['topic']}")

    result = call_gemini(prompt)
    result["video_type"]   = args.type
    result["category"]     = t["category"]
    result["channel"]      = CHANNEL_NAME
    result["generated_at"] = today.isoformat()

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[DIREWEALTH] Saved → {args.output}")
    print(f"[DIREWEALTH] Title: {result.get('title', 'N/A')}")
    print(f"[DIREWEALTH] Words: {len(result.get('script','').split())}")


if __name__ == "__main__":
    main()