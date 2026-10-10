#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_voices_bridge.py - safer Max voices + a status check for the Solana page.

Run from Downloads (next to the vocallus-bridge folder), AFTER max_voices_bridge.py:

    python fix_voices_bridge.py

  - If ElevenLabs fails during a call (wrong key, voice not in your ElevenLabs account, out of credits),
    Solana switches to her normal voice instead of going silent.
  - Every call logs which voice it used (Railway -> Deployments -> View logs: "Agent for ...").
  - New GET /api/agent/status: the Solana page shows what your phone line will really use
    (number, AI, voice) and explains any problem.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/api/agent/status"
START = "// Mute the AI's own voice and speak its words with ElevenLabs instead.\nfunction withEleven(o, voiceId) {"
END = "function geminiAgent(cfg, o) {"

NEW = r"""// Mute the AI's own voice and speak its words with ElevenLabs instead.
// If ElevenLabs fails (bad key, voice not in your account...), the call falls back to the AI's own voice.
function withEleven(o, voiceId) {
  const fmt = o.io === 'phone' ? 'ulaw_8000' : 'pcm_24000';
  let tts = null, broken = false, held = [];
  const giveUp = (why) => {
    if (broken) return;
    broken = true;
    app.log.error(`ElevenLabs gave no audio (${why}) - using the default voice for the rest of this call`);
    const backlog = held; held = [];
    backlog.forEach(b => o.onAudio(b));
  };
  const current = () => {
    if (!tts) {
      const inst = elevenStream(voiceId, fmt, (b64) => {
        inst.gotAudio = true; held = [];
        o.onAudio(b64);
      }, () => {
        if (tts === inst) tts = null;
        if (inst.pushed && !inst.gotAudio && !inst.cancelled) giveUp('stream closed');
      });
      tts = inst;
    }
    return tts;
  };
  return Object.assign({}, o, {
    onAudio: (b64) => {
      if (broken) return o.onAudio(b64);
      if (held.length < 3000) held.push(b64);       // kept in case ElevenLabs fails this turn
    },
    onCaption: (who, text) => {
      if (o.onCaption) o.onCaption(who, text);
      if (!broken && who === 'agent' && text && text.trim()) { const t = current(); t.pushed = true; t.push(text); }
      else if (!broken && who === 'agent' && text && tts) tts.push(text);
    },
    onTurnEnd: () => { if (tts) { tts.end(); tts = null; } if (o.onTurnEnd) o.onTurnEnd(); },
    onClear: () => {
      held = [];
      if (tts) { tts.cancelled = true; tts.cancel(); tts = null; }
      if (o.onClear) o.onClear();
    }
  });
}

function openAgent(cfg, o) {
  const elevenId = ELEVEN_VOICES[cfg.voice];
  const useEleven = !!(elevenId && ELEVEN_KEY);
  app.log.info(`Agent for ${cfg.uid || 'default line'}: ${cfg.provider || 'gemini'}, voice=${cfg.voice || 'default'}` +
    (useEleven ? ' (ElevenLabs)' : (elevenId ? ' (ELEVENLABS_API_KEY missing - default voice)' : '')));
  if (useEleven) o = withEleven(o, elevenId);
  return (cfg.provider === 'openai' ? openaiAgent : geminiAgent)(cfg, o);
}

// What the server will actually use for this account - shown on the Solana page.
app.get('/api/agent/status', async (req, reply) => {
  const user = await requireUser(req, reply);
  if (!user) return reply;
  let cfg;
  try { cfg = await loadConfig(user.uid); } catch (e) { return reply.code(500).send({ error: 'Could not load your settings.' }); }
  const out = {
    plan: user.data.plan || 'none',
    phoneNumber: user.data.phoneNumber || '',
    provider: cfg.provider || 'gemini',
    aiReady: !!cfg.key,
    savedVoice: user.data.voice || 'default',
    voice: cfg.voice || 'default',
    engine: cfg.provider === 'openai' ? 'openai' : 'gemini',
    problem: ''
  };
  const eid = ELEVEN_VOICES[out.voice];
  if (eid) {
    out.engine = 'elevenlabs';
    if (!ELEVEN_KEY) out.problem = 'eleven-missing';
    else {
      try {
        const r = await fetch(`https://api.elevenlabs.io/v1/voices/${eid}`, { headers: { 'xi-api-key': ELEVEN_KEY } });
        if (!r.ok) {
          const body = await r.text().catch(() => '');
          if (/missing_permissions/i.test(body)) out.problem = '';            // key can't read voices; can't check
          else out.problem = r.status === 401 ? 'eleven-key' : 'eleven-voice';
        }
      } catch { out.problem = 'eleven-unreachable'; }
    }
  }
  return out;
});
"""


def find_folder() -> Path:
    cwd = Path.cwd()
    for c in [cwd, cwd / "vocallus-bridge",
              Path(__file__).resolve().parent / "vocallus-bridge",
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


def main():
    folder = find_folder()
    server = folder / "server.js"
    src = server.read_text(encoding="utf-8")
    print(f"Bridge folder: {folder}\n")

    if DONE_MARKER in src:
        print("  [skip] already added")
    else:
        if "/* ELEVEN_VOICES */" not in src:
            print("error: run max_voices_bridge.py first.")
            sys.exit(1)
        i = src.find(START)
        j = src.find(END, i + 1) if i != -1 else -1
        if i == -1 or j == -1:
            print("error: server.js doesn't look like the version this script expects. Nothing was changed.")
            sys.exit(1)
        src = src[:i] + NEW + "\n" + src[j:]
        server.write_text(src, encoding="utf-8")
        print("  [ok]   ElevenLabs falls back to the normal voice if it fails")
        print("  [ok]   calls log which voice they use")
        print("  [ok]   /api/agent/status for the Solana page")

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(server)], text=True)
        if r.returncode != 0:
            print("error: server.js has a syntax error. Undo with:  git checkout -- server.js")
            sys.exit(1)
        print("  [ok]   server.js syntax check")

    print("\nPushing to GitHub -> Railway redeploys")
    run(["git", "add", "."], folder)
    run(["git", "commit", "-m", "Voice fallback + agent status"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
