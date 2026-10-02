#!/usr/bin/env python3
"""
NASH-02 Voiceover Generator
Uses Microsoft Edge TTS (id-ID-ArdiNeural, +5% rate) for deep, authoritative historical narration.
"""

import sys
import os
import asyncio
import edge_tts

VOICE = "id-ID-ArdiNeural"
RATE = "+5%"

async def synthesize(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
    await communicate.save(output_path)
    print(f"[EdgeTTS] Generated voiceover: {output_path} ({os.path.getsize(output_path)} bytes)")

def generate_voiceover(text: str, output_path: str):
    asyncio.run(synthesize(text, output_path))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_voiceover.py <text> <output_path>")
        sys.exit(1)
    text = sys.argv[1]
    out_path = sys.argv[2]
    generate_voiceover(text, out_path)
