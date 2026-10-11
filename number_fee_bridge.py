#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
number_fee_bridge.py - a replacement phone number costs a one-time fee (default $5).

Run from your VP folder (it finds Downloads\\vocallus-bridge):

    python number_fee_bridge.py

Why: before this, a customer could delete their number and get a new one for free as often as
they liked - and every new number costs you money in Twilio.

What it does:
  - each account's FIRST number is included in the plan (free), like before
  - after that, getting another number charges a one-time fee to the card already on file
    (the one they pay their plan with), using your existing Stripe key - no new keys needed
  - the customer is asked to confirm the fee first; nothing is charged without that
  - if the card is declined, no number is bought; if Twilio fails after the charge, the fee
    is refunded automatically
  - unlinking a number you added by hand (like your own test number) doesn't count as a used number

Change the fee in Railway Variables: NEW_NUMBER_FEE_CENTS (500 = $5.00, 0 = free).

Safe to run twice. Pushes to GitHub so Railway redeploys.
"""

import shutil
import subprocess
import sys
from pathlib import Path

DONE_MARKER = "/* NUMBER_FEE */"

EDITS = [
    ("count numbers when one is deleted",
     "    numberReleasedAt: admin.firestore.FieldValue.serverTimestamp()\n  }, { merge: true });\n"
     "  app.log.info(`Number ${d.phoneNumber} ${released ? 'released' : 'unlinked'} for ${user.uid}`);\n",
     "    numberReleasedAt: admin.firestore.FieldValue.serverTimestamp(),\n"
     "    // only numbers bought through Vocallus count toward the free one\n"
     "    numbersBought: Number.isFinite(d.numbersBought) ? d.numbersBought : (d.numberSource === 'purchased' ? 1 : 0)\n"
     "  }, { merge: true });\n"
     "  app.log.info(`Number ${d.phoneNumber} ${released ? 'released' : 'unlinked'} for ${user.uid}`);\n"),

    ("fee check before buying",
     "  const phone = String((req.body && req.body.phoneNumber) || '');\n"
     "  if (!/^\\+1\\d{10}$/.test(phone)) return reply.code(400).send({ error: 'Invalid phone number.' });\n"
     "  try {\n"
     "    const r = await twilioApi('/IncomingPhoneNumbers.json', {\n",
     "  const phone = String((req.body && req.body.phoneNumber) || '');\n"
     "  if (!/^\\+1\\d{10}$/.test(phone)) return reply.code(400).send({ error: 'Invalid phone number.' });\n"
     "  /* NUMBER_FEE */\n"
     "  const prior = Number.isFinite(user.data.numbersBought) ? user.data.numbersBought : (user.data.numberReleasedAt ? 1 : 0);\n"
     "  let paid = null;\n"
     "  if (prior >= 1 && NEW_NUMBER_FEE > 0) {\n"
     "    if (!(req.body && req.body.confirmFee === true)) {\n"
     "      return reply.code(402).send({ needsFee: true, fee: NEW_NUMBER_FEE,\n"
     "        error: `Your plan includes one number. A new number is a one-time $${(NEW_NUMBER_FEE / 100).toFixed(2)}.` });\n"
     "    }\n"
     "    try { paid = await chargeNumberFee(user, prior, phone); }\n"
     "    catch (e) { return reply.code(402).send({ error: e.message }); }\n"
     "  }\n"
     "  try {\n"
     "    const r = await twilioApi('/IncomingPhoneNumbers.json', {\n"),

    ("remember how many numbers were bought",
     "      numberSource: 'purchased',\n      numberCreatedAt: admin.firestore.FieldValue.serverTimestamp()\n    }, { merge: true });\n"
     "    app.log.info(`Bought ${r.phone_number} for ${user.uid}`);\n"
     "    return { phoneNumber: r.phone_number };\n"
     "  } catch (e) {\n"
     "    return reply.code(502).send({ error: e.message });\n"
     "  }\n",
     "      numberSource: 'purchased',\n      numberCreatedAt: admin.firestore.FieldValue.serverTimestamp(),\n"
     "      numbersBought: prior + 1\n"
     "    }, { merge: true });\n"
     "    app.log.info(`Bought ${r.phone_number} for ${user.uid}` + (paid ? ` (fee ${paid.id})` : ''));\n"
     "    return { phoneNumber: r.phone_number, charged: paid ? paid.amount : 0 };\n"
     "  } catch (e) {\n"
     "    if (paid) {                                   // number failed after the charge: give the money back\n"
     "      try { await stripe.refunds.create({ payment_intent: paid.id }); app.log.info('Refunded number fee ' + paid.id); }\n"
     "      catch (re) { app.log.error('NUMBER FEE REFUND FAILED ' + paid.id + ': ' + re.message); }\n"
     "      return reply.code(502).send({ error: \"Couldn't get that number, so your $\" + (paid.amount / 100).toFixed(2) + ' was refunded. Try another number.' });\n"
     "    }\n"
     "    return reply.code(502).send({ error: e.message });\n"
     "  }\n"),

    ("charge the card on file",
     "/* ---------------- Stripe webhook ---------------- */\n",
     r"""/* ---------------- replacement number fee ---------------- */
const NEW_NUMBER_FEE = Math.max(0, Math.round(Number(process.env.NEW_NUMBER_FEE_CENTS ?? 500)));
async function chargeNumberFee(user, prior, phone) {
  if (typeof stripe === 'undefined' || !stripe) throw new Error('Payments are not set up yet. Please contact support.');
  const d = user.data;
  if (!d.stripeCustomerId) throw new Error('No card on file. Add a payment method in Billing first.');
  let pm = null;
  if (d.stripeSubscriptionId) {
    try { pm = (await stripe.subscriptions.retrieve(d.stripeSubscriptionId)).default_payment_method; } catch {}
  }
  if (!pm) {
    try { const c = await stripe.customers.retrieve(d.stripeCustomerId); pm = c.invoice_settings && c.invoice_settings.default_payment_method; } catch {}
  }
  if (!pm) {
    try { const l = await stripe.paymentMethods.list({ customer: d.stripeCustomerId, type: 'card', limit: 1 }); pm = l.data[0] && l.data[0].id; } catch {}
  }
  if (!pm) throw new Error('No card on file. Add a payment method in Billing first.');
  try {
    const pi = await stripe.paymentIntents.create({
      amount: NEW_NUMBER_FEE, currency: 'usd',
      customer: d.stripeCustomerId, payment_method: typeof pm === 'string' ? pm : pm.id,
      off_session: true, confirm: true,
      description: 'Vocallus - new phone number',
      metadata: { uid: user.uid, type: 'number_fee', previousNumbers: String(prior) }
    }, { idempotencyKey: `numfee-${user.uid}-${prior}-${phone}-${Math.floor(Date.now() / 60000)}` });   // no double charge on a double click
    if (pi.status !== 'succeeded') throw Object.assign(new Error('not completed'), { code: 'authentication_required' });
    app.log.info(`Number fee charged for ${user.uid}: ${pi.id}`);
    return pi;
  } catch (e) {
    if (e.code === 'authentication_required') throw new Error('Your bank wants to confirm this charge. Update your card in Billing, then try again.');
    throw new Error('Your card was declined' + (e.message ? ': ' + e.message : '.'));
  }
}

/* ---------------- Stripe webhook ---------------- */
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
    run(["git", "commit", "-m", "Replacement phone numbers cost a one-time fee"], folder, check=False)
    run(["git", "push"], folder)
    print("\nDONE. Give Railway about a minute.")


if __name__ == "__main__":
    main()
