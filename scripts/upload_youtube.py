#!/usr/bin/env python3
"""scripts/upload_youtube.py — YouTube Data API v3 uploader"""
import argparse, json, os, pickle, sys
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("[ERROR] pip install google-auth google-auth-oauthlib google-api-python-client"); sys.exit(1)

def get_service(token_path, secrets_path):
    with open(token_path,"rb") as f: creds=pickle.load(f)
    if creds.expired and creds.refresh_token: creds.refresh(Request())
    with open(token_path,"wb") as f: pickle.dump(creds,f)
    return build("youtube","v3",credentials=creds)

def upload(service, video_path, title, description, tags, is_short):
    if is_short and "#Shorts" not in title: title=f"{title} #Shorts"
    if is_short: description+="\n\n#Shorts #MensFashion #MensHealth #SelfImprovement"
    body={"snippet":{"title":title[:100],"description":description[:5000],
                     "tags":tags[:500] if isinstance(tags,str) else ",".join(tags)[:500],
                     "categoryId":"22","defaultLanguage":"en"},
          "status":{"privacyStatus":"public","selfDeclaredMadeForKids":False,"madeForKids":False}}
    media=MediaFileUpload(video_path,mimetype="video/mp4",resumable=True,chunksize=1024*1024*5)
    print(f"[UPLOAD] Starting: {title}")
    req=service.videos().insert(part=",".join(body.keys()),body=body,media_body=media)
    resp=None
    while resp is None:
        status,resp=req.next_chunk()
        if status: print(f"[UPLOAD] {int(status.progress()*100)}%")
    vid_id=resp["id"]
    print(f"[UPLOAD] Done → https://youtu.be/{vid_id}")
    return vid_id

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video",required=True); p.add_argument("--meta",required=True)
    p.add_argument("--type",choices=["short","long"],default="short")
    p.add_argument("--token",required=True); p.add_argument("--secrets",required=True)
    a=p.parse_args()
    with open(a.meta) as f: meta=json.load(f)
    service=get_service(a.token,a.secrets)
    upload(service,a.video,meta["title"],meta["description"],meta["tags"],a.type=="short")

if __name__=="__main__": main()
