#!/usr/bin/env python3
"""
NASH-02 Long-Form Video Publisher & Scheduler
Publishes or schedules documentary episodes to YouTube Data API v3 and Zernio.
"""

import sys
import os
import json
import urllib.parse
import urllib.request
import urllib.error
import argparse
import time

def get_env_var(name: str, default: str = "") -> str:
    val = os.environ.get(name)
    if val:
        return val.strip()
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip()
    return default

def get_yt_access_token() -> str:
    refresh_token = get_env_var("YT_REFRESH_TOKEN")
    client_id = get_env_var("GOOGLE_CLIENT_ID")
    client_secret = get_env_var("GOOGLE_CLIENT_SECRET")
    
    if not refresh_token:
        raise ValueError("Missing YT_REFRESH_TOKEN")
        
    data = urllib.parse.urlencode({
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["access_token"]

def upload_youtube_long(
    video_path: str,
    title: str,
    description: str,
    schedule_time: str | None = None,
    tags: list | None = None
) -> dict:
    token = get_yt_access_token()
    file_size = os.path.getsize(video_path)
    
    status_dict: dict[str, str | bool] = {
        "selfDeclaredMadeForKids": False
    }
    
    if schedule_time:
        # Scheduled release must be private until publishAt
        status_dict["privacyStatus"] = "private"
        status_dict["publishAt"] = schedule_time
        print(f"[YouTube] Scheduling publication for: {schedule_time}")
    else:
        status_dict["privacyStatus"] = "public"
        print("[YouTube] Publishing immediately as PUBLIC")
        
    meta = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["Nash Taktik", "Sejarah Perang", "Taktik Militer"],
            "categoryId": "27"
        },
        "status": status_dict
    }
    
    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    init_req = urllib.request.Request(
        init_url,
        data=json.dumps(meta).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size)
        },
        method="POST"
    )
    with urllib.request.urlopen(init_req) as init_resp:
        upload_url = init_resp.headers.get("Location")
        
    chunk_size = 4 * 1024 * 1024
    offset = 0
    video_id = None
    t0 = time.time()
    
    with open(video_path, "rb") as vf:
        while offset < file_size:
            chunk = vf.read(min(chunk_size, file_size - offset))
            n = len(chunk)
            req = urllib.request.Request(
                upload_url,
                data=chunk,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(n),
                    "Content-Range": f"bytes {offset}-{offset + n - 1}/{file_size}"
                },
                method="PUT"
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    if resp.status in [200, 201]:
                        res_json = json.loads(resp.read().decode())
                        video_id = res_json.get("id")
                        break
            except urllib.error.HTTPError as e:
                if e.code == 308:
                    pass
                else:
                    raise e
            offset += n
            pct = (offset / file_size) * 100
            print(f"  Upload progress: {pct:.1f}% ({offset / (1024*1024):.1f}/{file_size / (1024*1024):.1f} MB)...")
            
    dt = time.time() - t0
    yt_url = f"https://youtu.be/{video_id}"
    print(f"\n[YouTube Long-Form] SUCCESS in {dt:.1f}s -> {yt_url}")
    return {"ok": True, "videoId": video_id, "url": yt_url, "scheduled": schedule_time}

def main():
    parser = argparse.ArgumentParser(description="Publish or schedule long-form video")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--desc", required=True, help="Video description")
    parser.add_argument("--schedule", required=False, help="ISO-8601 UTC schedule time, e.g. 2026-10-08T12:00:00Z")
    args = parser.parse_args()
    
    upload_youtube_long(args.video, args.title, args.desc, args.schedule)

if __name__ == "__main__":
    main()
