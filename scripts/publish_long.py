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
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent

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
    tags: list | None = None,
    thumb_path: str | None = None,
    srt_path: str | None = None
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
    
    # Optional thumbnail
    if thumb_path and os.path.exists(thumb_path) and video_id:
        upload_thumbnail(token, video_id, thumb_path)
        
    return {"ok": True, "videoId": video_id, "url": yt_url, "scheduled": schedule_time}

def upload_thumbnail(token: str, video_id: str, thumb_path: str):
    if not os.path.exists(thumb_path):
        return
    print(f"\n[Thumbnail] Uploading custom thumbnail ({os.path.basename(thumb_path)})...")
    with open(thumb_path, "rb") as tf:
        thumb_data = tf.read()
    thumb_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}"
    req = urllib.request.Request(
        thumb_url,
        data=thumb_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(thumb_data))
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("[Thumbnail] Custom thumbnail applied successfully!")
    except Exception as e:
        print(f"[Thumbnail] Warning: Failed to set thumbnail: {e}")

def upload_zernio(video_path: str, caption: str) -> dict:
    z_key = get_env_var("ZERNIO_API_KEY")
    if not z_key:
        print("[Zernio] Skipped (ZERNIO_API_KEY not set)")
        return {"ok": False, "error": "ZERNIO_API_KEY missing"}
        
    print(f"\n[Zernio] Publishing Long-Form to TikTok & Instagram...")
    file_size = os.path.getsize(video_path)
    
    # 1. Get presigned R2 upload URL
    presign_req = urllib.request.Request(
        "https://api.zernio.com/v1/media/presign",
        data=json.dumps({
            "filename": os.path.basename(video_path),
            "contentType": "video/mp4",
            "size": file_size
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {z_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(presign_req) as resp:
        presign_data = json.loads(resp.read().decode())
        upload_url = presign_data["uploadUrl"]
        public_url = presign_data["publicUrl"]
        
    # 2. Upload video file to Cloudflare storage
    print(f"[Zernio] Uploading video binary ({file_size / (1024*1024):.2f} MB)...")
    with open(video_path, "rb") as vf:
        video_bytes = vf.read()
        
    put_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size)
        },
        method="PUT"
    )
    with urllib.request.urlopen(put_req) as put_resp:
        if put_resp.status != 200:
            raise RuntimeError(f"Storage upload failed: {put_resp.status}")
            
    # 3. Create post for TikTok + Instagram
    post_body = {
        "content": caption,
        "mediaItems": [{"type": "video", "url": public_url}],
        "platforms": [
            {"platform": "tiktok", "accountId": get_env_var("TIKTOK_ACCOUNT_ID", "6abbb2e6694b468f723ea3a4")},
            {"platform": "instagram", "accountId": get_env_var("INSTAGRAM_ACCOUNT_ID", "6abbb38ad9cc457b83f314fc")}
        ],
        "publishNow": True
    }
    
    post_req = urllib.request.Request(
        "https://api.zernio.com/v1/posts",
        data=json.dumps(post_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {z_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(post_req) as post_resp:
        post_data = json.loads(post_resp.read().decode())
        print(f"[Zernio] Post dispatched successfully to TikTok & Instagram!")
        return {"ok": True, "data": post_data}

def publish_week_long_form(week_str: str, schedule_time: str | None = None, video_override: str | None = None):
    week_dir = REPO_DIR / "curriculum" / week_str
    json_path = week_dir / "long_form.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Missing {json_path}")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    title = data.get("title_id", "")
    desc = data.get("description", "")
    tags = data.get("tags", [])
    
    # Determine video file
    video_path = None
    if video_override and os.path.exists(video_override):
        video_path = video_override
    else:
        temp_dir = REPO_DIR / "temp_render"
        candidates = list(temp_dir.glob("*.mp4")) if temp_dir.exists() else []
        if candidates:
            video_path = str(candidates[0])
            
    if not video_path or not os.path.exists(video_path):
        raise FileNotFoundError(f"No video file found for publishing {week_str}")
        
    # Find thumbnail
    thumb_path = None
    img_dir = week_dir / "images"
    if img_dir.exists():
        thumbs = list(img_dir.glob("thumbnail_*.jpg")) or list(img_dir.glob("*thumb*.jpg"))
        if thumbs:
            thumb_path = str(thumbs[0])
            
    res = upload_youtube_long(
        video_path=video_path,
        title=title,
        description=desc,
        schedule_time=schedule_time,
        tags=tags,
        thumb_path=thumb_path
    )
    
    # 2. Upload to Zernio (TikTok + Instagram)
    z_caption = f"{title}\n\n{desc[:300]}\n\n#sejarahperang #taktikmiliter #nashtaktik"
    z_res = upload_zernio(video_path, z_caption)
    
    # Update long_form.json with published URLs
    data["published_youtube_url"] = res["url"]
    data["youtube_video_id"] = res["videoId"]
    data["status"] = "PUBLISHED" if not schedule_time else "SCHEDULED"
    data["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    if z_res.get("ok"):
        data["published_tiktok_status"] = "DISPATCHED"
        data["published_instagram_status"] = "DISPATCHED"
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"\n[Success] Updated {json_path.name} with publication details.")
    return res

def main():
    parser = argparse.ArgumentParser(description="Publish or schedule long-form video")
    parser.add_argument("--week", default="", help="Week identifier, e.g. week_004")
    parser.add_argument("--video", default="", help="Path to video file")
    parser.add_argument("--title", default="", help="Video title")
    parser.add_argument("--desc", default="", help="Video description")
    parser.add_argument("--schedule", default="", help="ISO-8601 UTC schedule time, e.g. 2026-10-08T12:00:00Z")
    parser.add_argument("--thumb", default="", help="Custom thumbnail path")
    args = parser.parse_args()
    
    if args.week:
        publish_week_long_form(args.week, args.schedule or None, args.video or None)
    elif args.video:
        upload_youtube_long(
            video_path=args.video,
            title=args.title,
            description=args.desc,
            schedule_time=args.schedule or None,
            thumb_path=args.thumb or None
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
