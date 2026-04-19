#!/usr/bin/env python3
"""
scripts/generate_voice.py
DireWealth — Voice Generator
Generates voiceover MP3 using Microsoft Edge-TTS (free, unlimited, no API key).
"""
import argparse, asyncio, json, os, sys

try:
    import edge_tts
except ImportError:
    print("[ERROR] pip install edge-tts"); sys.exit(1)

# DireWealth Voice — Deep, calm, authoritative, like a wealthy wolf mentor
STYLE_SETTINGS = {
    "short": {"voice": "en-US-ChristopherNeural", "rate": "-8%",  "pitch": "-6Hz", "volume": "+10%"},
    "long":  {"voice": "en-US-ChristopherNeural", "rate": "-12%", "pitch": "-8Hz", "volume": "+5%"},
    "hype":  {"voice": "en-US-ChristopherNeural", "rate": "-5%",  "pitch": "-6Hz", "volume": "+15%"},
}

async def synthesize(text, output, voice, rate, pitch, volume):
    await edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch, volume=volume).save(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--style",  choices=["short","long","hype"], default="short")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)
    script = data.get("script","").strip()
    if not script:
        print("[ERROR] Empty script"); sys.exit(1)

    s = STYLE_SETTINGS[args.style]
    print(f"[DIREWEALTH TTS] Voice: {s['voice']} | Style: {args.style}")
    print(f"[DIREWEALTH TTS] Rate: {s['rate']} | Pitch: {s['pitch']}")
    asyncio.run(synthesize(script, args.output, s["voice"], s["rate"], s["pitch"], s["volume"]))
    print(f"[DIREWEALTH TTS] Done → {args.output} ({os.path.getsize(args.output)/1024:.1f} KB)")

if __name__ == "__main__":
    main()