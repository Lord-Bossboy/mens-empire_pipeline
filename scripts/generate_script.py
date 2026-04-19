#!/usr/bin/env python3
"""
scripts/generate_script.py
DireWealth — AI Script Generator
Calls Google Gemini 2.5 Flash API to generate a full video script,
title, description, tags, and topic. Saves result as JSON for other steps.

Usage:
  python scripts/generate_script.py --type short --output /tmp/script_data.json
  python scripts/generate_script.py --type long  --output /tmp/script_data.json
"""

import argparse, json, os, sys, datetime, requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# Channel Identity
CHANNEL_NAME = "DireWealth"

CHANNEL_PERSONALITY = (
    "You are the voice of DireWealth. "
    "You speak like a calm, deeply confident, wealthy wolf — "
    "a man who has mastered money, physique, and power through discipline. "
    "Your tone is slow, deep, authoritative, and motivating. "
    "You never use slang, hype, or filler words. "
    "Every sentence carries weight, like a billionaire giving rare advice to young men. "
    "You speak directly to men aged 20-40 who want to level up their wealth, body, and style. "
    "You are not a hype man. You are a mentor. Calm. Powerful. Precise."
)

# Rotating topic schedule
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

Channel Voice & Personality:
{personality}

Write a 45-second voiceover script (90-110 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation, no extra text:
{{
  "title": "A powerful viral title under 58 chars. No hashtags. Sounds like a wealthy mentor speaking.",
  "script": "Full voiceover text only. No stage directions. No brackets. No sound effects. Start with one powerful statement that stops a man mid-scroll. End with: Follow DireWealth. Your future self will thank you.",
  "description": "180-word SEO-rich description written in DireWealth voice. Include timestamps: [0:00 Opening] [0:15 The Truth] [0:40 Final Word]. End with: #DireWealth #WealthMindset #MensLifestyle #SelfImprovement #Finance",
  "tags": "DireWealth,wealth mindset,mens lifestyle,self improvement,{category},men motivation,financial freedom,mens success",
  "search_topic": "2-4 word Pexels footage search, e.g. luxury office man or suit businessman city",
  "thumbnail_text": "5 words max ALL CAPS. Powerful and curiosity-driven."
}}

Rules:
- Calm, deep, authoritative tone throughout
- No filler words, no hype, no exclamation marks
- Every sentence must be worth the listener's time
- Write as if a billionaire mentor is speaking directly to a young man"""

LONG_PROMPT = """You are the scriptwriter for DireWealth, a men's wealth and self-improvement YouTube channel.

Channel Voice & Personality:
{personality}

Write a full 8-10 minute video script (1100-1300 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation, no extra text:
{{
  "title": "A compelling powerful title under 58 chars. Sounds authoritative and premium.",
  "script": "Full voiceover script 1100-1300 words. Open with a hook in the first 20 seconds that makes a man stop everything. Present 5 powerful insights with depth and clarity. Close with a strong CTA: If this gave you clarity, subscribe to DireWealth. More is coming.",
  "description": "320-word SEO description in DireWealth voice. Include chapter timestamps: [0:00 The Opening] [1:30 Insight One] [3:00 Insight Two] [5:00 Insight Three] [6:30 Insight Four] [8:00 The Close]. End with: #DireWealth #WealthMindset #MensLifestyle #SelfImprovement #Finance #MensSuccess",
  "tags": "DireWealth,wealth mindset,mens lifestyle,self improvement,{category},men motivation,financial freedom,mens success,mens health",
  "search_topic": "3-5 word Pexels footage search for background visuals",
  "thumbnail_text": "5 words max ALL CAPS. Premium and powerful."
}}

Rules:
- Calm, deep, authoritative tone — like a wealthy wolf mentoring young men
- No filler, no hype, no weak words
- Every insight must be specific and actionable
- Pacing should feel deliberate and weighty"""


def call_gemini(prompt: str) -> dict:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 4500,
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

    return json.loads(raw.strip().split("```")[0].strip())


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
        print(f"[DIREWEALTH] Generating SHORT | Category: {t['category']}")
        print(f"[DIREWEALTH] Topic: {t['topic']}")
    else:
        week_idx = today.isocalendar()[1] % len(LONG_VIDEO_TOPICS)
        t = LONG_VIDEO_TOPICS[week_idx]
        prompt = LONG_PROMPT.format(
            topic=t["topic"],
            category=t["category"],
            personality=CHANNEL_PERSONALITY
        )
        print(f"[DIREWEALTH] Generating LONG VIDEO | Category: {t['category']}")
        print(f"[DIREWEALTH] Topic: {t['topic']}")

    result = call_gemini(prompt)

    result["video_type"]   = args.type
    result["category"]     = t["category"]
    result["channel"]      = CHANNEL_NAME
    result["generated_at"] = today.isoformat()

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[DIREWEALTH] Script saved → {args.output}")
    print(f"[DIREWEALTH] Title: {result.get('title', 'N/A')}")
    print(f"[DIREWEALTH] Words: {len(result.get('script','').split())}")


if __name__ == "__main__":
    main()