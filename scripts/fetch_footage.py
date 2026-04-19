#!/usr/bin/env python3
"""
scripts/fetch_footage.py
Downloads royalty-free stock video clips from Pexels API.
Short videos → portrait 9:16 orientation
Long videos  → landscape 16:9 orientation

Usage:
  python scripts/fetch_footage.py --input /tmp/script_data.json --type short --outdir /tmp/clips
"""

import argparse, json, os, sys, time
import requests

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"

# Fallback topics if Pexels returns 0 results for the specific topic
FALLBACK_QUERIES = {
    "fashion":  ["men suit", "men style", "fashion lifestyle"],
    "physique": ["gym workout", "fitness man", "weights training"],
    "diet":     ["healthy food", "meal prep", "nutrition"],
    "finance":  ["business man", "money", "city lifestyle"],
}


def search_pexels(query: str, num_clips: int, orientation: str) -> list:
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {
        "query": query,
        "per_page": num_clips,
        "orientation": orientation,
        "size": "medium",       # medium = HD quality
    }
    resp = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("videos", [])


def pick_best_file(video: dict, max_width: int = 1080) -> str | None:
    """Pick the highest quality video file at or below max_width."""
    files = sorted(video.get("video_files", []), key=lambda x: x.get("width", 0), reverse=True)
    for f in files:
        if f.get("width", 9999) <= max_width and f.get("link"):
            return f["link"]
    return files[0]["link"] if files else None


def download_clip(url: str, path: str) -> bool:
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                f.write(chunk)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        return size_mb > 0.5   # Must be at least 500KB to be valid
    except Exception as e:
        print(f"[PEXELS] Download failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True, help="Path to script_data.json")
    parser.add_argument("--type",   choices=["short", "long"], required=True)
    parser.add_argument("--outdir", required=True, help="Directory to save clips")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    with open(args.input) as f:
        data = json.load(f)

    search_topic = data.get("search_topic", "men lifestyle")
    category     = data.get("category", "fashion")

    if args.type == "short":
        orientation = "portrait"
        num_clips   = 5
        max_width   = 1080
    else:
        orientation = "landscape"
        num_clips   = 12
        max_width   = 1920

    print(f"[PEXELS] Searching: '{search_topic}' | {orientation} | {num_clips} clips")

    videos = search_pexels(search_topic, num_clips, orientation)

    # Try fallback if not enough results
    if len(videos) < 3:
        fallbacks = FALLBACK_QUERIES.get(category, ["men lifestyle"])
        for fb in fallbacks:
            print(f"[PEXELS] Low results, trying fallback: '{fb}'")
            videos = search_pexels(fb, num_clips, orientation)
            if len(videos) >= 3:
                break

    if not videos:
        print("[PEXELS] ERROR: No videos found. Check PEXELS_API_KEY.")
        sys.exit(1)

    downloaded = []
    for i, video in enumerate(videos):
        link = pick_best_file(video, max_width)
        if not link:
            continue

        out_path = os.path.join(args.outdir, f"clip_{i:02d}.mp4")
        print(f"[PEXELS] Downloading clip {i+1}/{len(videos)} ...", end=" ", flush=True)

        if download_clip(link, out_path):
            downloaded.append(out_path)
            size_mb = os.path.getsize(out_path) / (1024*1024)
            print(f"OK ({size_mb:.1f} MB)")
        else:
            print("SKIPPED")

        time.sleep(0.3)   # Be polite to Pexels API

    print(f"[PEXELS] Downloaded {len(downloaded)} clips → {args.outdir}")

    if len(downloaded) < 2:
        print("[PEXELS] ERROR: Need at least 2 clips to assemble video.")
        sys.exit(1)


if __name__ == "__main__":
    main()
