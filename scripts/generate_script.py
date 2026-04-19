#!/usr/bin/env python3
"""
scripts/generate_script.py
Calls Google Gemini 2.0 Flash API to generate a full video script,
title, description, tags, and topic. Saves result as JSON for other steps.

Usage:
  python scripts/generate_script.py --type short --output /tmp/script_data.json
  python scripts/generate_script.py --type long  --output /tmp/script_data.json
"""

import argparse, json, os, sys, datetime, requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)

# ── Rotating topic schedule ────────────────────────────────────────────────
# weekday() → 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
DAILY_TOPICS = {
    0: {"category": "fashion",  "topic": "men outfit tips look expensive on a budget"},
    1: {"category": "physique", "topic": "best workout routine for men to build muscle fast"},
    2: {"category": "diet",     "topic": "high protein meal prep for men to lose fat"},
    3: {"category": "finance",  "topic": "investing and saving money tips for young men"},
    4: {"category": "fashion",  "topic": "men grooming and style upgrade secrets"},
    5: {"category": "physique", "topic": "morning routine discipline and fitness habits men"},
    6: {"category": "finance",  "topic": "side hustle and passive income ideas for men"},
}

# Long video rotates between two categories per week
LONG_VIDEO_TOPICS = [
    {"category": "fashion",  "topic": "complete men capsule wardrobe guide that makes you look rich"},
    {"category": "physique", "topic": "12 week body transformation guide for men starting from zero"},
    {"category": "finance",  "topic": "how to build wealth from scratch in your 20s complete guide"},
    {"category": "diet",     "topic": "men complete nutrition guide for muscle gain and fat loss"},
]

SHORT_PROMPT = """You are a viral YouTube Shorts scriptwriter for a men's self-improvement channel.

Write a 45-second voiceover script (90-110 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "title": "Viral title under 58 chars, no hashtags here",
  "script": "Full voiceover text only, no stage directions, no brackets. Start with a bold fact or shocking statement. End with: Follow for daily tips.",
  "description": "180-word SEO-rich description. Include 3 timestamps: [0:00 Hook] [0:15 Tips] [0:40 Summary]. End with hashtags: #MensFashion #MensHealth #SelfImprovement #MenStyle #Finance",
  "tags": "mens lifestyle,men,self improvement,{category},mens advice,men motivation",
  "search_topic": "2-4 word Pexels search query for background footage, e.g. gym workout man",
  "thumbnail_text": "5 words max ALL CAPS shocking or curiosity-driven"
}}

Rules: Confident authoritative tone. No fluff. Pure value. Each tip must be actionable."""

LONG_PROMPT = """You are a YouTube scriptwriter for a men's self-improvement channel targeting ages 20-40.

Write a full 8-10 minute video script (1100-1300 words) about: {topic}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "title": "Compelling title under 58 chars",
  "script": "Full voiceover script 1100-1300 words. Hook in first 20 seconds. 5 clear value points. Strong CTA at end: subscribe and watch next video.",
  "description": "320-word SEO description. Include chapter timestamps: [0:00 Intro] [1:30 Point 1] [3:00 Point 2] [5:00 Point 3] [7:00 Point 4] [8:30 Summary]. End with hashtags: #MensFashion #MensHealth #SelfImprovement #Finance #MensLifestyle",
  "tags": "mens lifestyle,men,self improvement,{category},mens advice,men motivation,men health",
  "search_topic": "3-5 word Pexels search for background footage",
  "thumbnail_text": "5 words max ALL CAPS"
}}"""


def call_gemini(prompt: str) -> dict:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json",
        },
    }
    resp = requests.post(GEMINI_URL, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type",   choices=["short", "long"], required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    today = datetime.datetime.utcnow()
    weekday = today.weekday()

    if args.type == "short":
        t = DAILY_TOPICS[weekday]
        prompt = SHORT_PROMPT.format(topic=t["topic"], category=t["category"])
        print(f"[GEMINI] Generating SHORT script | Category: {t['category']}")
        print(f"[GEMINI] Topic: {t['topic']}")
    else:
        # Pick long video topic based on which week of year
        week_idx = today.isocalendar()[1] % len(LONG_VIDEO_TOPICS)
        t = LONG_VIDEO_TOPICS[week_idx]
        prompt = LONG_PROMPT.format(topic=t["topic"], category=t["category"])
        print(f"[GEMINI] Generating LONG VIDEO script | Category: {t['category']}")
        print(f"[GEMINI] Topic: {t['topic']}")

    result = call_gemini(prompt)

    # Attach metadata
    result["video_type"] = args.type
    result["category"]   = t["category"]
    result["generated_at"] = today.isoformat()

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[GEMINI] Script saved → {args.output}")
    print(f"[GEMINI] Title: {result.get('title', 'N/A')}")
    print(f"[GEMINI] Script length: {len(result.get('script','').split())} words")


if __name__ == "__main__":
    main()
