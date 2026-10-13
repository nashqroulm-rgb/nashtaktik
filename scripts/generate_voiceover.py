#!/usr/bin/env python3
"""
NASH-02 Voiceover Generator
Uses Microsoft Edge TTS (id-ID-ArdiNeural, +5% rate) for deep, authoritative historical narration.
"""

import sys
import os
import asyncio
import edge_tts
import edge_tts.constants
import edge_tts.communicate

# Fix Microsoft Edge TTS 403 on cloud runners (synthesize via api.msedgeservices.com)
_NEW_WSS = (
    "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
    f"?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
)
edge_tts.constants.WSS_URL = _NEW_WSS
edge_tts.communicate.WSS_URL = _NEW_WSS

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
