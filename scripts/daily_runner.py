#!/usr/bin/env python3
"""
NASH-02 Daily Short Orchestrator & Auto-Publisher
Executed autonomously by GitHub Actions Cron every Monday-Saturday.
Renders the daily short and distributes it across YouTube Shorts, TikTok, and Instagram.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def run_daily_pipeline(target_day: str | None = None, target_week: int | None = None, dry_run: bool = False):
    print("=" * 60)
    print("  NASH-02 AUTONOMOUS DAILY SHORTS PIPELINE")
    print("=" * 60)
    
    state_file = ROOT_DIR / "state" / "campaign_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
        
    week_num = target_week or state.get("active_week", 1)
    short_idx = state.get("next_short_index", 2)
    day_name = target_day or state.get("next_short_day", "selasa").lower()
    
    week_dir = ROOT_DIR / "curriculum" / f"week_{week_num:03d}"
    short_packet_file = week_dir / f"short_{short_idx:02d}_{day_name}.json"
    
    if not short_packet_file.exists():
        # Fallback search by day
        found = list(week_dir.glob(f"short_*_{day_name}.json"))
        if found:
            short_packet_file = found[0]
        else:
            raise FileNotFoundError(f"Packet not found for week {week_num}, day {day_name}: {short_packet_file}")
            
    print(f"Loading packet: {short_packet_file.name}")
    with open(short_packet_file, "r", encoding="utf-8") as f:
        packet = json.load(f)
        
    title = packet["title"]
    spoken_text = packet["spoken_text"]
    
    # Check parent long form link
    long_form_file = week_dir / "long_form.json"
    long_url = None
    if long_form_file.exists():
        with open(long_form_file, "r", encoding="utf-8") as f:
            lf_data = json.load(f)
            long_url = lf_data.get("published_youtube_url")
            
    temp_dir = ROOT_DIR / "temp_render"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    voice_path = temp_dir / f"voice_{day_name}.mp3"
    ass_path = temp_dir / f"subs_{day_name}.ass"
    output_video = temp_dir / f"short_{day_name}_1080x1920.mp4"
    bgm_path = ROOT_DIR / "assets" / "audio" / "The Weight of the Shield.mp3"
    
    # 1. Generate Voiceover
    print(f"\n[1/4] Generating Voiceover (EdgeTTS ArdiNeural)...")
    from generate_voiceover import generate_voiceover
    generate_voiceover(spoken_text, str(voice_path))
    
    # Probe duration
    res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voice_path)
    ], capture_output=True, text=True, check=True)
    duration = float(res.stdout.strip())
    print(f"Voiceover duration: {duration:.2f}s")
    
    # 2. Generate Subtitles
    print(f"\n[2/4] Generating Kinetic ASS Subtitles...")
    from generate_subtitles import create_ass_subtitles
    create_ass_subtitles(spoken_text, duration, str(ass_path))
    
    # 3. Select Images
    images_dir = week_dir / "images"
    # Choose top map and bottom cinematic
    available_imgs = list(images_dir.glob("*.jpg"))
    if not available_imgs:
        raise FileNotFoundError(f"No images found in {images_dir}")
        
    # Map top image preference
    map_imgs = [img for img in available_imgs if "map" in img.name.lower()]
    top_img = map_imgs[0] if map_imgs else available_imgs[0]
    
    # Bottom image preference (different from top)
    bot_imgs = [img for img in available_imgs if img != top_img]
    bot_img = bot_imgs[0] if bot_imgs else top_img
    
    print(f"Top Panel Image    : {top_img.name}")
    print(f"Bottom Panel Image : {bot_img.name}")
    
    # 4. Render Dual-Stack Short Video
    print(f"\n[3/4] Rendering Dual-Stack 1080x1920 Video...")
    from render_short import render_short_video
    render_short_video(
        top_image_path=str(top_img),
        bot_image_path=str(bot_img),
        voice_audio_path=str(voice_path),
        bgm_audio_path=str(bgm_path),
        ass_subtitle_path=str(ass_path),
        banner_title=title,
        output_video_path=str(output_video),
        duration=duration
    )
    
    # 5. Publish
    if dry_run:
        print("\n[Dry Run] Skipping publishing step.")
        return
        
    print(f"\n[4/4] Publishing Across All Platforms...")
    from publish_short import publish_short
    desc = f"{spoken_text}\n\nAnalisis taktik sejarah lengkap di channel YouTube @nashtaktik!"
    pub_res = publish_short(str(output_video), title, desc, long_url)
    
    # Update State
    next_idx = short_idx + 1
    days_order = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
    try:
        cur_d_idx = days_order.index(day_name)
        next_d = days_order[(cur_d_idx + 1) % len(days_order)]
    except ValueError:
        next_d = "senin"
        
    state["next_short_index"] = next_idx
    state["next_short_day"] = next_d
    state["total_shorts_published"] = state.get("total_shorts_published", 0) + 1
    state["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    # Append History
    history_file = ROOT_DIR / "state" / "publish_history.json"
    history = []
    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            
    history.append({
        "type": "short",
        "week": week_num,
        "short_number": short_idx,
        "day": day_name.capitalize(),
        "title": title,
        "published_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platforms": pub_res
    })
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        
    print("\n" + "=" * 60)
    print("  DAILY SHORT PRODUCTION & PUBLISHING COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", help="Target day (senin-sabtu)")
    parser.add_argument("--week", type=int, help="Target week (1-26)")
    parser.add_argument("--dry-run", action="store_true", help="Render without publishing")
    args = parser.parse_args()
    
    run_daily_pipeline(args.day, args.week, args.dry_run)
