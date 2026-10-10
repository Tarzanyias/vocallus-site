#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
number_release_bridge.py - lets a customer delete their Solana phone number.

Run from your VP folder (it finds Downloads\\vocallus-bridge):

    python number_release_bridge.py

Adds POST /api/numbers/release  {confirm: "DELETE"}  (signed-in user only):
  - a number bought through Vocallus is released in Twilio (so you stop paying for it)
  - a number you linked by hand (like your own test number) is only unlinked, never released
  - the account goes back to "Get a new number"; call history and calendar are kept

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/api/numbers/release"
PORT_ANCHOR = "const port = process.env.PORT || 8080;"

BLOCK = r"""/* ---------------- delete (release) the account's number ---------------- */
app.post('/api/numbers/release', async (req, reply) => {
  const user = await requireUser(req, reply);
  if (!user) return reply;
  if (!req.body || req.body.confirm !== 'DELETE') return reply.code(400).send({ error: 'Please confirm first.' });
  const d = user.data || {};
  if (!d.phoneNumber) return reply.code(404).send({ error: 'This account has no number.' });

  let released = false;
  if (d.twilioNumberSid && d.numberSource === 'purchased') {
    try {
      await twilioApi(`/IncomingPhoneNumbers/${d.twilioNumberSid}.json`, { method: 'DELETE' });
      released = true;
    } catch (e) {
      // Already gone in Twilio? Fine - just unlink it. Anything else: stop so we don't lose track of a paid number.
      if (!/404|not found|20404/i.test(e.message)) {
        app.log.error('Release number: ' + e.message);
        return reply.code(502).send({ error: "Couldn't release the number right now. Please try again." });
      }
    }
  }
  const del = admin.firestore.FieldValue.delete();
  await db.doc(`users/${user.uid}`).set({
    phoneNumber: del, twilioNumberSid: del, numberSource: del, numberCreatedAt: del,
    numberReleasedAt: admin.firestore.FieldValue.serverTimestamp()
  }, { merge: true });
  app.log.info(`Number ${d.phoneNumber} ${released ? 'released' : 'unlinked'} for ${user.uid}`);
  return { ok: true, released };
});

"""


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
    if "requireUser" not in src or "twilioApi" not in src or src.count(PORT_ANCHOR) != 1:
        return None, ["the place to add it"]
    print("  [ok]   added /api/numbers/release")
    return src.replace(PORT_ANCHOR, BLOCK + PORT_ANCHOR, 1), []


def main():
    folder = find_folder()
    server = folder / "server.js"
    run(["git", "pull"], folder, check=False)
    src = server.read_text(encoding="utf-8")
    print(f"\nBridge folder: {folder}\n")
    new, missing = apply(src)
    if missing:
        print("error: server.js doesn't look like the version this script expects. Nothing was changed.")
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
    run(["git", "commit", "-m", "Delete number"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
