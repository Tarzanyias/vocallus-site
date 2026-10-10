#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
account_bridge.py - lets a customer delete their Vocallus account.

Run from your VP folder or Downloads (it finds Downloads\\vocallus-bridge), AFTER billing_api.py:

    python account_bridge.py

Adds POST /api/account/delete  {confirm: "DELETE"}  (signed-in user only). In order:
  1. Cancels their Stripe subscription (so they're never charged again)
  2. Releases the phone number if it was bought through Vocallus (stops your Twilio charge)
  3. Deletes all their data: settings, calls, appointments, keys, alert tokens
  4. Deletes their login

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/api/account/delete"
PORT_ANCHOR = "const port = process.env.PORT || 8080;"

BLOCK = r"""/* ---------------- delete account ---------------- */
app.post('/api/account/delete', async (req, reply) => {
  const user = await requireUser(req, reply);
  if (!user) return reply;
  if (!req.body || req.body.confirm !== 'DELETE') return reply.code(400).send({ error: 'Type DELETE to confirm.' });
  const d = user.data || {};

  // 1. Stop billing first - if this fails, nothing else is touched.
  try {
    if (typeof stripe !== 'undefined' && stripe && d.stripeCustomerId) {
      const subs = await stripe.subscriptions.list({ customer: d.stripeCustomerId, status: 'all', limit: 20 });
      for (const s of subs.data) {
        if (!['canceled', 'incomplete_expired'].includes(s.status)) await stripe.subscriptions.cancel(s.id);
      }
    }
  } catch (e) {
    app.log.error('Delete account (Stripe): ' + e.message);
    return reply.code(502).send({ error: "Couldn't cancel your subscription, so nothing was deleted. Please try again." });
  }

  // 2. Release a number Vocallus bought for them.
  if (d.twilioNumberSid && d.numberSource === 'purchased') {
    try { await twilioApi(`/IncomingPhoneNumbers/${d.twilioNumberSid}.json`, { method: 'DELETE' }); }
    catch (e) { app.log.error('Delete account (Twilio): ' + e.message); }
  }

  // 3. All their data (user doc + calls, appointments, private keys, push tokens).
  try { await db.recursiveDelete(db.doc(`users/${user.uid}`)); }
  catch (e) {
    app.log.error('Delete account (data): ' + e.message);
    return reply.code(500).send({ error: "Your subscription was cancelled but your data couldn't be deleted. Please try again." });
  }

  // 4. Their login.
  try { await admin.auth().deleteUser(user.uid); }
  catch (e) { app.log.error('Delete account (auth): ' + e.message); }

  app.log.info(`Deleted account ${user.uid}`);
  return { deleted: true };
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


def main():
    folder = find_folder()
    server = folder / "server.js"
    src = server.read_text(encoding="utf-8")
    print(f"Bridge folder: {folder}\n")

    if DONE_MARKER in src:
        print("  [skip] already added")
    else:
        if "requireUser" not in src or src.count(PORT_ANCHOR) != 1:
            print("error: server.js doesn't look like the version this script expects. Nothing was changed.")
            sys.exit(1)
        src = src.replace(PORT_ANCHOR, BLOCK + PORT_ANCHOR, 1)
        server.write_text(src, encoding="utf-8")
        print("  [ok]   added /api/account/delete")

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(server)], text=True)
        if r.returncode != 0:
            print("error: server.js has a syntax error. Undo with:  git checkout -- server.js")
            sys.exit(1)
        print("  [ok]   server.js syntax check")

    print("\nPushing to GitHub -> Railway redeploys")
    run(["git", "add", "."], folder)
    run(["git", "commit", "-m", "Delete account"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
