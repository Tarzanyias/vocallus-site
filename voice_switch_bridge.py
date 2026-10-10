#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_switch_bridge.py - change Solana's voice in the middle of a test call.

Run from your VP folder (it finds Downloads\\vocallus-bridge), AFTER fix_calls_bridge.py:

    python voice_switch_bridge.py

During a test call on the Solana page, picking another voice now switches it live:
the old voice fades out, a new AI session starts in the new voice with the conversation
so far, says one short line ("this is my new voice"), and carries on where it left off.
If the switch fails, the call keeps going in the old voice.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* DEMO_VOICE_SWITCH */"

OLD_VARS = "  let agent = null, live = false, cfg = null, uid = null, started = 0, timer = null, closed = false;\n"
NEW_VARS = ("  let agent = null, live = false, cfg = null, uid = null, started = 0, timer = null, closed = false;\n"
            "  let switching = false, hooks = null;   /* DEMO_VOICE_SWITCH */\n")

OLD_AGENT = """      agent = openAgent(cfg, {
        io: 'browser',
        tools: true,
        system: buildSystem(cfg, '', 'call'),
        greet: 'A caller just connected. Greet them warmly and ask how you can help.',
        runTool: (name, args) => runTool(cfg, name, args, ''),
        onReady: () => {
          live = true;
          started = Date.now();
          timer = setTimeout(() => end('limit'), Math.min(300, left) * 1000);
          send({ type: 'live', maxSec: Math.min(300, left), agentName: cfg.agentName });
        },
        onAudio: (b64) => send({ type: 'audio', data: b64 }),
        onClear: () => send({ type: 'clear' }),
        onTool: (name) => send({ type: 'tool', name }),
        onCaption: (who, text) => {
          addLine(transcript, who === 'caller' ? 'Caller' : cfg.agentName, text);
          send({ type: 'caption', who: who === 'caller' ? 'you' : 'agent', text });
        },
        onError: (msg) => send({ type: 'error', error: keyError(cfg.provider, msg) }),
        onClose: (code, why) => {
          if (closed) return;
          if (code !== 1000) {
            send({ type: 'error', error: code === 1007
              ? 'The AI connection dropped. Press Call again to keep testing.'
              : keyError(cfg.provider, why || 'The AI connection closed.') });
          }
          end('ai');
        }
      });
    } else if (m.type === 'audio' && live && agent && typeof m.data === 'string') {"""

NEW_AGENT = """      // Callbacks only act for the session that is currently live (a voice switch starts a second one).
      hooks = (box) => ({
        io: 'browser',
        tools: true,
        runTool: (name, args) => runTool(cfg, name, args, ''),
        onAudio: (b64) => { if (agent === box.ref) send({ type: 'audio', data: b64 }); },
        onClear: () => { if (agent === box.ref) send({ type: 'clear' }); },
        onTool: (name) => send({ type: 'tool', name }),
        onCaption: (who, text) => {
          if (agent !== box.ref) return;
          addLine(transcript, who === 'caller' ? 'Caller' : cfg.agentName, text);
          send({ type: 'caption', who: who === 'caller' ? 'you' : 'agent', text });
        },
        onError: (msg) => { if (agent === box.ref) send({ type: 'error', error: keyError(cfg.provider, msg) }); },
        onClose: (code, why) => {
          if (closed) return;
          if (agent !== box.ref) {                       // a voice switch that never got going
            if (box.onFail) box.onFail();
            return;
          }
          if (code !== 1000) {
            send({ type: 'error', error: code === 1007
              ? 'The AI connection dropped. Press Call again to keep testing.'
              : keyError(cfg.provider, why || 'The AI connection closed.') });
          }
          end('ai');
        }
      });
      const first = {};
      first.ref = agent = openAgent(cfg, Object.assign(hooks(first), {
        system: buildSystem(cfg, '', 'call'),
        greet: 'A caller just connected. Greet them warmly and ask how you can help.',
        onReady: () => {
          live = true;
          started = Date.now();
          timer = setTimeout(() => end('limit'), Math.min(300, left) * 1000);
          send({ type: 'live', maxSec: Math.min(300, left), agentName: cfg.agentName });
        }
      }));
    } else if (m.type === 'voice' && live && agent && cfg && hooks && !closed) {
      // Switch voice mid-call: start a new session in the new voice, then hand over.
      const want = String(m.voice || '');
      const allowed = want === 'default' || (['pro', 'max'].includes(cfg.plan) && ['female', 'male'].includes(want));
      if (!allowed || want === cfg.voice || switching) return send({ type: 'switched', voice: cfg.voice, same: true });
      switching = true;
      const oldVoice = cfg.voice, oldName = cfg.agentName;
      cfg.voice = want;
      if (m.agentName) cfg.agentName = String(m.agentName).slice(0, 40);
      const box = {};
      let done = false;
      const fail = () => {
        if (done) return;
        done = true; switching = false;
        cfg.voice = oldVoice; cfg.agentName = oldName;
        try { box.ref && box.ref.close(); } catch {}
        send({ type: 'switched', voice: oldVoice, failed: true });
      };
      box.onFail = fail;
      const guard = setTimeout(fail, 12000);
      const sofar = transcriptText(transcript).slice(-6000);
      box.ref = openAgent(cfg, Object.assign(hooks(box), {
        system: buildSystem(cfg, '', 'call') +
          '\\n\\nThis call is already in progress. The conversation so far:\\n' + (sofar || '(nothing yet)') +
          '\\n\\nContinue from where it left off. Do not greet the caller again or repeat yourself.',
        greet: 'The caller just switched you to a new voice. Say one short, natural sentence in your new voice ' +
          '(for example "Here is my new voice, how does this sound?"), then continue helping from where you left off.',
        onReady: () => {
          if (done) { try { box.ref.close(); } catch {} return; }
          done = true; switching = false; clearTimeout(guard);
          const old = agent;
          agent = box.ref;
          try { old.close(); } catch {}
          send({ type: 'switched', voice: want, agentName: cfg.agentName });
        }
      }));
    } else if (m.type === 'audio' && live && agent && typeof m.data === 'string') {"""


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
    missing = [n for n, o in (("test call variables", OLD_VARS), ("test call AI session", OLD_AGENT)) if src.count(o) != 1]
    if missing:
        return None, missing
    src = src.replace(OLD_VARS, NEW_VARS, 1).replace(OLD_AGENT, NEW_AGENT, 1)
    print("  [ok]   switch voice during a test call")
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
    run(["git", "commit", "-m", "Switch voice during a test call"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
