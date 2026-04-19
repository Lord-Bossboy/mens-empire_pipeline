#!/usr/bin/env python3
"""scripts/assemble_video.py — DireWealth FFmpeg video assembly engine"""
import argparse, glob, json, os, subprocess, sys, tempfile
from pathlib import Path

def ffprobe_duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=noprint_wrappers=1:nokey=1",path],
                       capture_output=True,text=True,check=True)
    return float(r.stdout.strip())

def run_ff(cmd, label=""):
    print(f"[FFMPEG] {label}")
    r = subprocess.run(["ffmpeg","-y"]+cmd+["-loglevel","error"],capture_output=True,text=True)
    if r.returncode!=0: print(f"[ERR] {r.stderr[-400:]}"); sys.exit(1)

def normalize_clip(src,dst,w,h):
    run_ff(["-i",src,"-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1",
            "-r","30","-c:v","libx264","-preset","veryfast","-crf","26","-an",dst],
           f"Normalize {Path(src).name}")

def build_looped(clips,duration,w,h,workdir):
    nd=os.path.join(workdir,"norm"); os.makedirs(nd,exist_ok=True)
    normed=[]
    for i,c in enumerate(clips):
        d=os.path.join(nd,f"n{i:02d}.mp4"); normalize_clip(c,d,w,h); normed.append(d)
    cf=os.path.join(workdir,"concat.txt"); total=0.0; entries=[]; idx=0
    while total<duration+2:
        c=normed[idx%len(normed)]; entries.append(c)
        try: total+=ffprobe_duration(c)
        except: total+=5.0
        idx+=1
        if idx>200: break
    with open(cf,"w") as f:
        for e in entries: f.write(f"file '{e}'\n")
    out=os.path.join(workdir,"looped.mp4")
    run_ff(["-f","concat","-safe","0","-i",cf,"-t",str(duration+1),"-c","copy",out],"Concat")
    return out

def composite(looped,audio,output,channel):
    wm=f"drawtext=text='{channel}':fontcolor=white@0.35:fontsize=16:x=20:y=20:font=Liberation Sans"
    run_ff(["-i",looped,"-i",audio,"-vf",wm,
            "-c:v","libx264","-preset","fast","-crf","22",
            "-c:a","aac","-b:a","192k","-shortest",output],"Composite final video")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--audio",required=True)
    p.add_argument("--clipsdir",required=True)
    p.add_argument("--type",choices=["short","long"],required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    W,H=(1080,1920) if a.type=="short" else (1920,1080)
    clips=sorted(glob.glob(os.path.join(a.clipsdir,"*.mp4")))
    if not clips: print(f"[ERROR] No clips in {a.clipsdir}"); sys.exit(1)
    dur=ffprobe_duration(a.audio)
    print(f"\n[ASSEMBLE] {a.type.upper()} | {W}x{H} | {dur:.1f}s | {len(clips)} clips")
    with tempfile.TemporaryDirectory(prefix="yt_") as wd:
        looped=build_looped(clips,dur,W,H,wd)
        composite(looped,a.audio,a.output,"DireWealth")
    print(f"\n[DONE] {a.output} ({os.path.getsize(a.output)/1024/1024:.1f} MB)")

if __name__=="__main__": main()