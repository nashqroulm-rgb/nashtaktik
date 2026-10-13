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

KEYWORD_MAP = {
    "kavaleri": ["cavalry", "horse"],
    "kuda": ["horse", "cavalry"],
    "baji": ["wedge"],
    "segitiga": ["wedge"],
    "darius": ["darius"],
    "kaisar": ["darius", "emperor", "leader"],
    "aleksander": ["alexander", "leader"],
    "bucephalus": ["horse", "leader", "mounting"],
    "celah": ["wedge", "clash", "gap"],
    "sayap": ["wing", "flank"],
    "menukik": ["attack", "attacking", "clash"],
    "menusuk": ["attack", "attacking", "clash"],
    "pasukan": ["infantry", "phalangites", "phalanx", "army"],
    "tempur": ["clash", "battle", "fighting"],
    "kepanikan": ["fleeing", "retreat", "flee"],
    "meremukkan": ["fleeing", "clash", "attack"],
    "kereta": ["chariot"],
    "tanah": ["plain", "plains", "laborers"],
    "panah": ["archers", "peltasts"],
    "obor": ["campfires", "dawn"],
    "pelajaran": ["leader", "commander", "tablet"],
    "epaminondas": ["epaminondas", "general"],
    "sparta": ["sparta", "phalanx", "hoplite"],
}

def select_images_for_scenes(
    images_dir: Path,
    sentence_cues: list,
    day_name: str,
    packet: dict,
    previously_used: set | None = None
) -> list[Path]:
    available = sorted([f for f in images_dir.glob("*.jpg") if "thumb" not in f.name.lower()])
    if not available:
        raise FileNotFoundError(f"No valid images found in {images_dir}")
        
    num_scenes = max(len(sentence_cues), 1)
    selected = []
    used = set(previously_used) if previously_used else set()
    
    # If used set leaves fewer images than needed, prune oldest
    remaining = [f for f in available if f.name not in used]
    if len(remaining) < num_scenes:
        used = set() # Reset if images exhausted in week
    
    for i, cue in enumerate(sentence_cues):
        stext = cue["text"].lower()
        best_img = None
        best_score = -1
        
        for img in available:
            if img.name in used:
                continue
            score = 0
            img_lower = img.name.lower()
            for id_kw, en_kws in KEYWORD_MAP.items():
                if id_kw in stext:
                    for en in en_kws:
                        if en in img_lower:
                            score += 3
            if score > best_score:
                best_score = score
                best_img = img
                
        if not best_img or best_score <= 0:
            days = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
            day_offset = days.index(day_name) if day_name in days else 0
            start_idx = (day_offset * 6 + i) % len(available)
            for offset in range(len(available)):
                candidate = available[(start_idx + offset) % len(available)]
                if candidate.name not in used:
                    best_img = candidate
                    break
                    
        if best_img:
            used.add(best_img.name)
            selected.append(best_img)
            
    while len(selected) < num_scenes:
        for img in available:
            if img not in selected:
                selected.append(img)
                break
        else:
            selected.append(available[0])
            
    return selected

def run_daily_pipeline(target_day: str | None = None, target_week: int | None = None, dry_run: bool = False):
    import datetime
    print("=" * 60)
    print("  NASH-02 AUTONOMOUS DAILY SHORTS PIPELINE")
    print("=" * 60)
    
    state_file = ROOT_DIR / "state" / "campaign_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)
        
    week_num = target_week or state.get("active_week", 1)
    
    # Dynamic Calendar Mapping (Rule 33 in Thematic Content Factory)
    days_order = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
    days_map = {0: "senin", 1: "selasa", 2: "rabu", 3: "kamis", 4: "jumat", 5: "sabtu"}
    
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_wib = now_utc + datetime.timedelta(hours=7)
    cur_weekday = now_wib.weekday()
    
    if target_day:
        day_name = target_day.lower()
        short_idx = (days_order.index(day_name) + 1) if day_name in days_order else 1
    else:
        if cur_weekday in days_map:
            day_name = days_map[cur_weekday]
            short_idx = cur_weekday + 1
        else:
            # Sunday or off-schedule fallback
            day_name = state.get("next_short_day", "senin").lower()
            short_idx = state.get("next_short_index", 1)
    
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
    sentence_cues = generate_voiceover(spoken_text, str(voice_path))
    
    # Probe duration
    res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voice_path)
    ], capture_output=True, text=True, check=True)
    duration = float(res.stdout.strip())
    print(f"Voiceover duration: {duration:.2f}s ({len(sentence_cues)} sentences)")
    
    # 2. Generate Subtitles
    print(f"\n[2/4] Generating Kinetic ASS Subtitles...")
    from generate_subtitles import create_ass_subtitles
    create_ass_subtitles(spoken_text, duration, str(ass_path), sentence_cues=sentence_cues)
    
    # 3. Select Images for Multi-Scene Short (Anti-Dejavu Tracking)
    images_dir = week_dir / "images"
    state_key = f"used_images_week_{week_num:03d}"
    used_images_this_week = set(state.get(state_key, []))
    
    # Also cross-check publish_history.json to ensure no past images from this week are reused
    history_file = ROOT_DIR / "state" / "publish_history.json"
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                hist_data = json.load(f)
            for entry in hist_data:
                if entry.get("type") == "short" and entry.get("week") == week_num:
                    for im in entry.get("images_used", []):
                        used_images_this_week.add(im)
        except Exception:
            pass
            
    selected_imgs = select_images_for_scenes(
        images_dir, sentence_cues, day_name, packet, previously_used=used_images_this_week
    )
    
    # Record newly selected images to state
    for img in selected_imgs:
        used_images_this_week.add(img.name)
    state[state_key] = sorted(list(used_images_this_week))
    
    scenes = []
    for i, cue in enumerate(sentence_cues):
        img_p = selected_imgs[i]
        dur = max(cue["end"] - cue["start"], 1.0)
        # Add small tail cushion to last scene
        if i == len(sentence_cues) - 1:
            dur += 1.0
        scenes.append({
            "image": str(img_p),
            "duration": dur,
            "zoom": "in" if i % 2 == 0 else "out"
        })
        print(f"  Scene {i+1}: {img_p.name} ({dur:.2f}s) -> {cue['text'][:35]}...")
        
    # 4. Render Modern Multi-Scene Short Video
    print(f"\n[3/4] Rendering Modern Multi-Scene 1080x1920 Video...")
    from render_short import render_multiscene_short
    render_multiscene_short(
        scenes=scenes,
        voice_audio_path=str(voice_path),
        bgm_audio_path=str(bgm_path),
        ass_subtitle_path=str(ass_path),
        output_video_path=str(output_video)
    )
    
    # Verify rendered video integrity with ffprobe (Rule 53)
    if not output_video.exists() or output_video.stat().st_size < 100_000:
        raise RuntimeError(f"Rendered video missing or empty: {output_video}")
    check_res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(output_video)
    ], capture_output=True, text=True)
    if check_res.returncode != 0 or not check_res.stdout.strip():
        raise RuntimeError(f"Rendered video corrupted (moov atom missing or unreadable): {output_video}")
    rendered_dur = float(check_res.stdout.strip())
    print(f"[Verification] Master video verified: {rendered_dur:.2f}s, {output_video.stat().st_size / (1024*1024):.2f} MB")
    
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
        "images_used": [img.name for img in selected_imgs],
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
