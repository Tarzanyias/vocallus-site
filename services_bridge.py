#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services_bridge.py - Solana books each kind of appointment for the right length.

Run from your VP folder (it finds Downloads\\vocallus-bridge):

    python services_bridge.py

Uses the "appointment types" list from the sign-up question / Solana page
(users/{uid}.services = [{name: "Cleaning", minutes: 30}, ...]):
  - Solana knows the services and how long each takes
  - she asks which one the caller wants, and only offers times with enough free room
  - the booking is saved with the right length and the service as its title
Without a list, everything works like before (your normal slot length).

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* SERVICES_LIST */"

EDITS = [
    ("read the list from the account",
     "    about: String(u.businessDescription || '').slice(0, 1500),\n",
     "    about: String(u.businessDescription || '').slice(0, 1500),\n"
     "    services: cleanServices(u.services),\n"),

    ("helpers", "async function freeSlots(cfg, dateStr) {\n",
     r"""/* SERVICES_LIST */
function cleanServices(list) {
  if (!Array.isArray(list)) return [];
  return list.map(x => ({ name: String((x && x.name) || '').trim().slice(0, 60),
                          minutes: Math.round(Number(x && x.minutes) || 0) }))
    .filter(x => x.name && x.minutes >= 5 && x.minutes <= 480).slice(0, 30);
}
function findService(cfg, name) {
  const list = (cfg && cfg.services) || [];
  if (!name || !list.length) return null;
  const n = String(name).toLowerCase().trim();
  return list.find(s => s.name.toLowerCase() === n) ||
         list.find(s => s.name.toLowerCase().includes(n) || n.includes(s.name.toLowerCase())) || null;
}
async function freeSlots(cfg, dateStr, minutes) {
"""),

    ("open times fit the service length",
     "  for (let t = toMin(h.open); t + cfg.len <= toMin(h.close); t += cfg.len) {\n"
     "    const s = zonedToUtc(dateStr, fromMin(t), cfg.tz).getTime();\n"
     "    const e = s + cfg.len * 60000;\n",
     "  const dur = Number(minutes) > 0 ? Number(minutes) : cfg.len;\n"
     "  const step = dur % cfg.len === 0 ? cfg.len : 15;\n"
     "  for (let t = toMin(h.open); t + dur <= toMin(h.close); t += step) {\n"
     "    const s = zonedToUtc(dateStr, fromMin(t), cfg.tz).getTime();\n"
     "    const e = s + dur * 60000;\n"),

    ("check_availability knows the service",
     "        properties: { date: { type: 'STRING', description: 'Date as YYYY-MM-DD' } },\n",
     "        properties: { date: { type: 'STRING', description: 'Date as YYYY-MM-DD' },\n"
     "                      service: { type: 'STRING', description: 'Which service the caller wants, if the business has a list' } },\n"),

    ("book_appointment knows the service",
     "          reason: { type: 'STRING', description: 'Short reason for the visit' }\n",
     "          reason: { type: 'STRING', description: 'Short reason for the visit' },\n"
     "          service: { type: 'STRING', description: 'Which service from the business list' }\n"),

    ("check uses the service length",
     "    if (name === 'check_availability') {\n      const r = await freeSlots(cfg, args.date);\n",
     "    if (name === 'check_availability') {\n"
     "      const svc = findService(cfg, args.service);\n"
     "      const r = await freeSlots(cfg, args.date, svc && svc.minutes);\n"),

    ("booking uses the service length",
     "      const time = normTime(args.time);\n      const r = await freeSlots(cfg, args.date);\n",
     "      const time = normTime(args.time);\n"
     "      const svc = findService(cfg, args.service);\n"
     "      const r = await freeSlots(cfg, args.date, svc && svc.minutes);\n"),
    ("booking end time",
     "      const end = new Date(start.getTime() + cfg.len * 60000);\n",
     "      const end = new Date(start.getTime() + ((svc && svc.minutes) || cfg.len) * 60000);\n"),
    ("booking title",
     "        title: args.reason || 'Appointment',\n",
     "        title: (svc && svc.name) || args.reason || 'Appointment',\n"),

    ("Solana knows the list",
     "  if (cfg.about) {\n    s += `\\n\\nAbout the business: ${cfg.about}`;\n  }\n",
     "  if (cfg.about) {\n    s += `\\n\\nAbout the business: ${cfg.about}`;\n  }\n"
     "  if (cfg.services && cfg.services.length) {\n"
     "    s += '\\n\\nServices you can book, and how long each takes: ' +\n"
     "      cfg.services.map(x => `${x.name} (${x.minutes} min)`).join(', ') + '.' +\n"
     "      ' Ask which service the caller wants before checking times, and pass its exact name as \"service\"' +\n"
     "      ' to check_availability and book_appointment. If they want something not on the list, take a message.';\n"
     "  }\n"),
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
    run(["git", "commit", "-m", "Appointment types with lengths"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
