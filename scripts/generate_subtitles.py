#!/usr/bin/env python3
"""
NASH-02 Subtitle Generator for Vertical Dual-Stack Layout
Outputs SubStation Alpha (.ass) with keyword color highlights and bottom-third safe margin.
"""

import sys
import os
import re

def format_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):01d}:{int(m):02d}:{s:05.2f}"

def create_ass_subtitles(spoken_text: str, total_duration: float, output_path: str):
    # Split spoken text into short readable chunks (~4-7 words per cue)
    words = spoken_text.split()
    chunk_size = 6
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    
    if not chunks:
        chunks = [spoken_text]
        
    dur_per_chunk = total_duration / len(chunks)
    
    header = """[Script Info]
Title: Nash Taktik Dual-Stack Short Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortCaption, Arial, 48, &H00FFFFFF, &H00000000, &H00000000, &H80000000, -1, 0, 0, 0, 100, 100, 1, 0, 1, 4, 3, 2, 60, 60, 260, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    
    highlight_keywords = [
        "kalah telak", "blunder fatal", "kavaleri berkuda", "naik kembali ke kapal",
        "sayap tebal", "pincer movement", "rawa schinia", "aspis", "sparabara",
        "serbuan lari", "miltiades", "athena", "persia", "darius", "bencana"
    ]
    
    cur_t = 0.0
    for c in chunks:
        end_t = min(cur_t + dur_per_chunk, total_duration)
        s_str = format_time(cur_t)
        e_str = format_time(end_t)
        
        styled = c
        for kw in highlight_keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            styled = pattern.sub(f"{{\\\\c&H003BF5&}}{kw.upper()}{{\\\\c&HFFFFFF&}}", styled)
            
        lines.append(f"Dialogue: 0,{s_str},{e_str},ShortCaption,,0,0,0,,{styled}\n")
        cur_t = end_t
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[Subtitles] Generated ASS subtitle: {output_path} ({len(chunks)} cues)")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_subtitles.py <text> <duration_sec> <output_path>")
        sys.exit(1)
    create_ass_subtitles(sys.argv[1], float(sys.argv[2]), sys.argv[3])
