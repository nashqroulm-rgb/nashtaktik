#!/usr/bin/env python3
"""
NASH-02 Modern Cinematic Vertical Short Renderer (1080x1920)
Renders multi-scene vertical video with color-matched ambient backdrop,
sharp 16:9 cinematic hero frame, gold hairline border, subtle Ken Burns motion,
burned kinetic ASS subtitles, and master audio mixing in a high-efficiency pipeline.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT_DIR / "assets" / "fonts"

def render_scene_clip(
    image_path: str,
    duration: float,
    output_path: str,
    zoom_mode: str = "in",
    fps: int = 24
) -> str:
    """
    Renders a single 1080x1920 scene clip:
    - Background: Ambient blurred and darkened expansion of the image
    - Foreground: 16:9 cinematic window (1040x585) centered at y=460 with gold hairline border
    - Top & Bottom subtle dark gradients for branding and subtitle readability
    """
    frames = max(int(duration * fps), 2)
    
    # Subtle Ken Burns zoom
    if zoom_mode == "in":
        z_expr = "min(zoom+0.0004,1.06)"
    else:
        z_expr = "max(1.06-0.0004*on,1.0)"
        
    fontfile_opt = ""
    georgia_font = FONTS_DIR / "Georgia.ttf"
    if georgia_font.exists():
        esc_font = georgia_font.resolve().as_posix().replace(":", "\\:")
        fontfile_opt = f"fontfile='{esc_font}':"
        
    filter_complex = (
        f"[0:v]split=2[bg_raw][fg_raw];"
        f"[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=30,eq=brightness=-0.35:contrast=1.15[bg];"
        f"[fg_raw]scale=1040:585,drawbox=x=0:y=0:w=1040:h=585:color=#D4AF37@0.9:t=2[fg];"
        f"[bg][fg]overlay=x=(W-w)/2:y=460[comp];"
        f"[comp]drawbox=x=0:y=0:w=1080:h=220:color=black@0.45:t=fill,"
        f"drawbox=x=0:y=1350:w=1080:h=570:color=black@0.55:t=fill,"
        f"drawtext={fontfile_opt}text='NASH TAKTIK  •  SEJARAH & STRATEGI':fontsize=22:fontcolor=#D4AF37:x=(w-text_w)/2:y=120[vout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration),
        "-i", image_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def render_multiscene_short(
    scenes: List[Dict[str, Any]],
    voice_audio_path: str,
    bgm_audio_path: str,
    ass_subtitle_path: str,
    output_video_path: str,
    temp_dir: Optional[str] = None,
    fps: int = 24
) -> str:
    """
    Renders full multi-scene short video:
    1. Renders individual scene clips
    2. Concat demuxer (lossless)
    3. Final mux with burned ASS subtitles and mixed voice/BGM
    """
    t_start = time.time()
    work_dir = Path(temp_dir) if temp_dir else Path(output_video_path).parent / "temp_scenes"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Render clips
    clip_paths = []
    print(f"[Renderer] Rendering {len(scenes)} cinematic scenes...")
    for i, sc in enumerate(scenes):
        img_p = str(sc["image"])
        dur = float(sc["duration"])
        zoom = sc.get("zoom", "in" if i % 2 == 0 else "out")
        clip_p = work_dir / f"scene_{i:02d}.mp4"
        render_scene_clip(img_p, dur, str(clip_p), zoom_mode=zoom, fps=fps)
        clip_paths.append(clip_p)
        print(f"  - Scene {i+1}/{len(scenes)}: {Path(img_p).name} ({dur:.2f}s)")
        
    # 2. Concat demuxer
    concat_list_file = work_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve().as_posix()}'\n")
            
    raw_visual_path = work_dir / "raw_visual.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(raw_visual_path)
    ]
    subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Probe audio duration for fade
    res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice_audio_path
    ], capture_output=True, text=True, check=True)
    voice_dur = float(res.stdout.strip())
    
    # 3. Final Mux with subtitles & audio
    ass_escaped = Path(ass_subtitle_path).resolve().as_posix().replace(":", "\\:")
    fade_start = max(voice_dur - 1.5, 0.5)
    
    fontsdir_opt = ""
    if FONTS_DIR.exists():
        esc_fontsdir = FONTS_DIR.resolve().as_posix().replace(":", "\\:")
        fontsdir_opt = f":fontsdir='{esc_fontsdir}'"
    
    filter_complex = (
        f"[0:v]ass='{ass_escaped}'{fontsdir_opt}[vout];"
        f"[2:a]volume=0.14,afade=t=out:st={fade_start:.2f}:d=2.0[bgm];"
        f"[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", str(raw_visual_path),
        "-i", voice_audio_path,
        "-i", bgm_audio_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        output_video_path
    ]
    subprocess.run(cmd_mux, check=True)
    
    # Cleanup temp clips
    try:
        for p in clip_paths:
            p.unlink(missing_ok=True)
        raw_visual_path.unlink(missing_ok=True)
        concat_list_file.unlink(missing_ok=True)
    except Exception:
        pass
        
    dt = time.time() - t_start
    sz_mb = os.path.getsize(output_video_path) / (1024 * 1024)
    print(f"[Renderer] Rendered Modern Multi-Scene Short in {dt:.1f}s -> {output_video_path} ({sz_mb:.2f} MB)")
    return output_video_path

def render_short_video(
    top_image_path: str,
    bot_image_path: str,
    voice_audio_path: str,
    bgm_audio_path: str,
    ass_subtitle_path: str,
    banner_title: str,
    output_video_path: str,
    duration: float = 0.0,
    fps: int = 24
) -> str:
    """
    Backwards-compatible wrapper: splits duration between the two images in modern layout.
    """
    if duration <= 0.0:
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice_audio_path
        ], capture_output=True, text=True, check=True)
        duration = float(res.stdout.strip())
        
    half = duration / 2.0
    scenes = [
        {"image": top_image_path, "duration": half, "zoom": "in"},
        {"image": bot_image_path, "duration": duration - half + 0.5, "zoom": "out"}
    ]
    return render_multiscene_short(
        scenes=scenes,
        voice_audio_path=voice_audio_path,
        bgm_audio_path=bgm_audio_path,
        ass_subtitle_path=ass_subtitle_path,
        output_video_path=output_video_path,
        fps=fps
    )

if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Usage: python render_short.py <top_img> <bot_img> <voice_mp3> <bgm_mp3> <ass_file> <title> <out_mp4>")
        sys.exit(1)
        
    render_short_video(
        top_image_path=sys.argv[1],
        bot_image_path=sys.argv[2],
        voice_audio_path=sys.argv[3],
        bgm_audio_path=sys.argv[4],
        ass_subtitle_path=sys.argv[5],
        banner_title=sys.argv[6],
        output_video_path=sys.argv[7]
    )
