#!/usr/bin/env python3
"""
NASH-02 Kinetic Subtitle Generator for Vertical Documentary Shorts
Outputs SubStation Alpha (.ass) with precision sentence-level synchronization,
bold mobile-first typography, strategic keyword highlights, and UI safe-zone margins.
"""

import sys
import os
import re
from typing import Optional, List, Dict, Any

def format_ass_time(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    cs = int((s - int(s)) * 100)
    return f"{int(h):01d}:{int(m):02d}:{int(s):02d}.{cs:02d}"

HIGHLIGHT_KEYWORDS = [
    # General tactical concepts
    "kalah telak", "blunder fatal", "kavaleri berkuda", "kavaleri companion",
    "sayap kiri", "sayap kanan", "sayap tebal", "pincer movement",
    "celah menganga", "robekan celah", "formasi baji", "baji segitiga", "baji lapis baja",
    "menukik tajam", "titik terlemah", "konsentrasi massa", "paling menentukan",
    "kepanikan", "meremukkan", "nyali sang kaisar", "serbuan lari", "hutan tombak",
    "garis komando", "pekik perang", "paean", "bucephalus",
    # Historical commanders & battles
    "aleksander", "darius", "epaminondas", "miltiades", "hannibal", "scipio",
    "sparta", "athena", "persia", "makedonia", "leuctra", "marathon", "gaugamela", "cannae"
]

def chunk_text(text: str, max_words: int = 5) -> List[str]:
    words = text.strip().split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
        i += max_words
    return chunks

def create_ass_subtitles(
    spoken_text: str,
    total_duration: float,
    output_path: str,
    sentence_cues: Optional[List[Dict[str, Any]]] = None
):
    header = """[Script Info]
Title: Nash Taktik Modern Documentary Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ModernShort, Impact, 60, &H00FFFFFF, &H000000FF, &H0010141C, &H80000000, -1, 0, 0, 0, 100, 100, 1, 0, 1, 3.5, 2.0, 2, 80, 80, 360, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    gold_color = r"{\c&H0037D4F5}"
    white_color = r"{\c&H00FFFFFF}"

    if sentence_cues and len(sentence_cues) > 0:
        for cue in sentence_cues:
            s_start = cue["start"]
            s_end = cue["end"]
            stext = cue["text"].strip()
            chunks = chunk_text(stext, max_words=5)
            if not chunks:
                continue

            total_chars = sum(len(c) for c in chunks) or 1
            cur_t = s_start
            s_dur = max(s_end - s_start, 0.5)

            for c in chunks:
                c_dur = (len(c) / total_chars) * s_dur
                c_end = cur_t + c_dur

                styled = c.upper()
                for kw in HIGHLIGHT_KEYWORDS:
                    kw_up = kw.upper()
                    if kw_up in styled:
                        styled = styled.replace(kw_up, f"{gold_color}{kw_up}{white_color}")

                lines.append(f"Dialogue: 0,{format_ass_time(cur_t)},{format_ass_time(c_end)},ModernShort,,0,0,0,,{styled}\n")
                cur_t = c_end
    else:
        # Fallback: chunk full text and divide time proportionally
        chunks = chunk_text(spoken_text, max_words=5)
        if not chunks:
            chunks = [spoken_text]
        dur_per_chunk = total_duration / len(chunks)
        cur_t = 0.0
        for c in chunks:
            end_t = min(cur_t + dur_per_chunk, total_duration)
            styled = c.upper()
            for kw in HIGHLIGHT_KEYWORDS:
                kw_up = kw.upper()
                if kw_up in styled:
                    styled = styled.replace(kw_up, f"{gold_color}{kw_up}{white_color}")
            lines.append(f"Dialogue: 0,{format_ass_time(cur_t)},{format_ass_time(end_t)},ModernShort,,0,0,0,,{styled}\n")
            cur_t = end_t

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[Subtitles] Generated Modern ASS subtitle: {output_path} ({len(lines)-1} cues)")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_subtitles.py <text> <duration_sec> <output_path>")
        sys.exit(1)
    create_ass_subtitles(sys.argv[1], float(sys.argv[2]), sys.argv[3])
