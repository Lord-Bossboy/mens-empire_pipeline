#!/usr/bin/env python3
"""scripts/assemble_video.py — FFmpeg video assembly engine"""
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

def gen_srt(audio,workdir):
    srt=os.path.join(workdir,"captions.srt")
    try:
        from faster_whisper import WhisperModel
        print("[WHISPER] Transcribing...")
        model=WhisperModel("base",device="cpu",compute_type="int8")
        segs,_=model.transcribe(audio,word_timestamps=False)
        def ts(s):
            h=int(s//3600);m=int((s%3600)//60);sec=s%60
            return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".",",")
        with open(srt,"w") as f:
            for i,s in enumerate(segs,1):
                f.write(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n\n")
        print(f"[WHISPER] Done → {srt}"); return srt
    except Exception as e:
        print(f"[WHISPER] Skipped: {e}"); return None

def composite(looped,audio,srt,output,channel):
    style="FontName=Liberation Sans,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=80"
    wm=f"drawtext=text='{channel}':fontcolor=white@0.35:fontsize=16:x=20:y=20:font=Liberation Sans:bold="
    if srt and os.path.exists(srt):
        sp=srt.replace("\\","/").replace(":","\\:")
        vf=f"subtitles='{sp}':force_style='{style}',{wm}"
    else: vf=wm
    run_ff(["-i",looped,"-i",audio,"-vf",vf,
            "-c:v","libx264","-preset","fast","-crf","22",
            "-c:a","aac","-b:a","192k","-shortest",output],"Composite final video")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True); p.add_argument("--audio",required=True)
    p.add_argument("--clipsdir",required=True); p.add_argument("--type",choices=["short","long"],required=True)
    p.add_argument("--output",required=True); p.add_argument("--no-captions",action="store_true")
    a=p.parse_args()
    W,H=(1080,1920) if a.type=="short" else (1920,1080)
    clips=sorted(glob.glob(os.path.join(a.clipsdir,"*.mp4")))
    if not clips: print(f"[ERROR] No clips in {a.clipsdir}"); sys.exit(1)
    dur=ffprobe_duration(a.audio)
    print(f"\n[ASSEMBLE] {a.type.upper()} | {W}x{H} | {dur:.1f}s | {len(clips)} clips")
    with tempfile.TemporaryDirectory(prefix="yt_") as wd:
        looped=build_looped(clips,dur,W,H,wd)
        srt=None if a.no_captions else gen_srt(a.audio,wd)
        composite(looped,a.audio,srt,a.output,"Men's Empire")
    print(f"\n[DONE] {a.output} ({os.path.getsize(a.output)/1024/1024:.1f} MB)")

if __name__=="__main__": main()
