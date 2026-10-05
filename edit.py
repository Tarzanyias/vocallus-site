#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit.py — Vocallus v2: checkout page, new pricing, demo banner, plan redirect.

Inserts the new block BEFORE the "# --- deepseek_python.py ---" and
"# --- smooth_fix.py ---" markers so those stay the outermost wrappers.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"

MARKER = "# --- vocallus_update_v2 ---"
INSERT_MARKERS = ["# --- deepseek_python.py ---", "# --- smooth_fix.py ---"]


OVERRIDE = r'''
# --- vocallus_update_v2 ---

import re as _re_v2

BRIDGE = "https://vocallus-bridge-production.up.railway.app"
STRIPE_PUBLISHABLE_KEY = "pk_live_51UMzQBBlomEBThpkMWidPnPgr0j25tV3TpUb15xe3IqzicOUhqiNiGycJqaO3VBzBYSVna4QBmRI5GlS7e8Qx8nZ00yQhomtn9"


# ===========================================================================
# PRICING — 2 plans, checkout redirect, current-plan disabled
# ===========================================================================

PRICING_INNER = """
        <div class="text-center max-w-[720px] mx-auto">
          <span class="inline-flex items-center rounded-full bg-[#111111] border border-[#111111] px-3.5 py-1.5 text-[13px] font-semibold text-white">Pricing</span>
          <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[44px] font-bold leading-[1.12] tracking-[-0.03em] text-[#111111]">Simple pricing that scales</h2>
          <p class="mt-5 text-[17px] leading-[1.6] text-[#55565B]">Two plans. Cancel anytime.</p>
        </div>
        <div class="mt-20 grid grid-cols-1 lg:grid-cols-2 gap-6 items-start max-w-[900px] mx-auto">
          <div class="rounded-3xl border border-gray-300 ring-2 ring-black/5 bg-white p-8 shadow-xs flex flex-col">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Pro</h3>
              <span class="inline-flex items-center rounded-full bg-[#111111] border border-[#111111] px-3 py-1 text-[12px] font-semibold text-white">Most popular</span>
            </div>
            <p class="mt-2.5 text-[15.5px] leading-[1.6] text-[#55565B]">Bring your own Gemini API key.</p>
            <div class="mt-6 flex items-end gap-1.5">
              <span class="text-[40px] font-extrabold leading-none tracking-[-0.04em] text-[#111111]">$14.99</span>
              <span class="pb-1 text-[14px] font-medium text-neutral-500">/ month</span>
            </div>
            <ul class="mt-7 space-y-3 flex-1">
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Bring your own Gemini API key</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>1 phone number</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Calendar booking</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Call history</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Up to 300 minutes / month</li>
            </ul>
            <div class="mt-8">
              <a href="#" data-plan-btn="pro" class="plan-btn btn-primary inline-flex w-full items-center justify-center px-6 py-3 rounded-xl font-bold text-[15.5px] tracking-[-0.01em] shadow-xs">Choose Pro</a>
            </div>
          </div>
          <div class="rounded-3xl border border-neutral-100 bg-white p-8 shadow-xs flex flex-col">
            <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Max</h3>
            <p class="mt-2.5 text-[15.5px] leading-[1.6] text-[#55565B]">AI included — no API key needed.</p>
            <div class="mt-6 flex items-end gap-1.5">
              <span class="text-[40px] font-extrabold leading-none tracking-[-0.04em] text-[#111111]">$99.99</span>
              <span class="pb-1 text-[14px] font-medium text-neutral-500">/ month</span>
            </div>
            <ul class="mt-7 space-y-3 flex-1">
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>AI included (no API key)</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>1 phone number</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Calendar booking</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Call history</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Up to 1,500 minutes / month</li>
              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]"><span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>Priority support</li>
            </ul>
            <div class="mt-8">
              <a href="#" data-plan-btn="max" class="plan-btn inline-flex w-full items-center justify-center px-6 py-3 rounded-xl font-bold text-[15.5px] border border-neutral-200 text-neutral-800 hover:bg-neutral-50 transition shadow-xs">Choose Max</a>
            </div>
          </div>
        </div>
"""

PRICING_JS = """
  <script>
    window.whenFirebase && window.whenFirebase(function (fb) {
      var plan = 'none', user = fb.auth.currentUser;
      function paint() {
        document.querySelectorAll('.plan-btn').forEach(function (b) {
          var p = b.dataset.planBtn;
          var lbl = p === 'pro' ? 'Choose Pro' : 'Choose Max';
          if (user && plan === p) {
            b.textContent = 'Current plan';
            b.classList.add('opacity-60','pointer-events-none');
            b.setAttribute('href','#');
          } else {
            b.textContent = lbl;
            b.classList.remove('opacity-60','pointer-events-none');
            b.setAttribute('href', user ? ('checkout.html?plan=' + p) : ('signup.html?plan=' + p));
          }
        });
      }
      fb.onAuthStateChanged(fb.auth, function (u) {
        user = u;
        if (!u) { plan = 'none'; paint(); return; }
        fb.onSnapshot(fb.doc(fb.db, 'users', u.uid), function (s) {
          plan = s.exists() ? (s.data().plan || 'none') : 'none';
          paint();
        });
      });
    });
  </script>
"""

def page_pricing(_ctx):
    return ("Pricing", "Simple pricing for Vocallus.",
            section_wrap("pricing", PRICING_INNER) + PRICING_JS, "")


# ===========================================================================
# CHECKOUT PAGE (new)
# ===========================================================================

CHECKOUT_BODY = """
      <div class="max-w-[1200px] mx-auto px-6 lg:px-12 py-16 w-full">
        <div class="mb-10">
          <a href="pricing.html" class="inline-flex items-center gap-1.5 text-[14px] font-medium text-neutral-500 hover:text-black transition">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            Back to pricing
          </a>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          <div class="lg:col-span-5">
            <div class="rounded-3xl border border-neutral-100 bg-white p-8 shadow-xs">
              <div class="text-[12px] font-semibold uppercase tracking-[0.08em] text-neutral-400 mb-3">Order summary</div>
              <div id="summary-title" class="text-[24px] font-bold tracking-tight text-[#111111]">Vocallus</div>
              <div id="summary-price" class="mt-1.5 text-[16px] font-medium text-neutral-500">—</div>
              <ul id="summary-features" class="mt-6 space-y-2.5"></ul>
              <div class="mt-6 pt-6 border-t border-neutral-100 text-[13px] text-neutral-500">
                Billed monthly. Cancel anytime.
              </div>
            </div>
          </div>
          <div class="lg:col-span-7">
            <div id="pay-wrap" class="rounded-3xl border border-neutral-100 bg-white p-8 shadow-xs">
              <div id="payment-element" class="min-h-[240px]"></div>
              <button id="pay-btn" class="btn-primary w-full mt-6 inline-flex items-center justify-center px-6 py-4 rounded-xl font-bold text-[16px] tracking-[-0.01em] shadow-sm">Subscribe</button>
              <div class="mt-4 flex items-center justify-center gap-2 text-[12.5px] text-neutral-400">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Payments secured by Stripe
              </div>
            </div>
            <div id="pay-status" class="hidden mt-6 rounded-2xl border p-5"></div>
          </div>
        </div>
      </div>
"""

CHECKOUT_JS = """
  <script src="https://js.stripe.com/v3/"></script>
  <script>
    window.requireAuth && window.requireAuth();
    (function () {
      var plan = (new URLSearchParams(location.search).get('plan') || '').toLowerCase();
      if (plan !== 'pro' && plan !== 'max') { location.replace('pricing.html'); return; }
      var PRICE = plan === 'pro' ? '$14.99/month' : '$99.99/month';
      var LABEL = plan === 'pro' ? 'Vocallus Pro' : 'Vocallus Max';
      var FEATS = plan === 'pro'
        ? ['Bring your own Gemini API key','1 phone number','Calendar booking','Call history','Up to 300 minutes / month']
        : ['AI included (no API key)','1 phone number','Calendar booking','Call history','Up to 1,500 minutes / month','Priority support'];
      var st = document.getElementById('summary-title');
      var sp = document.getElementById('summary-price');
      var su = document.getElementById('summary-features');
      if (st) st.textContent = LABEL;
      if (sp) sp.textContent = PRICE;
      if (su) {
        su.innerHTML = '';
        FEATS.forEach(function (f) {
          var li = document.createElement('li');
          li.className = 'flex items-start gap-2.5 text-[15px] text-[#55565B]';
          li.innerHTML = '<span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>' + f;
          su.appendChild(li);
        });
      }
      var pb = document.getElementById('pay-btn');
      if (pb) pb.textContent = 'Subscribe — ' + PRICE;

      function setStatus(kind, html) {
        var el = document.getElementById('pay-status');
        if (!el) return;
        el.classList.remove('hidden','border-green-200','bg-green-50','text-green-800','border-red-200','bg-red-50','text-red-800');
        if (kind === 'ok') el.classList.add('border-green-200','bg-green-50','text-green-800');
        if (kind === 'err') el.classList.add('border-red-200','bg-red-50','text-red-800');
        el.innerHTML = html;
      }

      window.whenFirebase && window.whenFirebase(async function (fb) {
        var user = fb.auth.currentUser;
        if (!user) return;
        var token = await user.getIdToken();
        var stripe = Stripe('%STRIPE_PK%');
        var r = await fetch('%BRIDGE%/api/billing/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({ plan: plan })
        });
        var data = await r.json().catch(function () { return {}; });
        if (!r.ok) { setStatus('err', 'Error: ' + (data.error || r.status)); return; }
        if (data.updated) {
          var pw = document.getElementById('pay-wrap');
          if (pw) pw.classList.add('hidden');
          setStatus('ok', '<div class="font-semibold">Your plan was changed to ' + (plan === 'pro' ? 'Pro' : 'Max') + '.</div><a href="dashboard.html" class="inline-block mt-3 font-semibold underline">Go to dashboard</a>');
          return;
        }
        if (!data.clientSecret) { setStatus('err', 'Error: ' + (data.error || 'Missing client secret')); return; }
        var elements = stripe.elements({
          clientSecret: data.clientSecret,
          appearance: {
            theme: 'stripe',
            variables: { colorPrimary: '#111111', colorText: '#111111', fontFamily: 'Plus Jakarta Sans, sans-serif', borderRadius: '12px' }
          },
          fonts: [{ cssSrc: 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600' }]
        });
        var payment = elements.create('payment', { layout: 'tabs' });
        payment.mount('#payment-element');
        var btn = document.getElementById('pay-btn');
        btn.addEventListener('click', async function () {
          btn.disabled = true;
          var orig = btn.textContent;
          btn.textContent = 'Processing…';
          var res = await stripe.confirmPayment({
            elements: elements,
            redirect: 'if_required',
            confirmParams: { return_url: 'https://vocallus.netlify.app/Pages/dashboard.html?paid=1' }
          });
          if (res.error) {
            setStatus('err', res.error.message || 'Payment failed');
            btn.disabled = false;
            btn.textContent = orig;
          } else {
            location.href = 'dashboard.html?paid=1';
          }
        });
      });
    })();
  </script>
""".replace("%STRIPE_PK%", STRIPE_PUBLISHABLE_KEY).replace("%BRIDGE%", BRIDGE)


def page_checkout(_ctx):
    return "Checkout", "Complete your Vocallus subscription.", CHECKOUT_BODY, ""


# ===========================================================================
# SIGNUP PLAN REDIRECT — replaces the signup JS so ?plan= goes to checkout
# ===========================================================================

SIGNUP_JS = """
  <script>
    window.redirectIfAuthed && window.redirectIfAuthed('dashboard.html');
    window.whenFirebase && window.whenFirebase(function (fb) {
      var errEl = document.getElementById('signup-error');
      function showErr(m) { errEl.textContent = m; errEl.classList.remove('hidden'); }
      function hideErr() { errEl.classList.add('hidden'); }
      var plan = (new URLSearchParams(location.search).get('plan') || '').toLowerCase();
      var DEST = (plan === 'pro' || plan === 'max') ? ('checkout.html?plan=' + plan) : 'dashboard.html';

      function ensureUserDoc(user, extra) {
        var ref = fb.doc(fb.db, 'users', user.uid);
        return fb.getDoc(ref).then(function (snap) {
          if (!snap.exists()) {
            return fb.setDoc(ref, {
              name: (extra && extra.name) || user.displayName || '',
              email: user.email || '',
              company: (extra && extra.company) || '',
              plan: 'none',
              agentName: 'Solana',
              systemPrompt: 'You are Solana, the friendly receptionist for our business. Greet callers warmly, ask how you can help, and keep every reply short and natural, like a real person on the phone. If they want an appointment, find a day and time that works, get their name, and confirm the day and time back to them. If you can\\'t help with something, offer to take a message and say someone will call them back.',
              createdAt: fb.serverTimestamp()
            });
          }
          return snap.data().name ? Promise.resolve() : fb.updateDoc(ref, { name: user.displayName || '' });
        });
      }

      document.getElementById('google-signup').addEventListener('click', function () {
        hideErr();
        fb.signInWithPopup(fb.auth, new fb.GoogleAuthProvider())
          .then(function (res) { return ensureUserDoc(res.user); })
          .then(function () { window.location.href = DEST; })
          .catch(function (e) { showErr(e.message || String(e)); });
      });

      document.getElementById('signup-form').addEventListener('submit', function (e) {
        e.preventDefault();
        hideErr();
        var name = this.name.value.trim();
        var email = this.email.value.trim();
        var company = this.company.value.trim();
        var pw = this.password.value;
        if (pw.length < 6) { showErr('Password must be at least 6 characters.'); return; }
        fb.createUserWithEmailAndPassword(fb.auth, email, pw)
          .then(function (cred) {
            return fb.updateProfile(cred.user, { displayName: name })
              .then(function () { return ensureUserDoc(cred.user, { name: name, company: company }); });
          })
          .then(function () { window.location.href = DEST; })
          .catch(function (e) { showErr(e.message || String(e)); });
      });
    });
  </script>
"""


# ===========================================================================
# DEMO / PAID BANNER on app pages
# ===========================================================================

BANNER_SNIPPET = """
  <div id="demo-banner" class="hidden w-full bg-black text-white text-[13.5px] py-2.5 px-4 items-center justify-center gap-3 z-50">
    <span>Demo mode — Upgrade for phone calls</span>
    <a href="pricing.html" class="font-semibold underline decoration-white/60 underline-offset-2 hover:decoration-white">Upgrade</a>
  </div>
  <div id="paid-banner" class="hidden w-full bg-green-600 text-white text-[13.5px] py-2.5 px-4 text-center z-50"></div>
  <script>
    window.whenFirebase && window.whenFirebase(function (fb) {
      fb.onAuthStateChanged(fb.auth, function (u) {
        if (!u) return;
        fb.onSnapshot(fb.doc(fb.db, 'users', u.uid), function (snap) {
          var plan = snap.exists() ? (snap.data().plan || 'none') : 'none';
          var active = (plan === 'pro' || plan === 'max');
          var d = document.getElementById('demo-banner');
          if (d) {
            d.classList.toggle('hidden', active);
            d.classList.toggle('flex', !active);
          }
          var params = new URLSearchParams(location.search);
          if (params.get('paid') === '1') {
            var p = document.getElementById('paid-banner');
            if (p) {
              p.classList.remove('hidden');
              if (active) {
                p.textContent = "You're on " + (plan === 'pro' ? 'Pro' : 'Max') + '!';
                setTimeout(function () { p.classList.add('hidden'); }, 4000);
                if (history.replaceState) {
                  history.replaceState(null, '', location.pathname + location.hash);
                }
              } else {
                p.textContent = 'Payment received — activating your plan…';
              }
            }
          }
        });
      });
    });
  </script>
"""

_APP_PAGES_V2 = {"dashboard.html", "solana.html", "calendar.html", "history.html"}

_prev_render_page_v2 = render_page

def render_page(path, builder):
    html = _prev_render_page_v2(path, builder)
    name = Path(path).name

    # Demo banner on every app page
    if name in _APP_PAGES_V2 and 'id="demo-banner"' not in html:
        m = _re_v2.search(r'<body[^>]*>', html)
        if m:
            html = html[:m.end()] + BANNER_SNIPPET + html[m.end():]

    # Checkout JS
    if name == "checkout.html" and 'js.stripe.com/v3' not in html:
        html = html.replace("</body>", CHECKOUT_JS + "\n</body>", 1)

    return html


# Rebind PAGES to include checkout + the new pricing
PAGES = [
    ("index.html",               page_index),
    ("Pages/products.html",      page_products),
    ("Pages/solutions.html",     page_solutions),
    ("Pages/pricing.html",       page_pricing),
    ("Pages/resources.html",     page_resources),
    ("Pages/login.html",         page_login),
    ("Pages/signup.html",        page_signup),
    ("Pages/talk-to-sales.html", page_talk_to_sales),
    ("Pages/dashboard.html",     page_dashboard),
    ("Pages/solana.html",        page_solana),
    ("Pages/history.html",       page_history),
    ("Pages/calendar.html",      page_calendar),
    ("Pages/checkout.html",      page_checkout),
]

# --- end vocallus_update_v2 ---
'''


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: {BUILD_PY} not found")
        return 1

    src = BUILD_PY.read_text(encoding="utf-8")

    if MARKER in src:
        print("  [skip] vocallus_update_v2 already present")
    else:
        insert_at = -1
        for m in INSERT_MARKERS:
            i = src.find(m)
            if i != -1:
                insert_at = i
                print(f"  [ok]   inserting before marker: {m}")
                break
        if insert_at == -1:
            insert_at = src.rfind('if __name__ == "__main__":')
            print("  [warn] no deepseek/smooth_fix marker — inserting before main guard")

        if insert_at == -1:
            print("error: could not find insertion point")
            return 1

        src = src[:insert_at] + OVERRIDE + "\n\n" + src[insert_at:]
        BUILD_PY.write_text(src, encoding="utf-8")
        print("  [ok]   inserted vocallus_update_v2 block")

    print("\nRunning build.py …\n")
    return subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())