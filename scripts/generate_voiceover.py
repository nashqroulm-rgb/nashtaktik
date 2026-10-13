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

ENDPOINTS = [
    (
        "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
        f"?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
    ),
    (
        "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
        f"?TrustedClientToken={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
    ),
]

async def synthesize(text: str, output_path: str) -> list[dict]:
    last_err = None
    for endpoint in ENDPOINTS:
        edge_tts.constants.WSS_URL = endpoint
        setattr(edge_tts.communicate, "WSS_URL", endpoint)
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
                cues = []
                with open(output_path, "wb") as f:
                    async for chunk in communicate.stream():
                        ctype = chunk.get("type")
                        if ctype == "audio" and "data" in chunk:
                            f.write(chunk["data"])
                        elif ctype == "SentenceBoundary" and "offset" in chunk and "duration" in chunk:
                            st = chunk["offset"] / 10_000_000
                            dur = chunk["duration"] / 10_000_000
                            cues.append({"start": st, "end": st + dur, "text": chunk.get("text", "")})
                print(f"[EdgeTTS] Generated voiceover: {output_path} ({os.path.getsize(output_path)} bytes, {len(cues)} sentences)")
                return cues
            except Exception as e:
                last_err = e
                await asyncio.sleep(1.0)
    raise RuntimeError(f"All TTS endpoints failed. Last error: {last_err}")

def generate_voiceover(text: str, output_path: str) -> list[dict]:
    return asyncio.run(synthesize(text, output_path))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_voiceover.py <text> <output_path>")
        sys.exit(1)
    text = sys.argv[1]
    out_path = sys.argv[2]
    generate_voiceover(text, out_path)
