#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
after_hours_bridge.py - teaches the phone bridge your business hours.

Run from Downloads (next to the vocallus-bridge folder):

    python after_hours_bridge.py

What it adds to server.js:
  - Solana always knows your business hours and whether you're open right now.
  - Outside your hours it follows what you picked on the Calendar page:
        Take a message  -> answers, says you're closed, takes name/number/reason
        Book for later  -> answers and books the next open time
        Forward         -> rings your phone instead (Solana doesn't answer)
        Play a message  -> says your closed message and hangs up
  - New take_message tool: messages are saved on the call, so they show in History.
  - Forwarded / closed calls are logged in History too.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* AFTER_HOURS helpers */"

EDITS = [
    # 1. loadConfig: read the after-hours settings
    ("loadConfig",
     "    business: u.company || ''\n  };",
     "    business: u.company || '',\n"
     "    afterHours: ['message', 'book', 'forward', 'closed'].includes(u.afterHours) ? u.afterHours : 'message',\n"
     "    afterHoursMessage: String(u.afterHoursMessage || '').slice(0, 400),\n"
     "    afterHoursForward: /^\\+1\\d{10}$/.test(u.afterHoursForward || '') ? u.afterHoursForward : ''\n"
     "  };"),

    # 2. helpers
    ("hours helpers",
     "/* ---------------- calendar ---------------- */",
     r"""/* AFTER_HOURS helpers */
const DAY_NAMES = { sun: 'Sunday', mon: 'Monday', tue: 'Tuesday', wed: 'Wednesday', thu: 'Thursday', fri: 'Friday', sat: 'Saturday' };
const WEEK_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
function nowInTz(tz) {
  const p = tzParts(new Date(), tz);
  const wd = new Intl.DateTimeFormat('en-US', { timeZone: tz, weekday: 'short' }).format(new Date()).slice(0, 3).toLowerCase();
  return { day: wd, min: (Number(p.hour) % 24) * 60 + Number(p.minute) };
}
function dayIsOpen(h) {
  return !!(h && !h.closed && h.open && h.close && toMin(h.close) > toMin(h.open));
}
function isOpenNow(cfg) {
  try {
    const n = nowInTz(cfg.tz);
    const h = cfg.hours[n.day];
    return dayIsOpen(h) && n.min >= toMin(h.open) && n.min < toMin(h.close);
  } catch { return true; }
}
function hoursText(cfg) {
  return WEEK_ORDER.map(k => {
    const h = cfg.hours[k];
    return DAY_NAMES[k] + ' ' + (dayIsOpen(h) ? to12(h.open) + ' to ' + to12(h.close) : 'closed');
  }).join('; ');
}
function nextOpenText(cfg) {
  try {
    const n = nowInTz(cfg.tz);
    const start = DAY_KEYS.indexOf(n.day);
    for (let i = 0; i < 8; i++) {
      const k = DAY_KEYS[(start + i) % 7];
      const h = cfg.hours[k];
      if (!dayIsOpen(h)) continue;
      if (i === 0 && n.min >= toMin(h.open)) continue;
      const when = i === 0 ? 'today' : i === 1 ? 'tomorrow' : DAY_NAMES[k];
      return `${when} at ${to12(h.open)}`;
    }
  } catch {}
  return '';
}
function closedGreeting(cfg) {
  if (cfg.afterHoursMessage) return cfg.afterHoursMessage;
  const next = nextOpenText(cfg);
  return `Thanks for calling${cfg.business ? ' ' + cfg.business : ''}. We're closed right now.` +
    (next ? ` We open again ${next}.` : '') + ' Please call back then. Goodbye.';
}
function hoursPrompt(cfg) {
  let s = `\n\nBusiness hours (${cfg.tz}): ${hoursText(cfg)}.`;
  if (isOpenNow(cfg)) {
    s += ' The business is OPEN right now.';
  } else {
    const next = nextOpenText(cfg);
    s += ` The business is CLOSED right now${next ? ' and opens again ' + next : ''}. Let the caller know early in the call.`;
    if (cfg.afterHours === 'book') {
      s += ' You can still help: book them into an upcoming open time with the calendar tools, or take a message.';
    } else {
      s += ' Offer to take a message so the team can call them back. If they ask, you can also book a time when the business is open.';
    }
    if (cfg.afterHoursMessage) s += ` Open the call with something close to: "${cfg.afterHoursMessage}"`;
  }
  s += " To take a message: get the caller's name, the best number to call back, and a short reason," +
    ' read it back to confirm, then call take_message.';
  return s;
}
async function logQuickCall(uid, from, status) {
  if (!db || !uid) return;
  try {
    await db.collection(`users/${uid}/calls`).add({
      from, status, durationSec: 0,
      startedAt: admin.firestore.FieldValue.serverTimestamp(),
      endedAt: admin.firestore.FieldValue.serverTimestamp()
    });
  } catch (e) { app.log.error('Call log failed: ' + e.message); }
}

/* ---------------- calendar ---------------- */"""),

    # 3. new tool declaration
    ("take_message tool",
     "        required: ['date', 'time', 'customer_name']\n      }\n    }\n  ]\n}];",
     "        required: ['date', 'time', 'customer_name']\n      }\n    },\n"
     "    {\n"
     "      name: 'take_message',\n"
     "      description: 'Save a message for the business. Call this after you have the caller\\'s name, callback number and message, and have read it back to them.',\n"
     "      parameters: {\n"
     "        type: 'OBJECT',\n"
     "        properties: {\n"
     "          caller_name: { type: 'STRING' },\n"
     "          callback_number: { type: 'STRING', description: 'Best number to call back' },\n"
     "          message: { type: 'STRING', description: 'What the caller needs, in a sentence or two' }\n"
     "        },\n"
     "        required: ['caller_name', 'message']\n"
     "      }\n"
     "    }\n  ]\n}];"),

    # 4. run the tool
    ("take_message handler",
     "    return { error: 'Unknown tool' };",
     "    if (name === 'take_message') {\n"
     "      const message = {\n"
     "        name: String(args.caller_name || '').slice(0, 100),\n"
     "        phone: String(args.callback_number || callerPhone || '').slice(0, 40),\n"
     "        reason: String(args.message || '').slice(0, 1000),\n"
     "        at: admin.firestore.Timestamp.now()\n"
     "      };\n"
     "      if (cfg.callRef) await cfg.callRef.set({ message }, { merge: true });\n"
     "      app.log.info(`Message taken for ${cfg.uid} from ${message.name}`);\n"
     "      return { saved: true };\n"
     "    }\n"
     "    return { error: 'Unknown tool' };"),

    # 5. route calls outside business hours
    ("after-hours routing",
     "      const cfg = await loadConfig(tenant.uid);\n      if (!cfg.key) {",
     "      const cfg = await loadConfig(tenant.uid);\n"
     "      if (!isOpenNow(cfg)) {\n"
     "        if (cfg.afterHours === 'closed') {\n"
     "          await logQuickCall(tenant.uid, from, 'after-hours');\n"
     "          return sayAndHang(reply, closedGreeting(cfg));\n"
     "        }\n"
     "        if (cfg.afterHours === 'forward' && cfg.afterHoursForward && cfg.afterHoursForward !== to) {\n"
     "          await logQuickCall(tenant.uid, from, 'forwarded');\n"
     "          return reply.type('text/xml').send(\n"
     "            '<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response>' +\n"
     "            `<Dial timeout=\"25\">${xml(cfg.afterHoursForward)}</Dial>` +\n"
     "            `<Say>${xml('Sorry, no one could pick up. Please call back during business hours. Goodbye.')}</Say>` +\n"
     "            '</Response>'\n"
     "          );\n"
     "        }\n"
     "      }\n"
     "      if (!cfg.key) {"),

    # 6. tell Gemini the hours
    ("hours in prompt",
     "        ' Speak like a real person on the phone and keep replies short.';",
     "        ' Speak like a real person on the phone and keep replies short.';\n"
     "      if (cfg.uid) system += hoursPrompt(cfg);"),

    # 7. let the tool reach the call log
    ("call ref for messages",
     "            from, startedAt: admin.firestore.FieldValue.serverTimestamp(), status: 'in-progress'\n          });",
     "            from, startedAt: admin.firestore.FieldValue.serverTimestamp(), status: 'in-progress'\n          });\n"
     "          cfg.callRef = callRef;"),
]


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
        print("  [skip] after-hours support is already in server.js")
    else:
        missing = [label for label, old, _ in EDITS if src.count(old) != 1]
        if missing:
            print("error: server.js doesn't look like the version this script expects.")
            print("       couldn't find: " + ", ".join(missing))
            print("       Nothing was changed.")
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
    run(["git", "commit", "-m", "Business hours + after-hours handling"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute, then call your number.")


if __name__ == "__main__":
    main()
