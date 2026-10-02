#!/usr/bin/env python3
"""
NASH-02 Multi-Platform Short Publisher
Publishes vertical Shorts (1080x1920) simultaneously to:
1. YouTube Shorts (Direct YouTube Data API v3)
2. TikTok (@nashtaktik via Zernio API)
3. Instagram Reels (@nashtaktik via Zernio API)
4. Telegram Notification (Optional)
"""

import sys
import os
import json
import urllib.parse
import urllib.request
import urllib.error
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
        raise ValueError("Missing YT_REFRESH_TOKEN in environment")
        
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

def upload_youtube_short(video_path: str, title: str, description: str, tags: list | None = None) -> dict:
    print(f"\n[YouTube] Publishing to YouTube Shorts...")
    token = get_yt_access_token()
    file_size = os.path.getsize(video_path)
    
    # Ensure #Shorts is present in title
    yt_title = title if "#Shorts" in title else f"{title} #Shorts"
    
    meta = {
        "snippet": {
            "title": yt_title[:100],
            "description": description[:5000],
            "tags": tags or ["Shorts", "Nash Taktik", "Sejarah Perang", "Taktik Militer"],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
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
            
    yt_url = f"https://youtube.com/shorts/{video_id}"
    print(f"[YouTube] SUCCESS -> {yt_url}")
    return {"ok": True, "videoId": video_id, "url": yt_url}

def upload_zernio(video_path: str, caption: str) -> dict:
    z_key = get_env_var("ZERNIO_API_KEY")
    if not z_key:
        print("[Zernio] Skipped (ZERNIO_API_KEY not set)")
        return {"ok": False, "error": "ZERNIO_API_KEY missing"}
        
    print(f"\n[Zernio] Publishing to TikTok & Instagram...")
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
    with urllib.request.urlopen(post_req) as p_resp:
        post_res = json.loads(p_resp.read().decode())
        post_obj = post_res.get("post") or post_res
        post_id = post_obj.get("_id") or post_obj.get("id")
        print(f"[Zernio] Post dispatched successfully! ID: {post_id}")
        return {"ok": True, "postId": post_id, "platforms": post_obj.get("platforms")}

def send_telegram_alert(message: str):
    bot_token = get_env_var("BOT_TOKEN")
    chat_id = get_env_var("OWNER_CHAT_ID")
    if not bot_token or not chat_id:
        return
        
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=data)
        urllib.request.urlopen(req)
        print("[Telegram] Alert sent to owner.")
    except Exception as e:
        print(f"[Telegram] Alert failed: {e}")

def publish_short(video_path: str, title: str, description: str, linked_long_url: str | None = None) -> dict:
    results = {}
    
    # 1. YouTube Shorts
    try:
        yt_desc = description
        if linked_long_url:
            yt_desc = f"{description}\n\n👉 Tonton analisis taktik lengkapnya: {linked_long_url}\n\n#Shorts #SejarahPerang"
        yt_res = upload_youtube_short(video_path, title, yt_desc)
        results["youtube"] = yt_res
    except Exception as e:
        print(f"[YouTube] Error: {e}")
        results["youtube"] = {"ok": False, "error": str(e)}
        
    # 2. Zernio (TikTok + IG)
    try:
        z_caption = f"{title}\n\n{description[:300]}\n\n#sejarahperang #taktikmiliter #nashtaktik"
        z_res = upload_zernio(video_path, z_caption)
        results["zernio"] = z_res
    except Exception as e:
        print(f"[Zernio] Error: {e}")
        results["zernio"] = {"ok": False, "error": str(e)}
        
    # 3. Telegram Report
    yt_url = results.get("youtube", {}).get("url", "Failed")
    alert = (
        f"⚔️ <b>[NASH TAKTIK] SHORT BARU BERHASIL TAYANG</b>\n\n"
        f"<b>Judul:</b> {title}\n"
        f"<b>YouTube Shorts:</b> {yt_url}\n"
        f"<b>TikTok + IG:</b> Dispatched via Zernio\n"
    )
    send_telegram_alert(alert)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python publish_short.py <video_path> <title> <desc> [linked_long_url]")
        sys.exit(1)
        
    v_path = sys.argv[1]
    tit = sys.argv[2]
    des = sys.argv[3]
    l_url = sys.argv[4] if len(sys.argv) > 4 else None
    
    publish_short(v_path, tit, des, l_url)
