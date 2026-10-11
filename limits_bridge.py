#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
limits_bridge.py - monthly minute limits + forward calls to a backup number when a customer runs out.

Run from your VP folder (it finds Downloads\\vocallus-bridge):

    python limits_bridge.py

What it does:
  - counts each customer's call minutes for the month (every call rounds UP to a whole minute,
    like the phone bill) and compares them with the plan limit: Pro 1,000, Max 1,500
  - when a customer has used all their minutes, new calls ring their "Backup number"
    (Calendar page -> Business hours). If they haven't set one, it uses their after-hours
    forward number. If neither exists, the caller hears a short "can't take your call" message.
  - the owner gets one notification that month: "You've used all your minutes"
  - forwarded calls are capped at 15 minutes each so they can't run up the phone bill
  - if the usage check ever fails, calls go through as normal (nobody gets cut off by a glitch)

Change the limits without code: set PRO_MINUTES / MAX_MINUTES in Railway Variables.

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* MINUTE_LIMITS */"

EDITS = [
    ("backup number in the account settings",
     "    afterHoursForward: /^\\+1\\d{10}$/.test(u.afterHoursForward || '') ? u.afterHoursForward : ''\n  };\n",
     "    afterHoursForward: /^\\+1\\d{10}$/.test(u.afterHoursForward || '') ? u.afterHoursForward : '',\n"
     "    backupNumber: /^\\+1\\d{10}$/.test(u.backupNumber || '') ? u.backupNumber : ''\n  };\n"),

    ("minute counting",
     "async function logQuickCall(uid, from, status) {\n",
     r"""/* MINUTE_LIMITS */
const PLAN_MINUTES = { pro: Number(process.env.PRO_MINUTES || 1000), max: Number(process.env.MAX_MINUTES || 1500) };
const usageCache = new Map();

function monthOf(tz) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit' })
    .formatToParts(new Date()).map(x => [x.type, x.value]));
  return { key: `${p.year}-${p.month}`, start: zonedToUtc(`${p.year}-${p.month}-01`, '00:00', tz) };
}

// Minutes used this month in the business's time zone. Each call rounds up to a whole minute.
async function minutesUsed(uid, tz) {
  const m = monthOf(tz);
  const hit = usageCache.get(uid);
  if (hit && hit.key === m.key && Date.now() - hit.at < 30000) return { mins: hit.mins, key: m.key };
  const snap = await db.collection(`users/${uid}/calls`)
    .where('startedAt', '>=', admin.firestore.Timestamp.fromDate(m.start)).get();
  let mins = 0;
  snap.forEach(d => { mins += Math.ceil((Number(d.data().durationSec) || 0) / 60); });
  usageCache.set(uid, { at: Date.now(), mins, key: m.key });
  return { mins, key: m.key };
}

// true when this customer has used every minute their plan includes.
async function outOfMinutes(uid, cfg) {
  const limit = PLAN_MINUTES[cfg.plan] || 0;
  if (!limit || !db) return false;
  try {
    const { mins, key } = await minutesUsed(uid, cfg.tz);
    if (mins < limit) return false;
    const ref = db.doc(`users/${uid}`);
    const u = (await ref.get()).data() || {};
    if (u.limitNotified !== key) {                               // tell the owner once a month
      await ref.set({ limitNotified: key }, { merge: true });
      const where = cfg.backupNumber || (cfg.afterHours === 'forward' ? cfg.afterHoursForward : '');
      await notifyOwner(uid, "You've used all your minutes",
        `All ${limit} minutes for this month are used. ` + (where
          ? 'New calls now ring your backup number until your minutes reset.'
          : 'Add a backup number (Calendar > Business hours) so callers still reach you, or upgrade your plan.'));
    }
    app.log.info(`Out of minutes for ${uid}: ${mins}/${limit}`);
    return true;
  } catch (e) {
    app.log.error('Minute check failed (letting the call through): ' + e.message);
    return false;
  }
}

async function logQuickCall(uid, from, status) {
"""),

    ("send the call to the backup number",
     "      const cfg = await loadConfig(tenant.uid);\n",
     r"""      const cfg = await loadConfig(tenant.uid);
      if (await outOfMinutes(tenant.uid, cfg)) {
        const fwd = cfg.backupNumber || (cfg.afterHours === 'forward' ? cfg.afterHoursForward : '');
        if (fwd && fwd !== to) {
          await logQuickCall(tenant.uid, from, 'forwarded');
          return reply.type('text/xml').send(
            '<?xml version="1.0" encoding="UTF-8"?><Response>' +
            `<Dial timeout="25" timeLimit="900">${xml(fwd)}</Dial>` +
            `<Say>${xml('Sorry, no one could pick up. Please try again later. Goodbye.')}</Say>` +
            '</Response>'
          );
        }
        await logQuickCall(tenant.uid, from, 'out-of-minutes');
        return sayAndHang(reply, "Sorry, we can't take your call right now. Please try again later. Goodbye.");
      }
"""),
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
    run(["git", "commit", "-m", "Monthly minute limits and backup number"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
