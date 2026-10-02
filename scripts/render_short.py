#!/usr/bin/env python3
"""
NASH-02 Dual-Stack Vertical Short Renderer (1080x1920)
Assembles Top Tactical Map, Center Gold Title Banner, Bottom Faceless Cinematic Visual,
burned ASS subtitles, and mixed voiceover/BGM in a single-pass FFmpeg pipeline.
"""

import sys
import os
import subprocess
import time

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
):
    if duration <= 0.0:
        # Probe voice duration
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice_audio_path
        ], capture_output=True, text=True, check=True)
        duration = float(res.stdout.strip())
        
    frames = int(duration * fps)
    ass_escaped = ass_subtitle_path.replace("\\", "/").replace(":", "\\:")
    clean_banner = banner_title.replace("'", "").replace(":", " - ").replace(",", " ").upper()
    
    # Dual-stack filter complex
    filter_complex = (
        f"[0:v]scale=1920:1080,zoompan=z='min(zoom+0.0003,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps},"
        f"crop=1080:920:(1920-1080)/2:(1080-920)/2[top];"
        f"[1:v]scale=1920:1080,zoompan=z='max(1.06-0.0003*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps},"
        f"crop=1080:920:(1920-1080)/2:(1080-920)/2[bot];"
        f"color=c=#10141C:s=1080x80:d={duration}[sep_bg];"
        f"[sep_bg]drawbox=x=0:y=0:w=1080:h=4:color=#D4AF37:t=fill,"
        f"drawbox=x=0:y=76:w=1080:h=4:color=#D4AF37:t=fill,"
        f"drawtext=text='{clean_banner}':fontsize=36:fontcolor=#F5D76E:x=(w-text_w)/2:y=(h-text_h)/2[sep];"
        f"[top][sep][bot]vstack=inputs=3[stacked];"
        f"[stacked]drawbox=x=40:y=40:w=320:h=50:color=#121821@0.85:t=fill,"
        f"drawbox=x=40:y=40:w=320:h=50:color=#D4AF37@0.6:t=2,"
        f"drawtext=text='NASH TAKTIK • @nashtaktik':fontsize=20:fontcolor=#F5D76E:x=55:y=55,"
        f"ass='{ass_escaped}'[vout];"
        f"[3:a]volume=0.15,afade=t=out:st={max(duration - 1.5, 0.5):.1f}:d=1.5[bgm];"
        f"[2:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", top_image_path,
        "-loop", "1", "-i", bot_image_path,
        "-i", voice_audio_path,
        "-i", bgm_audio_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        output_video_path
    ]
    
    t0 = time.time()
    subprocess.run(cmd, check=True)
    dt = time.time() - t0
    
    sz_mb = os.path.getsize(output_video_path) / (1024 * 1024)
    print(f"[Renderer] Rendered Dual-Stack Short ({duration:.2f}s) in {dt:.1f}s -> {output_video_path} ({sz_mb:.2f} MB)")
    return output_video_path

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
