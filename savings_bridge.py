#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
savings_bridge.py - shorter, cheaper phone calls (Step 1 of the savings plan).

Run from your VP folder (it finds Downloads\\vocallus-bridge):

    python savings_bridge.py

Phone calls only (test calls on the website stay the same):
  1. Solana hangs up by herself after saying goodbye (new "end_call" tool), instead of
     waiting for the caller to hang up.
  2. Silence: after ~11 s of nobody talking she asks "are you still there?"; after ~22 s she
     says goodbye and hangs up. Catches silent robocalls and people who forget to hang up.
  3. Max call length: 10 minutes. One minute before, she politely wraps up.
     Change it in Railway Variables with MAX_CALL_MINUTES.
  4. While Solana is talking and the caller is quiet, the caller's line isn't sent to the AI
     (you pay for that audio). If the caller starts talking over her, it's sent right away,
     including the moment just before, so interrupting still works.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* CALL_SAVINGS */"

EDITS = [
    ("end_call tool",
     "        required: ['caller_name', 'message']\n      }\n    }\n  ]\n}];\n",
     "        required: ['caller_name', 'message']\n      }\n    },\n"
     "    {\n"
     "      name: 'end_call',\n"
     "      description: 'Hang up the phone. Call this only after the caller has nothing else and you have already said goodbye.',\n"
     "      parameters: {\n"
     "        type: 'OBJECT',\n"
     "        properties: { reason: { type: 'STRING', description: 'Optional: why the call is ending' } }\n"
     "      }\n"
     "    }\n  ]\n}];\n"),

    ("end_call is harmless in test calls",
     "async function runToolInner(cfg, name, args, callerPhone) {\n  try {\n",
     "async function runToolInner(cfg, name, args, callerPhone) {\n  if (name === 'end_call') return { ok: true };\n  try {\n"),

    ("Solana knows to hang up",
     "    s += ` The caller's number is ${from || 'unknown'}. Speak like a real person on the phone and keep replies short.`;\n",
     "    s += ` The caller's number is ${from || 'unknown'}. Speak like a real person on the phone and keep replies short.`;\n"
     "    if (cfg.uid) s += ' When the caller has nothing else, say a short goodbye and then call end_call to hang up.';\n"),

    ("agent can be nudged (Gemini)",
     "    close() { closed = true; try { ws.close(); } catch {} }\n  };\n}\n\n/* LIVE_FALLBACK */",
     "    nudge(text) {\n"
     "      if (ready && toolBusy === 0 && ws.readyState === WebSocket.OPEN)\n"
     "        ws.send(JSON.stringify({ clientContent: { turns: [{ role: 'user', parts: [{ text }] }], turnComplete: true } }));\n"
     "    },\n"
     "    close() { closed = true; try { ws.close(); } catch {} }\n  };\n}\n\n/* LIVE_FALLBACK */"),

    ("agent can be nudged (backup models)",
     "    close() { stopped = true; if (cur) cur.close(); }\n",
     "    nudge(t) { if (isReady && cur && cur.nudge) cur.nudge(t); },\n"
     "    close() { stopped = true; if (cur) cur.close(); }\n"),

    ("call timers",
     "  let streamSid = null, agent = null, cfg = null, from = '', callRef = null, startedAt = Date.now();\n  const transcript = [];\n",
     r"""  let streamSid = null, agent = null, cfg = null, from = '', callRef = null, startedAt = Date.now();
  const transcript = [];
  /* CALL_SAVINGS */
  const MAX_CALL_MS = Math.max(2, Number(process.env.MAX_CALL_MINUTES || 10)) * 60000;
  let lastVoice = Date.now(), lastOut = 0, playUntil = 0, talkOver = 0, floor = 300, nudged = 0;
  let wrapSent = false, byeAt = 0, watch = null, byeTimer = null;
  const preroll = [];
  const loud = (b64) => {                              // is the caller talking? (simple loudness check)
    const b = Buffer.from(b64, 'base64');
    if (!b.length) return false;
    let sum = 0;
    for (let i = 0; i < b.length; i++) { const v = ULAW_PCM[b[i]]; sum += v * v; }
    const rms = Math.sqrt(sum / b.length);
    const speech = rms > Math.max(450, floor * 3);
    if (!speech) floor = floor * 0.98 + rms * 0.02;
    return speech;
  };
  function hangUp(why) {
    if (byeAt) return;
    byeAt = Date.now();
    app.log.info(`Ending call (${why})`);
    const wait = () => {
      const now = Date.now();
      if ((now < playUntil + 400 || now - lastOut < 1500) && now - byeAt < 20000) { byeTimer = setTimeout(wait, 250); return; }
      if (streamSid) { try { twilio.send(JSON.stringify({ event: 'mark', streamSid, mark: { name: 'vc-bye' } })); } catch {} }
      byeTimer = setTimeout(() => { try { twilio.close(); } catch {} }, 3000);
    };
    byeTimer = setTimeout(wait, 700);
  }
  function startWatch() {
    lastVoice = Date.now();
    watch = setInterval(() => {
      if (byeAt || !agent) return;
      const now = Date.now();
      if (now - startedAt > MAX_CALL_MS) return hangUp('time limit');
      if (!wrapSent && now - startedAt > MAX_CALL_MS - 60000 && agent.nudge) {
        wrapSent = true;
        agent.nudge('(Note: this call is almost at its time limit. Politely wrap up now: offer to take a message if needed, say goodbye, then call end_call.)');
      }
      const quiet = now - Math.max(lastVoice, playUntil);
      if (quiet > 22000) {
        if (agent.nudge) agent.nudge('(Note: the caller is still silent. Say a short goodbye now, then call end_call.)');
        return hangUp('silence');
      }
      if (quiet > 11000 && !nudged && agent.nudge) {
        nudged = 1;
        agent.nudge('(Note: the caller has been silent for a while. Briefly ask if they are still there.)');
      }
    }, 1000);
  }
"""),

    ("hang up through the end_call tool",
     "        runTool: (name, args) => runTool(cfg, name, args, from),\n",
     "        runTool: (name, args) => name === 'end_call'\n"
     "          ? (hangUp('goodbye'), { ok: true, note: 'Hanging up when your goodbye finishes. Do not start anything new.' })\n"
     "          : runTool(cfg, name, args, from),\n"),

    ("know when Solana is talking",
     "        onAudio: (b64) => { if (streamSid) twilio.send(JSON.stringify({ event: 'media', streamSid, media: { payload: b64 } })); },\n"
     "        onClear: () => { if (streamSid) twilio.send(JSON.stringify({ event: 'clear', streamSid })); },\n",
     "        onAudio: (b64) => {\n"
     "          const now = Date.now();\n"
     "          lastOut = now;\n"
     "          playUntil = Math.max(now, playUntil) + Math.floor(b64.length * 3 / 4) / 8;   // 8 bytes = 1 ms of phone audio\n"
     "          if (streamSid) twilio.send(JSON.stringify({ event: 'media', streamSid, media: { payload: b64 } }));\n"
     "        },\n"
     "        onClear: () => { playUntil = Date.now(); if (streamSid) twilio.send(JSON.stringify({ event: 'clear', streamSid })); },\n"),

    ("skip quiet audio while Solana talks",
     "        onClose: () => { try { twilio.close(); } catch {} }\n      });\n"
     "    } else if (msg.event === 'media') {\n"
     "      if (agent) agent.sendAudio(msg.media.payload);\n"
     "    } else if (msg.event === 'stop') {\n",
     "        onClose: () => { try { twilio.close(); } catch {} }\n      });\n"
     "      startWatch();\n"
     "    } else if (msg.event === 'media') {\n"
     "      const p = msg.media.payload, now = Date.now(), speech = loud(p);\n"
     "      if (speech) { lastVoice = now; nudged = 0; }\n"
     "      if (!agent) return;\n"
     "      if (now < playUntil && !speech && now > talkOver) {   // Solana is talking, caller is quiet: don't pay to send it\n"
     "        preroll.push(p); if (preroll.length > 10) preroll.shift();\n"
     "        return;\n"
     "      }\n"
     "      if (speech && now < playUntil) talkOver = now + 1500;  // caller talking over her: send everything for a bit\n"
     "      while (preroll.length) agent.sendAudio(preroll.shift());\n"
     "      agent.sendAudio(p);\n"
     "    } else if (msg.event === 'mark') {\n"
     "      if (msg.mark && msg.mark.name === 'vc-bye') { try { twilio.close(); } catch {} }\n"
     "    } else if (msg.event === 'stop') {\n"),

    ("clean up timers",
     "  twilio.on('close', async () => {\n    if (agent) agent.close();\n",
     "  twilio.on('close', async () => {\n    clearInterval(watch); clearTimeout(byeTimer);\n    if (agent) agent.close();\n"),

    ("phone sound table",
     "function twilioToGemini(b64) {\n",
     "// u-law phone sample -> 16-bit level (used to tell when the caller is talking)\n"
     "const ULAW_PCM = new Int16Array(256);\n"
     "for (let i = 0; i < 256; i++) {\n"
     "  const u = ~i & 0xff;\n"
     "  const s = ((((u & 0x0f) << 3) + 0x84) << ((u >> 4) & 7)) - 0x84;\n"
     "  ULAW_PCM[i] = (u & 0x80) ? -s : s;\n"
     "}\n"
     "function twilioToGemini(b64) {\n"),
]


