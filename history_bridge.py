#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
history_bridge.py - call details for History + stricter booking + business-only answers.

Run from your VP folder or Downloads (it finds Downloads\\vocallus-bridge), AFTER fix_voices_bridge.py:

    python history_bridge.py

What it changes in server.js:
  - Every action Solana takes on a call is saved on the call (checked availability, booked,
    took a message), so History can show it next to the full transcript.
  - Bookings remember which call made them.
  - Never books in the past or too soon: earliest slot is BOOKING_LEAD_MINUTES from now
    (Railway variable, default 30).
  - Solana spells the caller's name back letter by letter ("R-A-Y-A-A-N, is that right?")
    and confirms day, time and name before booking; fixes it if they say no.
  - Uses the "What does your business do?" answer (saved at sign-up / on the Solana page)
    and politely declines things that have nothing to do with the business.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* HISTORY_ACTIONS */"

EDITS = [
    ("business description from the account",
     "    business: u.company || '',\n",
     "    business: u.company || '',\n"
     "    about: String(u.businessDescription || '').slice(0, 1500),\n"),

    ("no bookings in the past or too soon",
     "async function freeSlots(cfg, dateStr) {\n",
     "const BOOKING_LEAD_MIN = Math.max(0, Number(process.env.BOOKING_LEAD_MINUTES || 30));\n"
     "async function freeSlots(cfg, dateStr) {\n"),
    ("lead time in the slot check",
     "  const now = Date.now();\n  const slots = [];\n",
     "  const now = Date.now() + BOOKING_LEAD_MIN * 60000;   // never in the past, never too soon\n  const slots = [];\n"),
    ("clearer 'no times' answer",
     "message: 'Fully booked that day.' }",
     "message: 'No open times left that day (it may already be over, or fully booked). Offer another day.' }"),

    ("bookings remember their call",
     "        source: 'ai',\n        createdAt: admin.firestore.FieldValue.serverTimestamp()\n",
     "        source: 'ai',\n        callId: cfg.callRef ? cfg.callRef.id : null,\n"
     "        createdAt: admin.firestore.FieldValue.serverTimestamp()\n"),

    ("save every action on the call",
     "async function runTool(cfg, name, args, callerPhone) {\n",
     r"""/* HISTORY_ACTIONS */
async function runTool(cfg, name, args, callerPhone) {
  const result = await runToolInner(cfg, name, args, callerPhone);
  if (cfg && cfg.callRef) {
    const a = { type: name, at: admin.firestore.Timestamp.now() };
    if (name === 'check_availability') {
      a.date = String(args.date || '');
      a.open = !!(result && result.open);
      a.times = (result && result.available_times) ? result.available_times.length : 0;
    } else if (name === 'book_appointment') {
      a.date = String(args.date || ''); a.time = (result && result.time) || String(args.time || '');
      a.name = String(args.customer_name || '').slice(0, 100); a.reason = String(args.reason || '').slice(0, 200);
      a.ok = !!(result && result.booked);
    } else if (name === 'take_message') {
      a.name = String(args.caller_name || '').slice(0, 100); a.ok = !!(result && result.saved);
    }
    cfg.callRef.set({ actions: admin.firestore.FieldValue.arrayUnion(a) }, { merge: true }).catch(() => {});
  }
  return result;
}
async function runToolInner(cfg, name, args, callerPhone) {
"""),

    ("business-only answers, spelled names, confirm before booking",
     "      ' Say times in 12-hour format like 2:30 PM.';\n  }\n  return s;\n}",
     "      ' Say times in 12-hour format like 2:30 PM.';\n"
     "    s += ' Before booking, always spell the caller\\'s name back letter by letter, for example \"So that is R-A-Y-A-A-N, is that right?\".'\n"
     "      + ' If they say no, ask them to spell it and spell it back again until they say yes.'\n"
     "      + ' Then repeat the day, date and time and only call book_appointment after they clearly say yes.'\n"
     "      + ' Never book a time in the past or a time check_availability did not return.';\n"
     "  }\n"
     "  if (cfg.about) {\n"
     "    s += `\\n\\nAbout the business: ${cfg.about}`;\n"
     "  }\n"
     "  s += '\\n\\nOnly help with things related to this business (its services, hours, appointments, and taking messages).'\n"
     "    + ' If someone asks for something unrelated, politely say you can only help with this business and offer to take a message.';\n"
     "  return s;\n}"),
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


def main():
    folder = find_folder()
    server = folder / "server.js"
    src = server.read_text(encoding="utf-8")
    print(f"Bridge folder: {folder}\n")

    if DONE_MARKER in src:
        print("  [skip] already added")
    else:
        if "function buildSystem(" not in src:
            print("error: run solana_live_bridge.py / providers_bridge.py first.")
            sys.exit(1)
        missing = [label for label, old, _ in EDITS if src.count(old) != 1]
        if missing:
            print("error: server.js doesn't look like the version this script expects.")
            print("       couldn't find: " + ", ".join(missing) + ". Nothing was changed.")
            sys.exit(1)
        for label, old, new in EDITS:
            src = src.replace(old, new, 1)
            print(f"  [ok]   {label}")
        server.write_text(src, encoding="utf-8")

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(server)], text=True)
        if r.returncode != 0:
            print("error: server.js has a syntax error. Undo with:  git checkout -- server.js")
            sys.exit(1)
        print("  [ok]   server.js syntax check")

    print("\nPushing to GitHub -> Railway redeploys")
    run(["git", "add", "."], folder)
    run(["git", "commit", "-m", "Call actions in History, stricter booking, business-only answers"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
