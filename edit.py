#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stripe_webhook.py - turns a Stripe payment into an active plan.

Run from Downloads (or inside vocallus-bridge), after numbers_api.py:

    python stripe_webhook.py

Adds POST /stripe/webhook to the Railway server:
  checkout.session.completed      -> users/{uid}.plan = 'pro' ($14.99) or 'max' ($99.99)
                                     (uid comes from client_reference_id on the payment link)
  customer.subscription.deleted   -> plan = 'none'
  customer.subscription.updated   -> plan = 'none' if canceled / unpaid
Every request is checked with STRIPE_WEBHOOK_SECRET (Railway variable).
"""

import shutil
import subprocess
import sys
from pathlib import Path

MARKER = "/stripe/webhook"
ANCHOR = "const port = process.env.PORT || 8080;"

BLOCK = r"""/* ---------------- Stripe webhook ---------------- */
import crypto from 'node:crypto';

const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET;
const PLAN_BY_AMOUNT = { 1499: 'pro', 9999: 'max' };   // cents

// Keep the raw body so Stripe's signature can be checked.
app.removeContentTypeParser('application/json');
app.addContentTypeParser('application/json', { parseAs: 'buffer' }, (req, body, done) => {
  req.rawBody = body;
  if (!body || !body.length) return done(null, {});
  try { done(null, JSON.parse(body.toString('utf8'))); }
  catch (e) { e.statusCode = 400; done(e); }
});

function verifyStripe(raw, header) {
  if (!STRIPE_WEBHOOK_SECRET || !header || !raw) return false;
  const items = header.split(',');
  const t = (items.find(p => p.startsWith('t=')) || '').slice(2);
  const sigs = items.filter(p => p.startsWith('v1=')).map(p => p.slice(3));
  if (!t || !sigs.length) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > 300) return false;
  const expected = crypto.createHmac('sha256', STRIPE_WEBHOOK_SECRET)
    .update(`${t}.${raw.toString('utf8')}`).digest('hex');
  return sigs.some(s => s.length === expected.length &&
    crypto.timingSafeEqual(Buffer.from(s), Buffer.from(expected)));
}

app.post('/stripe/webhook', async (req, reply) => {
  if (!verifyStripe(req.rawBody, req.headers['stripe-signature'])) {
    app.log.warn('Stripe webhook: bad signature');
    return reply.code(400).send({ error: 'bad signature' });
  }
  if (!db) return reply.code(500).send({ error: 'database not configured' });
  const evt = req.body || {};
  const obj = (evt.data && evt.data.object) || {};
  try {
    if (evt.type === 'checkout.session.completed') {
      const uid = obj.client_reference_id;
      const plan = PLAN_BY_AMOUNT[obj.amount_total];
      if (!uid || !plan) {
        app.log.warn(`Stripe checkout without uid/plan (uid=${uid}, amount=${obj.amount_total})`);
      } else {
        await db.doc(`users/${uid}`).set({
          plan,
          stripeCustomerId: obj.customer || null,
          stripeSubscriptionId: obj.subscription || null,
          planUpdatedAt: admin.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
        app.log.info(`Plan ${plan} activated for ${uid}`);
      }
    } else if (evt.type === 'customer.subscription.deleted' ||
              (evt.type === 'customer.subscription.updated' &&
               ['canceled', 'unpaid', 'incomplete_expired'].includes(obj.status))) {
      const snap = await db.collection('users').where('stripeSubscriptionId', '==', obj.id).limit(1).get();
      if (!snap.empty) {
        await snap.docs[0].ref.set({
          plan: 'none',
          planUpdatedAt: admin.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
        app.log.info(`Plan cancelled for ${snap.docs[0].id}`);
      }
    }
  } catch (e) {
    app.log.error('Stripe webhook failed: ' + e.message);
    return reply.code(500).send({ error: 'failed' });
  }
  return { received: true };
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

    if "firebase-admin" not in src:
        print("error: run tenant_bridge.py first.")
        sys.exit(1)
    if MARKER in src:
        print("  [skip] Stripe webhook already added")
    elif ANCHOR not in src:
        print("error: couldn't find where to insert the webhook in server.js")
        sys.exit(1)
    else:
        server.write_text(src.replace(ANCHOR, BLOCK + ANCHOR, 1), encoding="utf-8")
        print("  [ok]   added /stripe/webhook")

    print("\nPushing to GitHub -> Railway redeploys")
    run(["git", "add", "."], folder)
    run(["git", "commit", "-m", "Stripe webhook"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Next: add STRIPE_WEBHOOK_SECRET in Railway Variables.")


if __name__ == "__main__":
    main()
