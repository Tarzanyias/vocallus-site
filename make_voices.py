#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_voices.py - makes the voice samples for the Solana page with Google's Gemini voice model.

Put it in your VP folder and run:

    python make_voices.py

It asks for a Google (Gemini) API key, then saves:
    Audio/solana.mp3   - default voice (Aoede)   "Hello, I'm a voice from Vocallus."
    Audio/pfmale.mp3   - Pro female voice (Kore)
    Audio/pmale.mp3    - Pro male voice (Charon)

These are the same Gemini voices Solana uses on calls (see voices_bridge.py).
The key is only used while this runs - it isn't saved anywhere.
If an MP3 can't be made on your computer, it saves a .wav instead (the site plays either).
"""

import base64
import json
import os
import shutil
import struct
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LINE = "Hello, I'm a voice from Vocallus."
MODEL = "gemini-2.5-flash-preview-tts"
VOICES = [  # file name, Gemini voice, description
    ("solana", "Aoede", "default voice"),
    ("pfmale", "Kore", "Pro female voice"),
    ("pmale", "Charon", "Pro male voice"),
]


def tts(key, voice):
    body = {
        "contents": [{"parts": [{"text": f"Say in a warm, friendly, professional tone: {LINE}"}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        raise RuntimeError(msg or f"HTTP {e.code}")
    for c in resp.get("candidates", []):
        for p in (c.get("content") or {}).get("parts", []):
            d = p.get("inlineData") or p.get("inline_data")
            if d and d.get("data"):
                mime = d.get("mimeType") or d.get("mime_type") or ""
                rate = 24000
                if "rate=" in mime:
                    try:
                        rate = int(mime.split("rate=")[1].split(";")[0])
                    except ValueError:
                        pass
                return base64.b64decode(d["data"]), rate
    raise RuntimeError("no audio came back")


def to_mp3(pcm, rate):
    try:
        import lameenc  # noqa: F401
    except ImportError:
        print("   installing lameenc (MP3 encoder)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "lameenc"], check=False)
    try:
        import lameenc
        enc = lameenc.Encoder()
        enc.set_bit_rate(64)
        enc.set_in_sample_rate(rate)
        enc.set_channels(1)
        enc.set_quality(2)
        return bytes(enc.encode(pcm) + enc.flush())
    except Exception:
        pass
    ff = shutil.which("ffmpeg")
    if ff:
        r = subprocess.run([ff, "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "-",
                            "-b:a", "64k", "-f", "mp3", "-"], input=pcm, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
    return None


def wav(pcm, rate):
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) +
            b"data" + struct.pack("<I", len(pcm)) + pcm)


def main():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        print("Paste your Google (Gemini) API key. Get one at https://aistudio.google.com/api-keys")
        print("It's only used right now - it isn't saved anywhere.")
        key = input("API key: ").strip()
    if not key:
        print("No key - nothing made.")
        return 1

    out = ROOT / "Audio"
    out.mkdir(exist_ok=True)
    failed = 0
    for name, voice, desc in VOICES:
        print(f"Making Audio/{name} ({desc}, {voice})...")
        try:
            pcm, rate = tts(key, voice)
        except Exception as e:
            print(f"[warn] {name}: {e}")
            failed += 1
            continue
        mp3 = to_mp3(pcm, rate)
        if mp3:
            (out / f"{name}.mp3").write_bytes(mp3)
            old = out / f"{name}.wav"
            if old.exists():
                old.unlink()
            print(f"[ok] Audio/{name}.mp3")
        else:
            (out / f"{name}.wav").write_bytes(wav(pcm, rate))
            print(f"[ok] Audio/{name}.wav (no MP3 encoder on this computer - WAV plays fine)")

    if failed:
        print(f"\n{failed} voice(s) failed - check the key and try again.")
        return 1
    print("\nDone. Now push the site so the samples go live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