def find_folder() -> Path:
    cwd = Path.cwd()
    for c in [cwd, cwd / "vocallus-bridge", cwd.parent / "vocallus-bridge",
              Path(__file__).resolve().parent / "vocallus-bridge",
              Path(__file__).resolve().parent.parent / "vocallus-bridge",
              Path(r"C:\Users\Rayaan Arif\Downloads\vocallus-bridge")]:
        pkg = c / "package.json"
        if pkg.exists() and "vocallus-bridge" in pkg.read_text(encoding="utf-8"):
            return c
    print("error: couldn't find the vocallus-bridge folder.")
    sys.exit(1)


def run(cmd, cwd, check=True):
    exe = shutil.which(cmd[0])
    if not exe:
        print(f"error: {cmd[0]} not found.")
        sys.exit(1)
    print("  $ " + " ".join(cmd))
    r = subprocess.run([exe] + cmd[1:], cwd=cwd, text=True)
    if check and r.returncode != 0:
        sys.exit(r.returncode)
    return r.returncode


def apply(src):
    if DONE_MARKER in src:
        print("  [skip] already added")
        return src, []
    missing = [label for label, old, _ in EDITS if src.count(old) != 1]
    if missing:
        return None, missing
    for label, old, new in EDITS:
        src = src.replace(old, new, 1)
        print(f"  [ok]   {label}")
    return src, []


def main():
    folder = find_folder()
    server = folder / "server.js"
    run(["git", "pull"], folder, check=False)
    src = server.read_text(encoding="utf-8")
    print(f"\nBridge folder: {folder}\n")
    new, missing = apply(src)
    if missing:
        print("error: server.js doesn't look like the version this script expects.")
        print("       couldn't find: " + ", ".join(missing) + ". Nothing was changed.")
        sys.exit(1)
    if new != src:
        server.write_text(new, encoding="utf-8")

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(server)], text=True)
        if r.returncode != 0:
            print("error: server.js has a syntax error. Undo with:  git checkout -- server.js")
            sys.exit(1)
        print("  [ok]   server.js syntax check")

    print("\nPushing to GitHub -> Railway redeploys")
    run(["git", "add", "."], folder)
    run(["git", "commit", "-m", "Cheaper calls: hang up after goodbye, silence and length limits"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute, then make a test call to your Solana number.")


if __name__ == "__main__":
    main()
