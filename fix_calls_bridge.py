#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_calls_bridge.py - fixes the Test call and phone calls that answer then hang up.

Run from your VP folder or Downloads (it finds Downloads\\vocallus-bridge):

    python fix_calls_bridge.py

What it changes in server.js:
  1. Trusts https://vocallus.com and https://www.vocallus.com (the test call was being
     refused after the move from vocallus.netlify.app). Railway's ALLOWED_ORIGINS is still added on top.
  2. Backup AI voice model: if Google refuses the usual Gemini Live model (it now limits the
     2.5 models), the call switches to gemini-3.8-live automatically instead of hanging up,
     and remembers the one that works for the next calls.
  3. Same backup for summaries / test chat: gemini-2.5-flash -> gemini-3.8-flash.
  4. Sends the Google key in a header. New AI Studio keys (they start with "AQ.") are refused
     when sent the old way: "Request had invalid authentication credentials".
  5. Clear messages for quota / billing problems on the Google key.

Safe to run twice (and fine if you already ran domain_bridge.py). Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# (label, marker that means "already done", old text, new text)
EDITS = [
    ("trust vocallus.com", "/* SITE_DOMAINS */",
     "const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS ||\n"
     "  'https://vocallus.netlify.app,http://localhost:8080,http://127.0.0.1:5500')\n"
     "  .split(',').map(s => s.trim());\n",
     "/* SITE_DOMAINS */\n"
     "const ALLOWED_ORIGINS = [...new Set([\n"
     "  'https://vocallus.com', 'https://www.vocallus.com', 'https://vocallus.netlify.app',\n"
     "  'http://localhost:8080', 'http://127.0.0.1:5500',\n"
     "  ...String(process.env.ALLOWED_ORIGINS || '').split(',')\n"
     "].map(s => s.trim().replace(/\\/+$/, '')).filter(Boolean))];\n"),

    ("site address", "process.env.SITE_URL || 'https://vocallus.com'",
     "const SITE_URL = (process.env.SITE_URL || 'https://vocallus.netlify.app').replace(/\\/$/, '');",
     "const SITE_URL = (process.env.SITE_URL || 'https://vocallus.com').replace(/\\/$/, '');"),

    ("Gemini Live: one model per try", "function geminiAgentOnce(",
     "function geminiAgent(cfg, o) {\n  const ws = new WebSocket(GEMINI_URL + encodeURIComponent(cfg.key));",
     "function geminiAgentOnce(cfg, o, model) {\n  const ws = new WebSocket(GEMINI_URL + encodeURIComponent(cfg.key));"),
    ("Gemini Live: model name", "model: `models/${model}`,",
     "      model: `models/${MODEL}`,",
     "      model: `models/${model}`,"),

    ("Gemini Live: backup model", "/* LIVE_FALLBACK */",
     "function openaiAgent(cfg, o) {\n",
     r"""/* LIVE_FALLBACK */
// Try the usual Gemini Live model; if Google refuses it before the call starts, try the next one.
const LIVE_MODELS = [...new Set([MODEL, 'gemini-3.8-live', 'gemini-2.5-flash-native-audio-preview-12-2025'].filter(Boolean))];
let liveGood = null;
function geminiAgent(cfg, o) {
  const order = liveGood ? [liveGood, ...LIVE_MODELS.filter(m => m !== liveGood)] : LIVE_MODELS;
  let i = 0, cur = null, stopped = false, isReady = false;
  const buf = [];
  const start = () => {
    const model = order[i];
    cur = geminiAgentOnce(cfg, Object.assign({}, o, {
      onReady: () => {
        isReady = true;
        if (liveGood !== model) app.log.info('Gemini Live model in use: ' + model);
        liveGood = model;
        while (buf.length) cur.sendAudio(buf.shift());
        if (o.onReady) o.onReady();
      },
      onError: (m) => {
        if (isReady || i >= order.length - 1) { if (o.onError) o.onError(m); }
        else app.log.error(`Gemini ${model}: ${m}`);
      },
      onClose: (code, why) => {
        if (!stopped && !isReady && i < order.length - 1 && !/quota|billing|api key|unauthori|permission/i.test(why || '')) {
          app.log.error(`Gemini model ${model} refused (${code} ${why || ''}) - trying ${order[i + 1]}`);
          i++;
          return start();
        }
        if (!isReady) app.log.error(`Gemini Live failed (${code} ${why || ''})`);
        if (o.onClose) o.onClose(code, why);
      }
    }), model);
  };
  start();
  return {
    sendAudio(b64) { if (isReady) cur.sendAudio(b64); else if (buf.length < 100) buf.push(b64); },
    close() { stopped = true; if (cur) cur.close(); }
  };
}

function openaiAgent(cfg, o) {
"""),

    ("Gemini text: backup model", "/* TEXT_FALLBACK */",
     "async function geminiText(key, system, contents, tools) {\n",
     r"""/* TEXT_FALLBACK */
let textGood = null;
async function geminiText(key, system, contents, tools) {
  const order = [...new Set([textGood, TEXT_MODEL, 'gemini-3.8-flash'].filter(Boolean))];
  let last = null;
  for (const model of order) {
    try { const j = await geminiTextOnce(key, system, contents, tools, model); textGood = model; return j; }
    catch (e) { last = e; if (!/not found|not supported|no longer available|404/i.test(e.message)) throw e; }
  }
  throw last;
}
async function geminiTextOnce(key, system, contents, tools, model) {
"""),
    ("Gemini text: model name", "/models/${model}:generateContent",
     "`https://generativelanguage.googleapis.com/v1beta/models/${TEXT_MODEL}:generateContent?key=",
     "`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key="),

    ("Google key sent the new way (Live calls)", "/* KEY_HEADER */",
     "  const ws = new WebSocket(GEMINI_URL + encodeURIComponent(cfg.key));",
     "  /* KEY_HEADER */ const ws = new WebSocket(GEMINI_URL.replace(/\\?key=$/, ''), { headers: { 'x-goog-api-key': cfg.key } });"),
    ("Google key sent the new way (summaries / chat)", "/* KEY_HEADER_TEXT */",
     "    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,\n"
     "    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }",
     "    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, /* KEY_HEADER_TEXT */\n"
     "    { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': key }, body: JSON.stringify(body) }"),

    ("clear quota / billing messages", "/* KEY_ERRORS */",
     "const keyError = (provider, m) => /api key|unauthori|401|invalid.*key/i.test(m)\n"
     "  ? `Your ${provider === 'openai' ? 'OpenAI' : 'Google'} API key was rejected. Check it on the Solana page.` : m;",
     "/* KEY_ERRORS */\n"
     "const keyError = (provider, m) => /api key|unauthori|401|invalid.*key/i.test(m)\n"
     "  ? `Your ${provider === 'openai' ? 'OpenAI' : 'Google'} API key was rejected. Check it on the Solana page.`\n"
     "  : /quota|billing|exceeded|429|RESOURCE_EXHAUSTED/i.test(m)\n"
     "  ? `The ${provider === 'openai' ? 'OpenAI' : 'Google AI'} key is out of quota or needs billing turned on.` : m;"),
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
    out, missing, log = src, [], []
    for label, marker, old, new in EDITS:          # in order: later edits build on earlier ones
        if marker in out:
            log.append(f"  [skip] {label} (already done)")
        elif out.count(old) == 1:
            out = out.replace(old, new, 1)
            log.append(f"  [ok]   {label}")
        else:
            missing.append(label)
    if missing:
        return None, missing
    print("\n".join(log))
    return out, []


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
    run(["git", "commit", "-m", "Fix calls: new Google key format, trust vocallus.com, backup Gemini models"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute, then try the Test call and a phone call.")


if __name__ == "__main__":
    main()
