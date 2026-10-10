#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diag_gemini.py - finds out exactly why calls fail with
"Request had invalid authentication credentials".

Run it in your VP folder:

    python diag_gemini.py

It asks for the Google key (paste the SAME key that's in Railway -> GEMINI_API_KEY,
or the one saved on your Solana page). The key is only used while this runs; it's never
printed or saved. It then tests the key every way Google allows - normal requests and
live voice calls, with each way of sending the key - and tells you what works.

Results are also saved to diag_result.txt (no key inside) so you can paste them to me.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Installing websockets ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "websockets"])
    import websockets

BASE = "https://generativelanguage.googleapis.com/v1beta"
WS = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
BRIDGE = "https://vocallus-bridge-production.up.railway.app/health"
LIVE_MODELS = ["gemini-2.5-flash-native-audio-preview-12-2025", "gemini-3.8-live"]
TEXT_MODELS = ["gemini-2.5-flash", "gemini-3.8-flash"]
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def short(s, n=160):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + "..."


def http(url, headers=None, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=dict({"Content-Type": "application/json"}, **(headers or {})),
                                 method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def err_msg(body):
    try:
        e = json.loads(body).get("error", {})
        return f'{e.get("status", "")} {e.get("message", "")}'.strip()
    except Exception:
        return body


WAYS = {
    "key in URL (?key=)": lambda k: ({}, f"key={k}"),
    "x-goog-api-key header": lambda k: ({"x-goog-api-key": k}, ""),
    "Authorization: Bearer": lambda k: ({"Authorization": f"Bearer {k}"}, ""),
}


async def open_ws(url, headers):
    try:
        return await websockets.connect(url, additional_headers=headers, open_timeout=15, max_size=None)
    except TypeError:                                   # older websockets versions
        return await websockets.connect(url, extra_headers=headers, open_timeout=15, max_size=None)


async def live_try(model, headers, query):
    url = WS + (("?" + query) if query else "")
    ws = None
    try:
        ws = await open_ws(url, headers)
        await ws.send(json.dumps({"setup": {
            "model": f"models/{model}",
            "generationConfig": {"responseModalities": ["AUDIO"]},
            "systemInstruction": {"parts": [{"text": "Say hi."}]}}}))
        end = time.time() + 12
        while time.time() < end:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - time.time()))
            except asyncio.TimeoutError:
                return False, "no answer from Google in 12 s"
            try:
                m = json.loads(raw)
            except Exception:
                continue
            if "setupComplete" in m:
                return True, "connected (setupComplete)"
            if "error" in m:
                return False, short(m["error"])
        return False, "no setupComplete"
    except websockets.exceptions.ConnectionClosed as e:
        rc = getattr(e, "rcvd", None)
        code = rc.code if rc else getattr(e, "code", "")
        reason = rc.reason if rc else getattr(e, "reason", "")
        return False, f"closed {code} {short(reason)}"
    except Exception as e:
        resp = getattr(e, "response", None)
        code = getattr(resp, "status_code", None) or getattr(e, "status_code", "")
        return False, f"{type(e).__name__} {code} {short(e)}"
    finally:
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass


def main():
    say("Vocallus Gemini diagnostic")
    say("=" * 60)

    st, body = http(BRIDGE)
    say(f"\n[server] {BRIDGE} -> {st}")
    if st == 200:
        try:
            h = json.loads(body)
            say(f"         ai: {h.get('ai')} | firebase: {h.get('firebase')} | model: {h.get('model')}")
        except Exception:
            say("         " + short(body))

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        print("\nPaste the Google key from Railway (GEMINI_API_KEY). It isn't shown or saved.")
        key = input("Key: ").strip()
    if not key:
        say("No key - stopping.")
        return
    kind = "AQ. (new AI Studio key)" if key.startswith("AQ.") else "AIza (classic key)" if key.startswith("AIza") else "unknown format"
    say(f"\n[key] type: {kind}, length {len(key)}, ends with ...{key[-4:]}")
    if key != key.strip() or " " in key or '"' in key:
        say("      WARNING: the key has spaces or quotes in it - remove them in Railway.")

    say("\n[1] List models (simple request)")
    ok_ways = []
    for name, f in WAYS.items():
        h, q = f(key)
        st, body = http(f"{BASE}/models" + (f"?{q}" if q else ""), headers=h)
        good = st == 200
        if good:
            ok_ways.append(name)
        say(f"    {'OK  ' if good else 'FAIL'} {name:<24} {st} {'' if good else short(err_msg(body), 120)}")

    say("\n[2] Text answer (summaries / test chat)")
    for model in TEXT_MODELS:
        for name, f in WAYS.items():
            h, q = f(key)
            st, body = http(f"{BASE}/models/{model}:generateContent" + (f"?{q}" if q else ""), headers=h,
                            body={"contents": [{"parts": [{"text": "Say OK"}]}]})
            say(f"    {'OK  ' if st == 200 else 'FAIL'} {model:<22} {name:<24} {st} {'' if st == 200 else short(err_msg(body), 110)}")

    say("\n[3] Live voice connection (phone + web calls)")
    live_ok = []
    for model in LIVE_MODELS:
        for name, f in WAYS.items():
            h, q = f(key)
            good, why = asyncio.run(live_try(model, h, q))
            if good:
                live_ok.append((model, name))
            say(f"    {'OK  ' if good else 'FAIL'} {model:<46} {name:<24} {why}")

    say("\n" + "=" * 60)
    say("RESULT")
    if live_ok:
        m, w = live_ok[0]
        say(f"  Live calls WORK with: {m} + {w}")
        say("  Send me this file so I can set the server to use exactly that.")
    elif ok_ways:
        say("  The key works for normal requests but NOT for live voice calls.")
        say("  Google's live voice service doesn't accept this key type.")
        say("  Fix: make a key that live calls accept (see the message from Claude), or send me this file.")
    else:
        say("  The key doesn't work for anything. It's wrong, deleted, or its project is restricted.")
        say("  Fix: make a new key in AI Studio and put it in Railway (GEMINI_API_KEY).")

    out = Path(__file__).resolve().parent / "diag_result.txt"
    out.write_text("\n".join(OUT), encoding="utf-8")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
