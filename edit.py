#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_python.py (v7) - one script for all the site polish.
  v15: Checkout waits for sign-in and shows a loading form + clear errors; Delete account in Billing.
  v14.1: Picking a male voice renames Solana -> Solan (and back for female/default).
  v14: History: click a call -> transcript + what Solana did; clean black & white Google-style calendar;
       "What does your business do?" after sign-up + on the Solana page; dashboard tabs fade in.
  v13: Solana page shows what calls will really use (number, voice) and explains voice problems;
       clearer 'no numbers in that area code' message.
  v12: Max voices (Professional Male, Professional Female, Rustic Male) with a MAX tag + 'More voices coming soon'.
  v11.1: Pro upgrade box slides + fades in smoothly.
  v11: Voices: Solana (default, free) + Female and Male with a PRO tag. Demo accounts that pick
       a Pro voice get an Upgrade box -> pricing page (with a Back button). Samples come from
       make_voices.py (Audio/solana.mp3, pfmale.mp3, pmale.mp3); pictures Images/pfmale.png, pmale.png.
  v10: Voice picker (Female / Male with Play) under the system prompt; labels in normal case;
       provider badge just says "Connected". First run asks for a Gemini API key once to make
       Audio/pfemale.mp3 + Audio/pmale.mp3 ("Hello, I'm a voice on Vocallus.") and
       Images/pfemale.png + Images/pmale.png.
  v9.2: Pro bullet with the two key links no longer splits into columns.
  v9.1: Pricing/checkout: "Bring your own Google API key or OpenAI API key" (both linked).
  v9: Dashboard scrolls; AI provider = Gemini (Google) or ChatGPT (OpenAI), Claude removed (icon deleted);
      "Bring your own Google API key" links to AI Studio; checkout says "Secure payment";
      footer Contact column removed.
  v8: Real test call (talk in the browser) + test chat on the Solana page, using your prompt,
      hours and calendar; bell = "Allow alerts on Solana calls" (asked once after sign-up),
      call summaries in History; Save hours shows Saving -> Saved; Reset to default on the left.
  v7.3: Save hours creates your account record if it's missing; clearer rule errors.
  v7.2: Solana page shows only "Reset to default" under the prompt.
  v7.1: Demo mode banner is a small floating pill (no more big black box).
  v7: Calendar switches slide smoothly, "Copy Monday" removed, clearer save errors,
      Firebase helper restored on app pages (Save buttons, calendar, demo banner work),
      faster loading (local cache, parallel reads, fades twice as quick).
  v6: Number / Billing tabs open properly (no more bouncing to Home),
      Solana page: agent name + system prompt prefilled (edit freely, Reset to default),
      Calendar: Business hours + "When you're closed" at the top, saved for Solana,
      History shows messages Solana took.
  v5: History filter slides and works, "Call history appears here" when empty,
      Finances -> Billing (plan, minutes, placeholder card + invoices),
      dashboard "Recent call history will show here" when empty.

Run from the VP folder:

    python deepseek_python.py

Includes everything from the old deepseek_python.py AND smooth_fix.py
(you don't need to run smooth_fix.py anymore - this replaces it):

  Header / homepage
    - Signed out: Sign in | Talk to Sales | Try for free ; hero [Try for free] [Talk to Sales]
    - Signed in : Log out | [Dashboard] (solid black) ; hero [Try for free] [Dashboard] (outline)
    - Buttons fade in once sign-in state is known (no flicker)
  Login / signup
    - Page fades out the moment sign-in succeeds
  Dashboard
    - Greeting + banner stay blank, then fade in with your real name + calls today
    - Number tab rebuilt so it works: shows your number + forwarding, or Upgrade,
      or area-code search -> Choose -> buy
    - Empty recent calls: "Your recent calls will show here"
    - Page always scrolls
  History
    - Empty state: "This is where your call history shows"

Safe to run again. Undo with:  git checkout -- .
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"
MAIN_GUARD = 'if __name__ == "__main__":'

# Old blocks this script replaces.
OLD_BLOCKS = [
    ("# --- deepseek_python.py: header/hero auth buttons ---", "# --- end deepseek_python.py ---"),
    ("# --- smooth_fix.py ---", "# --- end smooth_fix.py ---"),
]

HEADER_DASH_CLS = "btn-primary inline-flex items-center justify-center px-5 py-2 rounded-xl font-semibold shadow-sm"
HERO_DASH_CLS = ("inline-flex items-center justify-center px-7 py-3.5 rounded-xl "
                 "font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 "
                 "text-neutral-800 hover:bg-neutral-50 transition")

SW_FILE = """// firebase-messaging-sw.js - shows Vocallus call alerts when the site isn't open.
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');
firebase.initializeApp({
  apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
  authDomain: "vocallus-aa81e.firebaseapp.com",
  projectId: "vocallus-aa81e",
  storageBucket: "vocallus-aa81e.firebasestorage.app",
  messagingSenderId: "997486177218",
  appId: "1:997486177218:web:7c4741dbd450549140845b"
});
firebase.messaging();
"""

OVERRIDE = r'''# --- deepseek_python.py: header/hero auth buttons ---
import re as _re_auth

_DP_FB = """
      const { initializeApp, getApps } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
      const app = getApps().length ? getApps()[0] : initializeApp({
        apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
        authDomain: "vocallus.com",
        projectId: "vocallus-aa81e",
        storageBucket: "vocallus-aa81e.firebasestorage.app",
        messagingSenderId: "997486177218",
        appId: "1:997486177218:web:7c4741dbd450549140845b"
      });
"""

# ======================= header / hero buttons =======================

_AUTH_BTN_CSS = """
  <style>
    /* AUTH_BTN_CSS_MARKER */
    [data-auth-swap], [data-auth-hide], [data-auth-logout] { opacity: 0; transition: opacity .12s ease; }
    html.auth-ready [data-auth-swap], html.auth-ready [data-auth-hide], html.auth-ready [data-auth-logout] { opacity: 1; }
    .auth-gone { display: none !important; }
    @media (prefers-reduced-motion: reduce) {
      [data-auth-swap], [data-auth-hide], [data-auth-logout] { transition: none; }
    }
  </style>
"""

_AUTH_BTN_JS = """
  <script type="module">
    /* AUTH_BTN_MARKER */
    const root = document.documentElement;
    const fallback = setTimeout(() => root.classList.add('auth-ready'), 1200);

    document.querySelectorAll('[data-auth-swap], [data-auth-logout]').forEach(a => {
      a.dataset.label = a.textContent.trim();
      a.dataset.href0 = a.getAttribute('href');
      a.dataset.cls0 = a.className;
    });

    let doSignOut = null;
    document.querySelectorAll('[data-auth-logout]').forEach(a => {
      a.addEventListener('click', async (e) => {
        if (a.dataset.mode !== 'logout' || !doSignOut) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        document.body.classList.add('is-leaving');
        try { await doSignOut(); } catch (err) {}
        window.location.reload();
      }, true);
    });

    function apply(user) {
      document.querySelectorAll('[data-auth-logout]').forEach(a => {
        if (user) { a.textContent = 'Log out'; a.setAttribute('href', '#'); a.dataset.mode = 'logout'; }
        else { a.textContent = a.dataset.label; a.setAttribute('href', a.dataset.href0); a.dataset.mode = ''; }
      });
      document.querySelectorAll('[data-auth-swap]').forEach(a => {
        if (user) { a.textContent = 'Dashboard'; a.setAttribute('href', a.dataset.dash); a.className = a.dataset.dashCls; }
        else { a.textContent = a.dataset.label; a.setAttribute('href', a.dataset.href0); a.className = a.dataset.cls0; }
      });
      document.querySelectorAll('[data-auth-hide]').forEach(el => el.classList.toggle('auth-gone', !!user));
      clearTimeout(fallback);
      requestAnimationFrame(() => root.classList.add('auth-ready'));
    }

    try {
""" + _DP_FB + """
      const { getAuth, onAuthStateChanged, signOut } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      const auth = getAuth(app);
      doSignOut = () => signOut(auth);
      onAuthStateChanged(auth, apply);
    } catch (e) {
      apply(null);
    }
  </script>
"""

# ======================= login / signup fade =======================

_DP_LOGIN_JS = """
  <script type="module">
    /* SF_LOGIN_MARKER */
    try {
""" + _DP_FB + """
      const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      onAuthStateChanged(getAuth(app), (user) => { if (user) document.body.classList.add('is-leaving'); });
    } catch (e) {}
  </script>
"""

# ======================= app pages: scrolling =======================

_DP_SCROLL_CSS = """
  <style>
    /* DP_SCROLL_CSS */
    body > * { min-height: 0; }
    main { min-height: 0 !important; overflow-y: auto !important; }
    #panel-home, #panel-number, #panel-finances { padding-bottom: 6rem; }
    /* Demo / paid banners: small floating pill instead of a giant black column */
    #demo-banner, #paid-banner {
      position: fixed !important; left: 50%; bottom: 20px; top: auto !important;
      transform: translateX(-50%); width: auto !important; max-width: calc(100vw - 32px);
      border-radius: 9999px; padding: 10px 18px !important; z-index: 60;
      box-shadow: 0 8px 24px rgba(0,0,0,.18); white-space: nowrap;
      animation: vcPillIn .2s ease-out both;
    }
    .vc-spin { animation: vcSpin .8s linear infinite; }
    @keyframes vcSpin { to { transform: rotate(360deg); } }
    .vd-dot { display: inline-block; margin-right: 2px; animation: vdBlink 1.2s infinite both; }
    .vd-dot:nth-child(2) { animation-delay: .2s; } .vd-dot:nth-child(3) { animation-delay: .4s; }
    @keyframes vdBlink { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }
    @keyframes vcPillIn { from { opacity: 0; transform: translate(-50%, 8px); } to { opacity: 1; transform: translate(-50%, 0); } }
    @media (prefers-reduced-motion: reduce) { #demo-banner, #paid-banner { animation: none; } }
  </style>
"""

# ======================= dashboard: greeting fade =======================

_DP_DASH_HEAD = """
  <script>document.documentElement.classList.add('dash-loading');</script>
  <style>
    /* SF_DASH_CSS */
    main > * { transition: opacity .15s ease; }
    html.dash-loading main > * { opacity: 0; }
    #panel-home h1, #banner-line { opacity: 0 !important; transition: opacity .2s ease !important; }
    html.greet-ready #panel-home h1, html.greet-ready #banner-line { opacity: 1 !important; }
    @media (prefers-reduced-motion: reduce) {
      main > *, #panel-home h1, #banner-line { transition: none !important; }
    }
  </style>
"""

_DP_DASH_JS = """
  <script type="module">
    /* SF_DASH_MARKER */
    const root = document.documentElement;
    const reveal = () => root.classList.remove('dash-loading');
    const showGreeting = () => root.classList.add('greet-ready');
    const fallback = setTimeout(() => { reveal(); showGreeting(); }, 2000);
    const greet = () => { const h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'; };

    try {
""" + _DP_FB + """
      const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      const { getFirestore, doc, getDoc, collection, query, where, getDocs, Timestamp } =
        await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
      const auth = getAuth(app), db = getFirestore(app);

      onAuthStateChanged(auth, async (user) => {
        if (!user) return;
        const h1 = document.querySelector('#panel-home h1');
        const banner = document.getElementById('banner-line');

        const start = new Date(); start.setHours(0, 0, 0, 0);
        const [userRes, callsRes] = await Promise.allSettled([
          getDoc(doc(db, 'users', user.uid)),
          getDocs(query(collection(db, 'users', user.uid, 'calls'), where('startedAt', '>=', Timestamp.fromDate(start))))
        ]);

        let name = '';
        if (userRes.status === 'fulfilled' && userRes.value.exists()) name = userRes.value.data().name || '';
        name = (name || user.displayName || (user.email || '').split('@')[0] || 'there').trim().split(' ')[0];
        if (h1) {
          h1.innerHTML = greet() + ', <span id="greeting-name"></span>';
          h1.querySelector('#greeting-name').textContent = name;
        }

        if (banner) {
          if (callsRes.status === 'fulfilled') {
            const n = callsRes.value.size;
            banner.textContent = n ? ('Solana answered ' + n + ' call' + (n === 1 ? '' : 's') + ' today') : 'No calls yet today';
          } else {
            const e = callsRes.reason || {};
            console.error('Vocallus calls:', e);
            banner.textContent = (e.code === 'permission-denied')
              ? 'Firestore rules are blocking call history - publish the rules that include "calls".'
              : 'No calls yet today';
          }
        }

        clearTimeout(fallback);
        requestAnimationFrame(() => { reveal(); requestAnimationFrame(showGreeting); });
      });
    } catch (e) {
      console.error('Vocallus dashboard:', e);
      reveal(); showGreeting();
    }
  </script>
"""

# ======================= dashboard: Number tab =======================

_DP_NUMBER_JS = """
  <script type="module">
    /* VN_NUMBER_MARKER */
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const panel = document.getElementById('panel-number');

    const fmt = (n) => {
      let d = String(n || '').replace(/\\D/g, '');
      if (d.length === 11 && d[0] === '1') d = d.slice(1);
      return d.length === 10 ? '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6) : (n || '');
    };
    const card = 'bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]';
    const FORWARD_HELP =
      '<div class="rounded-2xl bg-white border border-gray-200 p-5">' +
      '<div class="text-[13px] font-semibold text-gray-700 uppercase tracking-wide mb-2">How to forward</div>' +
      '<p class="text-[14px] leading-[1.6] text-gray-600">Turn on call forwarding from your current line to your Solana number. ' +
      'Most carriers: dial <span class="font-mono font-semibold text-gray-900">*72</span> then your Solana number, and ' +
      '<span class="font-mono font-semibold text-gray-900">*73</span> to turn it off. Some carriers differ — check with yours.</p></div>';

    if (panel) {
      // Old element ids kept (hidden) so the page's older scripts don't crash.
      const legacy = ['number-has','number-none','plan-required','plan-active','number-value','forward-from',
        'copy-number','save-forward','forward-saved','search-numbers','area-code','search-status',
        'search-results','switch-to-buy'].map(id => '<span id="' + id + '"></span>').join('');
      panel.innerHTML =
        '<div class="mb-8"><h1 class="text-[32px] font-semibold text-gray-900">Number</h1>' +
        '<p class="text-gray-500 text-[15px] mt-1">The phone number Solana answers.</p></div>' +
        '<div id="vn-body" style="opacity:0;transition:opacity .15s ease"></div>' +
        '<div hidden>' + legacy + '</div>';
      const body = document.getElementById('vn-body');
      const show = () => requestAnimationFrame(() => { body.style.opacity = '1'; });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, doc, onSnapshot, updateDoc } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const auth = getAuth(app), db = getFirestore(app);

        async function api(path, opts = {}) {
          const token = await auth.currentUser.getIdToken();
          let res;
          try {
            res = await fetch(BRIDGE + path, {
              ...opts,
              headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', ...(opts.headers || {}) }
            });
          } catch (e) { throw new Error("Couldn't reach the server. Try again in a moment."); }
          const j = await res.json().catch(() => ({}));
          if (!res.ok) throw new Error(j.error || ('Request failed (' + res.status + ')'));
          return j;
        }

        let lastKey = '';

        // ---------- Delete number: confirm popup (VN_DELETE_MARKER) ----------
        const dv = document.createElement('div');
        dv.className = 'fixed inset-0 z-[95] bg-black/40 flex items-center justify-center p-4';
        dv.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .2s ease';
        dv.innerHTML =
          '<div id="vn-dc" class="bg-white rounded-3xl w-full max-w-[440px] p-7" style="transform:translateY(10px) scale(.98);transition:transform .26s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.22)">' +
            '<div class="w-11 h-11 rounded-full bg-red-50 text-red-600 flex items-center justify-center mb-4">' +
              '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/><line x1="2" y1="2" x2="22" y2="22"/></svg></div>' +
            '<h3 class="text-[20px] font-semibold text-gray-900">Delete this number?</h3>' +
            '<p id="vn-dtext" class="text-[14px] text-gray-500 mt-2 leading-[1.6]"></p>' +
            '<div id="vn-derr" class="hidden mt-3 text-[13px] text-red-600"></div>' +
            '<div class="flex items-center justify-end gap-2 mt-6">' +
              '<button id="vn-dcancel" class="px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-800 hover:bg-gray-50 transition-colors">Cancel</button>' +
              '<button id="vn-dgo" class="min-w-[150px] px-5 py-2.5 rounded-xl text-[14px] font-semibold text-white transition-colors" style="background:#dc2626">Delete number</button>' +
            '</div>' +
          '</div>';
        document.body.appendChild(dv);
        const dcard = document.getElementById('vn-dc');
        let dBusy = false;
        function closeDelete() {
          if (dBusy) return;
          dv.style.opacity = '0'; dv.style.pointerEvents = 'none';
          dcard.style.transform = 'translateY(10px) scale(.98)';
        }
        function askDelete(d) {
          const n = '<b class="text-gray-900">' + fmt(d.phoneNumber) + '</b>';
          document.getElementById('vn-dtext').innerHTML = d.numberSource === 'purchased'
            ? 'Solana stops answering ' + n + ' right away and the number is released. You can’t get the same number back. Your calls and calendar stay.'
            : n + ' will be disconnected from your account and Solana stops answering it. Your calls and calendar stay.';
          document.getElementById('vn-derr').classList.add('hidden');
          const go = document.getElementById('vn-dgo');
          go.disabled = false; go.textContent = 'Delete number';
          dv.style.opacity = '1'; dv.style.pointerEvents = 'auto';
          requestAnimationFrame(() => { dcard.style.transform = 'none'; });
          setTimeout(() => document.getElementById('vn-dcancel').focus(), 60);
        }
        document.getElementById('vn-dcancel').onclick = closeDelete;
        dv.addEventListener('mousedown', (e) => { if (e.target === dv) closeDelete(); });
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && dv.style.pointerEvents === 'auto') closeDelete(); });
        document.getElementById('vn-dgo').onclick = async () => {
          const go = document.getElementById('vn-dgo'), err = document.getElementById('vn-derr');
          if (dBusy) return;
          dBusy = true; go.disabled = true; err.classList.add('hidden');
          go.innerHTML = '<span class="inline-flex items-center gap-2"><svg class="w-4 h-4" style="animation:vcSpin .8s linear infinite" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>Deleting…</span>';
          try {
            await api('/api/numbers/release', { method: 'POST', body: JSON.stringify({ confirm: 'DELETE' }) });
            dBusy = false; closeDelete();          // the page fades to "Get a new number" by itself
          } catch (e) {
            dBusy = false; go.disabled = false; go.textContent = 'Delete number';
            err.textContent = e.message; err.classList.remove('hidden');
          }
        };

        function renderHas(uid, d) {
          body.innerHTML =
            '<div class="' + card + ' mb-6">' +
              '<div class="text-[13px] text-gray-500 font-medium mb-2">Your Solana number</div>' +
              '<div class="flex items-center gap-3 flex-wrap">' +
                '<div id="vn-number" class="text-[32px] font-semibold text-gray-900 tracking-tight"></div>' +
                '<button id="vn-copy" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13px] font-semibold hover:bg-gray-50">Copy</button>' +
              '</div>' +
              '<p class="text-[14px] text-gray-500 mt-3">Solana answers this number 24/7.</p>' +
              '<div class="mt-6 pt-5 border-t border-gray-100 flex items-center justify-between gap-3 flex-wrap">' +
                '<span class="text-[13px] text-gray-500">No longer need this number?</span>' +
                '<button id="vn-del" class="px-3.5 py-2 rounded-lg text-[13px] font-semibold text-red-600 hover:bg-red-50 transition-colors">Delete number</button>' +
              '</div>' +
            '</div>' +
            '<div class="bg-[#f9fafb] rounded-3xl border border-gray-100 p-8">' +
              '<h2 class="text-[18px] font-semibold text-gray-900 mb-2">Keep your existing business number</h2>' +
              '<p class="text-[14px] text-gray-600 mb-5">Enter the number your customers already know, then forward it to your Solana number.</p>' +
              '<div class="flex items-center gap-3 flex-wrap mb-5">' +
                '<input id="vn-forward" type="tel" placeholder="(555) 123-4567" class="flex-1 min-w-[220px] rounded-xl border border-gray-200 px-4 py-3 text-[15px] focus:outline-none focus:border-gray-400 bg-white">' +
                '<button id="vn-save-forward" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Save</button>' +
              '</div>' + FORWARD_HELP +
              '<p id="vn-forward-msg" class="text-[13px] font-semibold mt-3"></p>' +
            '</div>';
          document.getElementById('vn-number').textContent = fmt(d.phoneNumber);
          document.getElementById('vn-del').onclick = () => askDelete(d);
          document.getElementById('vn-forward').value = d.forwardingFrom || '';
          document.getElementById('vn-copy').onclick = async (e) => {
            try { await navigator.clipboard.writeText(fmt(d.phoneNumber)); } catch (err) {}
            e.target.textContent = 'Copied';
            setTimeout(() => { e.target.textContent = 'Copy'; }, 1200);
          };
          document.getElementById('vn-save-forward').onclick = async () => {
            const msg = document.getElementById('vn-forward-msg');
            try {
              await updateDoc(doc(db, 'users', uid), { forwardingFrom: document.getElementById('vn-forward').value.trim() });
              msg.className = 'text-[13px] font-semibold mt-3 text-green-700'; msg.textContent = 'Saved.';
            } catch (err) {
              msg.className = 'text-[13px] font-semibold mt-3 text-red-600'; msg.textContent = 'Could not save: ' + err.message;
            }
            setTimeout(() => { msg.textContent = ''; }, 2000);
          };
        }

        function renderUpgrade() {
          body.innerHTML =
            '<div class="' + card + ' text-center p-10">' +
              '<h2 class="text-[22px] font-semibold text-gray-900 mb-2">Upgrade to get your Solana phone number</h2>' +
              '<p class="text-[15px] text-gray-500 mb-6">Pick a plan and you can choose a local number right here.</p>' +
              '<a href="pricing.html" class="btn-primary inline-flex items-center justify-center px-6 py-3 rounded-xl font-semibold text-[15px]">Upgrade</a>' +
            '</div>';
        }

        function renderBuy() {
          body.innerHTML =
            '<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">' +
              '<div class="' + card + '">' +
                '<h2 class="text-[18px] font-semibold text-gray-900 mb-2">Get a new number</h2>' +
                '<p class="text-[14px] text-gray-500 mb-5">Pick an area code and choose a number.</p>' +
                '<div class="flex items-center gap-3 mb-4">' +
                  '<input id="vn-area" type="text" inputmode="numeric" maxlength="3" placeholder="832" class="w-[120px] rounded-xl border border-gray-200 px-4 py-3 text-[15px] text-center tracking-widest focus:outline-none focus:border-gray-400">' +
                  '<button id="vn-search" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Search</button>' +
                '</div>' +
                '<div id="vn-status" class="text-[13px] text-gray-500 min-h-[20px]"></div>' +
                '<div id="vn-results" class="mt-3 space-y-2 max-h-[340px] overflow-y-auto custom-scrollbar"></div>' +
              '</div>' +
              '<div class="bg-[#f9fafb] rounded-3xl border border-gray-100 p-8">' +
                '<h2 class="text-[18px] font-semibold text-gray-900 mb-2">Use my existing number</h2>' +
                '<p class="text-[14px] text-gray-600 mb-5">Pick a Solana number on the left first. Then forward your current business line to it, and callers keep dialing the number they already know.</p>' +
                FORWARD_HELP +
              '</div>' +
            '</div>';

          const area = document.getElementById('vn-area');
          const btn = document.getElementById('vn-search');
          const status = document.getElementById('vn-status');
          const results = document.getElementById('vn-results');
          area.addEventListener('keydown', (e) => { if (e.key === 'Enter') btn.click(); });

          btn.onclick = async () => {
            const ac = area.value.trim();
            results.innerHTML = '';
            status.className = 'text-[13px] text-gray-500 min-h-[20px]';
            if (!/^\\d{3}$/.test(ac)) { status.textContent = 'Enter a 3-digit area code.'; return; }
            status.textContent = 'Searching…';
            btn.disabled = true;
            try {
              const j = await api('/api/numbers/search?areaCode=' + ac);
              const list = j.numbers || [];
              if (!list.length) { status.textContent = 'Twilio has no numbers left in ' + ac + ' right now. Try a nearby area code' + (['832', '281', '346', '713'].includes(ac) ? ' (Houston: 281, 346, 713 or 832).' : '.'); return; }
              status.textContent = list.length + ' number' + (list.length === 1 ? '' : 's') + ' available';
              list.forEach((n) => {
                const row = document.createElement('div');
                row.className = 'flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3';
                const left = document.createElement('div');
                const t = document.createElement('div');
                t.className = 'font-semibold text-[15px] text-gray-900';
                t.textContent = fmt(n.phoneNumber);
                const s = document.createElement('div');
                s.className = 'text-[12px] text-gray-500';
                s.textContent = [n.locality, n.region].filter(Boolean).join(', ');
                left.append(t, s);
                const choose = document.createElement('button');
                choose.className = 'vn-choose btn-primary px-4 py-2 rounded-lg font-semibold text-[13px]';
                choose.textContent = 'Choose';
                choose.onclick = async () => {
                  if (window.vcBusiness) { await window.vcBusiness.ensure('number'); }   // VO_ENSURE_NUMBER
                  if (!confirm('Get ' + fmt(n.phoneNumber) + ' as your Solana number?')) return;
                  document.querySelectorAll('.vn-choose').forEach(b => { b.disabled = true; b.style.opacity = '0.5'; });
                  btn.disabled = true;
                  status.textContent = 'Setting up your number…';
                  try {
                    await api('/api/numbers/buy', { method: 'POST', body: JSON.stringify({ phoneNumber: n.phoneNumber }) });
                    status.textContent = 'Done! Your number is ready.';
                  } catch (err) {
                    status.className = 'text-[13px] text-red-600 min-h-[20px]';
                    status.textContent = err.message;
                    document.querySelectorAll('.vn-choose').forEach(b => { b.disabled = false; b.style.opacity = ''; });
                    btn.disabled = false;
                  }
                };
                row.append(left, choose);
                results.appendChild(row);
              });
            } catch (err) {
              status.className = 'text-[13px] text-red-600 min-h-[20px]';
              status.textContent = err.message;
            } finally {
              btn.disabled = false;
            }
          };
        }

        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          onSnapshot(doc(db, 'users', user.uid), (snap) => {
            const d = snap.exists() ? snap.data() : {};
            const plan = d.plan || 'none';
            const key = d.phoneNumber ? 'has:' + d.phoneNumber : (plan === 'none' ? 'upgrade' : 'buy');
            if (key === lastKey) return;   // don't wipe what the user is typing
            lastKey = key;
            body.style.opacity = '0';
            setTimeout(() => {
              if (d.phoneNumber) renderHas(user.uid, d);
              else if (plan === 'none') renderUpgrade();
              else renderBuy();
              show();
            }, lastKey ? 120 : 0);
          }, (err) => {
            body.innerHTML = '<div class="' + card + ' text-red-600 text-[14px]">Could not load your number: ' + err.message + '</div>';
            show();
          });
        });
      } catch (e) {
        body.innerHTML = '<div class="' + card + ' text-[14px] text-gray-500">Could not load this page. Refresh to try again.</div>';
        show();
      }
    }
  </script>
"""

# ======================= shared call helpers =======================

_DP_CALL_HELPERS = """
    const fmtPhone = (n) => {
      let d = String(n || '').replace(/\\D/g, '');
      if (d.length === 11 && d[0] === '1') d = d.slice(1);
      return d.length === 10 ? '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6) : (n || 'Unknown caller');
    };
    const fmtDur = (s) => { s = Math.round(s || 0); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
    const tsOf = (c) => (c.startedAt && c.startedAt.toMillis) ? c.startedAt.toMillis() : 0;
    const ago = (ms) => {
      const s = Math.floor((Date.now() - ms) / 1000);
      if (s < 60) return 'just now';
      if (s < 3600) return Math.floor(s / 60) + ' min ago';
      if (s < 86400) return Math.floor(s / 3600) + ' hr ago';
      return Math.floor(s / 86400) + ' d ago';
    };
    const statusPill = (st) => {
      st = st || 'completed';
      if (st === 'completed') return ['Completed', 'bg-green-50 text-green-700'];
      if (st === 'in-progress' || st === 'in_progress') return ['In progress', 'bg-blue-50 text-blue-700'];
      if (st === 'forwarded') return ['Forwarded', 'bg-purple-50 text-purple-700'];
      if (st === 'after-hours') return ['After hours', 'bg-amber-50 text-amber-700'];
      return [st.replace(/[-_]/g, ' '), 'bg-gray-100 text-gray-600'];
    };
    const ICON = '<div class="w-14 h-14 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4">' +
      '<svg class="w-6 h-6 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>';
    const emptyBox = (title, sub, pad) =>
      '<div class="' + (pad || 'py-16') + ' text-center">' + ICON +
      '<p class="text-[16px] font-medium text-gray-700">' + title + '</p>' +
      '<p class="text-[13.5px] text-gray-400 mt-1">' + sub + '</p></div>';
"""

# ======================= dashboard: recent calls =======================

_DP_RECENT_JS = """
  <script type="module">
    /* VC_RECENT_MARKER */
""" + _DP_CALL_HELPERS + """
    const old = document.getElementById('call-list');
    if (old) {
      old.style.display = 'none';                      // older script can keep writing here, unseen
      const list = document.createElement('div');
      list.id = 'vc-list';
      list.className = 'flex flex-col';
      old.after(list);
      const search = document.getElementById('call-search');
      let calls = [], loaded = false;

      function render() {
        if (!loaded) return;
        const q = ((search && search.value) || '').replace(/\\D/g, '');
        let rows = q ? calls.filter(c => String(c.from || '').replace(/\\D/g, '').includes(q)) : calls;
        rows = rows.slice(0, 20);
        if (!rows.length) {
          list.innerHTML = q
            ? '<div class="py-12 text-center text-[14px] text-gray-400">No calls match that number.</div>'
            : emptyBox('Recent call history will show here', 'Call your Solana number to see it in action.');
          return;
        }
        list.innerHTML = '';
        rows.forEach(c => {
          const row = document.createElement('div');
          row.className = 'bg-white px-2 py-5 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors';
          row.addEventListener('click', () => { location.href = 'history.html#call=' + c.id; });
          row.innerHTML =
            '<div class="flex items-center gap-3 flex-wrap mb-1">' +
              '<div class="vc-num text-[15px] font-semibold text-gray-900"></div>' +
              '<div class="vc-ago text-[13px] text-gray-500"></div>' +
              '<span class="vc-st ml-auto text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"></span>' +
            '</div><div class="vc-dur text-[13px] text-gray-500"></div>' +
            '<div class="vc-sum hidden text-[13.5px] text-gray-700 mt-1.5 leading-[1.5]"></div>';
          const [label, cls] = statusPill(c.status);
          row.querySelector('.vc-num').textContent = fmtPhone(c.from);
          row.querySelector('.vc-ago').textContent = tsOf(c) ? ago(tsOf(c)) : '';
          row.querySelector('.vc-st').textContent = label;
          row.querySelector('.vc-st').className += ' ' + cls;
          row.querySelector('.vc-dur').textContent = 'Duration ' + (c.durationSec ? fmtDur(c.durationSec) : '—');
          if (c.summary) { const sm = row.querySelector('.vc-sum'); sm.textContent = c.summary; sm.classList.remove('hidden'); }
          list.appendChild(row);
        });
      }
      if (search) search.addEventListener('input', render);
      setTimeout(() => { if (!loaded) { loaded = true; render(); } }, 1500);

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, collection, onSnapshot } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const auth = getAuth(app), db = getFirestore(app);
        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          onSnapshot(collection(db, 'users', user.uid, 'calls'), (s) => {
            calls = s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => tsOf(b) - tsOf(a));
            loaded = true; render();
          }, (err) => {
            loaded = true;
            list.innerHTML = '<div class="py-12 text-center text-[14px] text-red-600">Could not load calls: ' + err.message + '</div>';
          });
        });
      } catch (e) { loaded = true; render(); }
    }
  </script>
"""

# ======================= history page =======================

_DP_HISTORY_JS = """
  <script type="module">
    /* VH_HISTORY_MARKER */
""" + _DP_CALL_HELPERS + """
    const old = document.getElementById('history-list');
    if (old) {
      old.style.display = 'none';
      const list = document.createElement('div');
      list.id = 'vh-list';
      list.className = 'space-y-3';
      old.after(list);

      // ---- sliding filter (All / Today / This week) ----
      const RANGES = [['all', 'All'], ['today', 'Today'], ['week', 'This week']];
      const toggle = document.createElement('div');
      toggle.className = 'relative inline-flex bg-gray-100 rounded-full p-1';
      toggle.innerHTML =
        '<span id="vh-pill" class="absolute top-1 bottom-1 left-0 rounded-full bg-white shadow-sm" ' +
        'style="width:0;transition:transform .28s cubic-bezier(.16,1,.3,1),width .28s cubic-bezier(.16,1,.3,1)"></span>' +
        RANGES.map(([r, l]) =>
          '<button type="button" data-r="' + r + '" class="vh-btn relative z-10 px-5 py-2 rounded-full text-[14px] font-medium text-gray-500 transition-colors outline-none focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-300">' + l + '</button>'
        ).join('');
      const oldBtn = document.querySelector('.hist-filter');
      if (oldBtn && oldBtn.parentElement) oldBtn.parentElement.replaceWith(toggle);
      else list.before(toggle);

      const pill = toggle.querySelector('#vh-pill');
      let range = 'all', calls = [], loaded = false;
      // ---- call detail drawer (click a call) ----
      const veil = document.createElement('div');
      veil.className = 'fixed inset-0 z-[80] bg-black/30';
      veil.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .2s ease';
      const drawer = document.createElement('aside');
      drawer.className = 'fixed top-0 right-0 bottom-0 z-[81] w-[460px] max-w-[100vw] bg-white flex flex-col';
      drawer.style.cssText += ';transform:translateX(100%);transition:transform .28s cubic-bezier(.16,1,.3,1);box-shadow:-12px 0 40px rgba(0,0,0,.12)';
      document.body.append(veil, drawer);
      let openId = null;
      const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
      const niceDate = (d) => { const m = String(d || '').match(/^(\\d{4})-(\\d{2})-(\\d{2})$/); if (!m) return d || '';
        return new Date(+m[1], +m[2] - 1, +m[3]).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }); };
      const ICONS = {
        check_availability: '<path d="M8 2v4M16 2v4M3 10h18"/><rect x="3" y="4" width="18" height="18" rx="2"/>',
        book_appointment: '<polyline points="20 6 9 17 4 12"/>',
        take_message: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
      };
      function actionText(a) {
        if (a.type === 'check_availability') return 'Checked open times for ' + niceDate(a.date) + (a.open ? (a.times ? ' · ' + a.times + ' free' : ' · none free') : ' · closed');
        if (a.type === 'book_appointment') return a.ok
          ? 'Booked ' + (a.reason || 'an appointment') + (a.name ? ' for ' + a.name : '') + ' on ' + niceDate(a.date) + ' at ' + a.time
          : 'Tried to book ' + niceDate(a.date) + ' at ' + (a.time || '?') + ' (not available)';
        if (a.type === 'take_message') return 'Took a message' + (a.name ? ' from ' + a.name : '');
        return a.type;
      }
      function closeDetail() {
        openId = null;
        veil.style.opacity = '0'; veil.style.pointerEvents = 'none';
        drawer.style.transform = 'translateX(100%)';
        if (location.hash.indexOf('#call=') === 0 && history.replaceState) history.replaceState(null, '', location.pathname);
      }
      function openDetail(c) {
        openId = c.id;
        const [label, cls] = statusPill(c.status);
        const when = tsOf(c) ? new Date(tsOf(c)).toLocaleString('en-US', { weekday: 'long', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '';
        const acts = (c.actions || []).slice().sort((x, y) => ((x.at && x.at.toMillis) ? x.at.toMillis() : 0) - ((y.at && y.at.toMillis) ? y.at.toMillis() : 0));
        const lines = Array.isArray(c.transcript) ? c.transcript : [];
        let h =
          '<div class="flex items-start justify-between gap-3 px-6 pt-6 pb-4 border-b border-gray-100">' +
            '<div><div class="text-[20px] font-semibold text-gray-900">' + esc(fmtPhone(c.from)) + '</div>' +
            '<div class="text-[13px] text-gray-500 mt-0.5">' + esc(when) + (c.durationSec ? ' · ' + fmtDur(c.durationSec) : '') + '</div>' +
            '<span class="inline-block mt-2 text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ' + cls + '">' + esc(label) + '</span></div>' +
            '<button data-x aria-label="Close" class="w-9 h-9 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-800 hover:bg-gray-100">' +
              '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
          '</div><div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">';
        if (c.summary) h += '<div><div class="text-[12px] font-semibold uppercase tracking-wide text-gray-400 mb-1.5">Summary</div>' +
          '<p class="text-[14.5px] leading-[1.55] text-gray-800">' + esc(c.summary) + '</p></div>';
        if (acts.length || (c.message && (c.message.reason || c.message.name))) {
          h += '<div><div class="text-[12px] font-semibold uppercase tracking-wide text-gray-400 mb-2">What ' + esc(agent) + ' did</div><div class="space-y-2">';
          acts.forEach(a => {
            const good = a.type !== 'book_appointment' || a.ok;
            h += '<div class="flex items-start gap-3 rounded-xl border border-gray-100 px-3.5 py-3">' +
              '<div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ' + (a.type === 'book_appointment' && a.ok ? 'bg-black text-white' : 'bg-gray-100 text-gray-700') + '">' +
              '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + (ICONS[a.type] || ICONS.check_availability) + '</svg></div>' +
              '<div class="flex-1 text-[13.5px] leading-[1.45] ' + (good ? 'text-gray-800' : 'text-gray-500') + '">' + esc(actionText(a)) +
              (a.type === 'book_appointment' && a.ok && a.date ? '<a href="calendar.html#date=' + esc(a.date) + '" class="block mt-1 text-[12.5px] font-semibold text-gray-900 underline underline-offset-2">Open in Calendar</a>' : '') +
              '</div></div>';
          });
          if (c.message && (c.message.reason || c.message.name)) {
            h += '<div class="rounded-xl bg-[#f9fafb] border border-gray-100 px-3.5 py-3 text-[13.5px] text-gray-700"><div class="font-semibold text-gray-900 mb-0.5">Message from ' +
              esc(c.message.name || 'caller') + (c.message.phone ? ' · ' + esc(fmtPhone(c.message.phone)) : '') + '</div>' + esc(c.message.reason || '') + '</div>';
          }
          h += '</div></div>';
        }
        h += '<div><div class="text-[12px] font-semibold uppercase tracking-wide text-gray-400 mb-2">Conversation</div>';
        if (!lines.length) {
          h += '<p class="text-[13.5px] text-gray-500">' + (c.status === 'in-progress' ? 'This call is still going. The conversation shows here when it ends.' : 'No transcript for this call.') + '</p>';
        } else {
          h += '<div class="space-y-3">';
          lines.forEach(l => {
            const me = l.who !== 'Caller';
            h += '<div class="flex ' + (me ? 'justify-end' : 'justify-start') + '"><div class="max-w-[82%]">' +
              '<div class="text-[11px] font-semibold text-gray-400 mb-0.5 ' + (me ? 'text-right' : '') + '">' + esc(me ? l.who : 'Caller') + '</div>' +
              '<div class="rounded-2xl px-3.5 py-2.5 text-[14px] leading-[1.5] ' + (me ? 'bg-black text-white rounded-tr-sm' : 'bg-gray-100 text-gray-900 rounded-tl-sm') + '">' + esc(l.text) + '</div></div></div>';
          });
          h += '</div>';
        }
        h += '</div></div>';
        drawer.innerHTML = h;
        drawer.querySelector('[data-x]').addEventListener('click', closeDetail);
        veil.style.opacity = '1'; veil.style.pointerEvents = 'auto';
        requestAnimationFrame(() => { drawer.style.transform = 'none'; });
        if (history.replaceState) history.replaceState(null, '', '#call=' + c.id);
      }
      veil.addEventListener('click', closeDetail);
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && openId) closeDetail(); });
      let agent = 'Solana';

      function movePill(animate) {
        const b = toggle.querySelector('.vh-btn[data-r="' + range + '"]');
        if (!b) return;
        if (!animate) pill.style.transition = 'none';
        pill.style.width = b.offsetWidth + 'px';
        pill.style.transform = 'translateX(' + b.offsetLeft + 'px)';
        if (!animate) requestAnimationFrame(() => { pill.style.transition = 'transform .28s cubic-bezier(.16,1,.3,1),width .28s cubic-bezier(.16,1,.3,1)'; });
        toggle.querySelectorAll('.vh-btn').forEach(x => {
          const on = x === b;
          x.classList.toggle('text-gray-900', on);
          x.classList.toggle('font-semibold', on);
          x.classList.toggle('text-gray-500', !on);
          x.classList.toggle('font-medium', !on);
        });
      }

      function render() {
        if (!loaded) return;
        const now = new Date();
        const day = new Date(now); day.setHours(0, 0, 0, 0);
        const week = new Date(day); week.setDate(week.getDate() - ((week.getDay() + 6) % 7));
        const from = range === 'today' ? day.getTime() : range === 'week' ? week.getTime() : 0;
        const rows = calls.filter(c => tsOf(c) >= from);
        list.style.opacity = '0';
        setTimeout(() => {
          if (!rows.length) {
            const sub = range === 'today' ? 'No calls today yet.'
                      : range === 'week' ? 'No calls this week yet.'
                      : 'Every call Solana answers shows up here with the caller, time, and length.';
            list.innerHTML = emptyBox('Call history appears here', sub, 'py-20');
          } else {
            list.innerHTML = '';
            rows.forEach(c => {
              const row = document.createElement('div');
              row.className = 'rounded-2xl border border-gray-100 bg-white p-5 hover:shadow-sm hover:border-gray-200 transition cursor-pointer';
              row.setAttribute('role', 'button');
              row.tabIndex = 0;
              row.addEventListener('click', () => openDetail(c));
              row.addEventListener('keydown', (e) => { if (e.key === 'Enter') openDetail(c); });
              row.innerHTML =
                '<div class="flex items-start gap-4">' +
                  '<div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center flex-shrink-0">' +
                    '<svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' +
                  '</div>' +
                  '<div class="flex-1 min-w-0">' +
                    '<div class="flex items-center gap-2 flex-wrap">' +
                      '<div class="vh-num font-semibold text-[15px] text-gray-900"></div>' +
                      '<span class="vh-st text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"></span>' +
                      '<div class="vh-when text-[12px] text-gray-400 ml-auto"></div>' +
                    '</div>' +
                    '<div class="vh-dur text-[13px] text-gray-500 mt-1"></div>' +
                    '<div class="vh-sum hidden text-[13.5px] text-gray-700 mt-2 leading-[1.5]"></div>' +
                    '<div class="vh-msg hidden mt-3 rounded-xl bg-[#f9fafb] border border-gray-100 p-3 text-[13.5px] text-gray-700"></div>' +
                  '</div>' +
                '</div>';
              const [label, cls] = statusPill(c.status);
              row.querySelector('.vh-num').textContent = fmtPhone(c.from);
              row.querySelector('.vh-st').textContent = label;
              row.querySelector('.vh-st').className += ' ' + cls;
              row.querySelector('.vh-when').textContent = tsOf(c)
                ? new Date(tsOf(c)).toLocaleString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
                : '';
              row.querySelector('.vh-dur').textContent = 'Duration ' + (c.durationSec ? fmtDur(c.durationSec) : '—');
              if (c.summary) { const sm = row.querySelector('.vh-sum'); sm.textContent = c.summary; sm.classList.remove('hidden'); }
              if (c.message && (c.message.reason || c.message.name)) {
                const m = row.querySelector('.vh-msg');
                m.classList.remove('hidden');
                const b = document.createElement('div');
                b.className = 'font-semibold text-gray-900 mb-0.5';
                b.textContent = 'Message from ' + (c.message.name || 'caller') + (c.message.phone ? ' · ' + fmtPhone(c.message.phone) : '');
                const t = document.createElement('div');
                t.textContent = c.message.reason || '';
                m.append(b, t);
              }
              list.appendChild(row);
            });
          }
          list.style.transition = 'opacity .1s ease';
          list.style.opacity = '1';
        }, 60);
      }

      toggle.querySelectorAll('.vh-btn').forEach(b => b.addEventListener('click', () => {
        range = b.dataset.r; movePill(true); render();
      }));
      requestAnimationFrame(() => movePill(false));
      window.addEventListener('resize', () => movePill(false));
      setTimeout(() => { if (!loaded) { loaded = true; render(); } }, 1500);

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, collection, onSnapshot } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const auth = getAuth(app), db = getFirestore(app);
        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js").then(m => {
            m.onSnapshot(m.doc(db, 'users', user.uid), (s) => { if (s.exists() && s.data().agentName) agent = s.data().agentName; }, () => {});
          });
          let first = true;
          onSnapshot(collection(db, 'users', user.uid, 'calls'), (s) => {
            calls = s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => tsOf(b) - tsOf(a));
            loaded = true; render();
            const want = openId || (first && location.hash.indexOf('#call=') === 0 ? location.hash.slice(6) : null);
            if (want) { const c = calls.find(x => x.id === want); if (c) openDetail(c); }
            first = false;
          }, (err) => {
            loaded = true;
            list.innerHTML = '<div class="py-12 text-center text-[14px] text-red-600">Could not load calls: ' + err.message + '</div>';
          });
        });
      } catch (e) { loaded = true; render(); }
    }
  </script>
"""

# ======================= dashboard: Billing tab =======================

_DP_BILLING_JS = """
  <script type="module">
    /* VB_BILLING_MARKER */
    const panel = document.getElementById('panel-finances');
    const PLANS = {
      none: { name: 'Demo', price: 'Free', limit: 0 },
      pro:  { name: 'Pro',  price: '$14.99 / month', limit: 3000 },
      max:  { name: 'Max',  price: '$99.99 / month', limit: 10000 }
    };
    if (panel) {
      const legacy = ['fin-plan', 'fin-minutes', 'fin-limit'].map(id => '<span id="' + id + '"></span>').join('');
      const box = 'bg-white rounded-3xl border border-gray-100 p-7 shadow-[0_2px_10px_rgba(0,0,0,0.04)]';
      const next = new Date(); next.setMonth(next.getMonth() + 1, 1);
      panel.innerHTML =
        '<div class="mb-8"><h1 class="text-[32px] font-semibold text-gray-900">Billing</h1>' +
        '<p class="text-gray-500 text-[15px] mt-1">Your plan, usage, payment method, and invoices.</p></div>' +
        '<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">' +
          // plan
          '<div class="' + box + '">' +
            '<div class="flex items-center justify-between mb-4">' +
              '<div class="text-[13px] text-gray-500 font-medium">Current plan</div>' +
              '<span id="vb-status" class="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">Demo</span>' +
            '</div>' +
            '<div id="vb-plan" class="text-[28px] font-semibold text-gray-900">Demo</div>' +
            '<div id="vb-price" class="text-[15px] text-gray-500 mt-1">Free</div>' +
            '<a id="vb-cta" href="pricing.html" class="btn-primary mt-6 inline-flex items-center justify-center px-5 py-3 rounded-xl font-semibold text-[14px]">Upgrade</a>' +
          '</div>' +
          // usage
          '<div class="' + box + '">' +
            '<div class="text-[13px] text-gray-500 font-medium mb-4">Minutes used this month</div>' +
            '<div class="text-[28px] font-semibold text-gray-900"><span id="vb-min">0</span>' +
            '<span class="text-[18px] text-gray-400 font-medium"> / <span id="vb-limit">0</span></span></div>' +
            '<div class="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden"><div id="vb-bar" class="h-full bg-black rounded-full" style="width:0%;transition:width .2s ease"></div></div>' +
            '<p class="text-[13px] text-gray-500 mt-3">Resets on ' + next.toLocaleDateString('en-US', { month: 'long', day: 'numeric' }) + '</p>' +
          '</div>' +
        '</div>' +
        '<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">' +
          // payment method (placeholder until Stripe is wired up)
          '<div class="' + box + '">' +
            '<div class="flex items-center justify-between mb-5">' +
              '<div class="text-[13px] text-gray-500 font-medium">Payment method</div>' +
              '<button disabled class="text-[13px] font-semibold text-gray-400 cursor-not-allowed">Update card · soon</button>' +
            '</div>' +
            '<div class="rounded-2xl p-5 text-white" style="background:linear-gradient(135deg,#111 0%,#3a3a3a 100%);max-width:340px">' +
              '<div class="flex items-center justify-between mb-8"><span class="text-[12px] font-semibold tracking-[0.15em] opacity-80">VOCALLUS</span>' +
              '<span class="w-9 h-6 rounded-md" style="background:linear-gradient(135deg,#d9d9d9,#9a9a9a)"></span></div>' +
              '<div class="font-mono text-[18px] tracking-[0.18em]">•••• •••• •••• ••••</div>' +
              '<div class="flex justify-between mt-4 text-[12px] opacity-70"><span id="vb-card-name">Cardholder</span><span>MM / YY</span></div>' +
            '</div>' +
            '<p id="vb-card-note" class="text-[13px] text-gray-500 mt-4">No card on file yet.</p>' +
          '</div>' +
          // invoices (placeholder)
          '<div class="' + box + '">' +
            '<div class="text-[13px] text-gray-500 font-medium mb-4">Invoices</div>' +
            '<div class="grid grid-cols-3 text-[12px] font-semibold uppercase tracking-wide text-gray-400 border-b border-gray-100 pb-2">' +
              '<span>Date</span><span>Amount</span><span class="text-right">Status</span></div>' +
            '<div class="py-10 text-center text-[14px] text-gray-400">Invoices will appear here after your first payment.</div>' +
          '</div>' +
        '</div>' +
        '<div hidden>' + legacy + '</div>';

      const $ = (id) => document.getElementById(id);
      let plan = 'none', minutes = 0;

      function paint() {
        const p = PLANS[plan] || PLANS.none;
        $('vb-plan').textContent = p.name;
        $('vb-price').textContent = p.price;
        const st = $('vb-status');
        st.textContent = plan === 'none' ? 'Demo' : 'Active';
        st.className = 'text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ' +
          (plan === 'none' ? 'bg-gray-100 text-gray-600' : 'bg-green-50 text-green-700');
        $('vb-cta').textContent = plan === 'none' ? 'Upgrade' : 'Change plan';
        $('vb-min').textContent = minutes;
        $('vb-limit').textContent = p.limit;
        $('vb-bar').style.width = (p.limit ? Math.min(100, minutes / p.limit * 100) : 0) + '%';
        $('vb-card-note').textContent = plan === 'none'
          ? 'No card on file yet.'
          : 'Your card is saved securely with Stripe. Card details will show here soon.';
      }
      paint();

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, doc, collection, onSnapshot } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const auth = getAuth(app), db = getFirestore(app);
        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          if (user.displayName) $('vb-card-name').textContent = user.displayName;
          onSnapshot(doc(db, 'users', user.uid), (snap) => {
            plan = (snap.exists() && snap.data().plan) || 'none';
            paint();
          });
          onSnapshot(collection(db, 'users', user.uid, 'calls'), (s) => {
            const start = new Date(); start.setDate(1); start.setHours(0, 0, 0, 0);
            let sec = 0;
            s.forEach(d => {
              const c = d.data();
              const t = (c.startedAt && c.startedAt.toMillis) ? c.startedAt.toMillis() : 0;
              if (t >= start.getTime()) sec += c.durationSec || 0;
            });
            minutes = Math.round(sec / 60);
            paint();
          });
        });
      } catch (e) {}
    }
  </script>
"""

# ======================= dashboard: tab router (works with Netlify pretty URLs) =======================

_DP_ROUTER_JS = """
  <script>
    /* VR_ROUTER_MARKER */
    (function () {
      if (!document.getElementById('panel-home')) return;
      function has(name) { return !!document.getElementById('panel-' + name); }
      var current = null;
      function activate(name) {
        if (!has(name)) name = 'home';
        var changed = current !== null && current !== name;
        current = name;
        document.querySelectorAll('.panel').forEach(function (p) {
          var on = p.id === 'panel-' + name;
          p.classList.toggle('hidden', !on);
          if (on && changed) {                       // fade + rise the new tab in
            p.style.transition = 'none'; p.style.opacity = '0'; p.style.transform = 'translateY(8px)';
            requestAnimationFrame(function () { requestAnimationFrame(function () {
              p.style.transition = 'opacity .22s ease, transform .22s cubic-bezier(.16,1,.3,1)';
              p.style.opacity = '1'; p.style.transform = 'none';
            }); });
          }
        });
        document.querySelectorAll('.app-tab[data-nav], .dash-tab[data-panel]').forEach(function (t) {
          var on = (t.dataset.nav || t.dataset.panel) === name;
          t.classList.toggle('bg-gray-200/80', on);
          t.classList.toggle('text-gray-900', on);
          t.classList.toggle('text-gray-500', !on);
          var bar = t.querySelector('.app-bar, .dash-bar');
          if (bar) { bar.classList.toggle('opacity-100', on); bar.classList.toggle('opacity-0', !on); }
        });
        var main = document.querySelector('main');
        if (main) main.scrollTop = 0;
      }
      function panelFromHref(href) {
        var m = String(href || '').match(/^(?:\\.\\/)?(?:dashboard(?:\\.html)?)?(?:#([\\w-]*))?$/);
        if (!m || href === '') return null;
        return m[1] || 'home';
      }
      // Capture phase: runs before every other click handler on the page,
      // so the old scripts can't send you to the home panel.
      document.addEventListener('click', function (e) {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var a = e.target.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href');
        if (href === '#') return;
        var name = panelFromHref(href);
        if (!name || !has(name)) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        activate(name);
        if (history.replaceState) history.replaceState(null, '', name === 'home' ? location.pathname : '#' + name);
      }, true);
      window.addEventListener('hashchange', function () {
        activate((location.hash || '').replace('#', '') || 'home');
      });
      function initial() { activate((location.hash || '').replace('#', '') || 'home'); }
      initial();
      window.addEventListener('load', initial);
      window.addEventListener('pageshow', initial);
    })();
  </script>
"""

# ======================= Solana page: prefilled agent name + system prompt =======================

_DP_SOLANA_JS = """
  <script type="module">
    /* VS_SOLANA_MARKER */
    const $ = (id) => document.getElementById(id);
    const nameIn = $('agent-name'), promptIn = $('system-prompt'), display = $('agent-name-display');

    const makePrompt = (agent, company) =>
      'You are ' + agent + ', the friendly AI receptionist for ' + (company || 'our business') + '. ' +
      'You answer the phone like a real person: warm, calm and to the point. Keep every reply to one or two short sentences.\\n\\n' +
      'What you do:\\n' +
      '- Greet the caller and find out their name and why they are calling.\\n' +
      '- Answer simple questions about the business. If you do not know something, say so honestly and never make things up.\\n' +
      '- Book appointments when someone asks, using the calendar.\\n' +
      '- If someone needs a person, take a message: their name, the best number to call back, and a short reason.\\n\\n' +
      'Always be polite and patient. Before the call ends, repeat back any booking or message so the caller knows it is handled.';

    if (nameIn && promptIn) {
      promptIn.classList.remove('resize-none');
      promptIn.style.resize = 'vertical';
      promptIn.style.minHeight = '260px';

      // Helper row under the prompt: status + "Reset to default"
      const row = document.createElement('div');
      row.className = 'flex items-center justify-start mt-2 text-[12px]';
      row.innerHTML = '<span id="vs-state" hidden></span>' +
        '<button type="button" id="vs-reset" class="font-semibold text-gray-600 hover:text-black underline underline-offset-2">Reset to default</button>';
      promptIn.insertAdjacentElement('afterend', row);
      const state = $('vs-state');

      let company = '';
      const currentDefault = () => makePrompt(nameIn.value.trim() || 'Solana', company);
      let lastDefault = '';
      const refreshState = () => {
        const n = promptIn.value.length;
        state.textContent = '';
      };

      function fill(d) {
        company = (d && d.company) || '';
        if (!nameIn.value.trim()) nameIn.value = (d && d.agentName) || 'Solana';
        if (display) display.textContent = nameIn.value.trim() || 'Solana';
        lastDefault = currentDefault();
        if (!promptIn.value.trim()) promptIn.value = (d && d.systemPrompt) || lastDefault;
        refreshState();
      }

      // Rename the agent -> if the prompt is still the default, update the name inside it too.
      nameIn.addEventListener('input', () => {
        const wasDefault = promptIn.value.trim() === lastDefault.trim();
        lastDefault = currentDefault();
        if (wasDefault) promptIn.value = lastDefault;
        if (display) display.textContent = nameIn.value.trim() || 'Solana';
        refreshState();
      });
      promptIn.addEventListener('input', refreshState);
      $('vs-reset').addEventListener('click', () => {
        lastDefault = currentDefault();
        promptIn.value = lastDefault;
        refreshState();
        promptIn.focus();
      });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, doc, onSnapshot } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const firstSnap = (ref) => new Promise((res) => { let un = null; un = onSnapshot(ref, (x) => { res(x.exists() ? x.data() : {}); setTimeout(() => un && un(), 0); }, () => res({})); });

        const auth = getAuth(app), db = getFirestore(app);
        onAuthStateChanged(auth, async (user) => {
          if (!user) return;
          let d = {};
          try { d = await firstSnap(doc(db, 'users', user.uid)); } catch (e) {}
          fill(d);
        });
      } catch (e) {
        fill({});
      }
    }
  </script>
"""

# ======================= Calendar: business hours + after-hours at the top =======================

_DP_HOURS_JS = """
  <script type="module">
    /* VK_HOURS_MARKER */
    const $ = (id) => document.getElementById(id);
    const DAYS = [['mon','Monday'],['tue','Tuesday'],['wed','Wednesday'],['thu','Thursday'],['fri','Friday'],['sat','Saturday'],['sun','Sunday']];
    const ZONES = [['America/New_York','Eastern'],['America/Chicago','Central'],['America/Denver','Mountain'],
      ['America/Phoenix','Arizona'],['America/Los_Angeles','Pacific'],['America/Anchorage','Alaska'],['Pacific/Honolulu','Hawaii']];
    const MODES = [
      ['message', 'Take a message', 'Solana answers, says you are closed, and takes their name, number and reason.'],
      ['book', 'Book for later', 'Solana answers and books them into your next open time.'],
      ['forward', 'Forward to my phone', 'The call rings your phone instead. Solana does not answer.'],
      ['closed', 'Play a message and hang up', 'Callers hear your closed message, then the call ends.']
    ];
    const to12 = (t) => { let [h, m] = t.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
    const toMin = (t) => { const [h, m] = String(t).split(':').map(Number); return h * 60 + m; };
    const e164 = (v) => { let d = String(v || '').replace(/\\D/g, ''); if (d.length === 11 && d[0] === '1') d = d.slice(1); return d.length === 10 ? '+1' + d : ''; };
    const fmtPhone = (v) => { const e = e164(v); if (!e) return v || ''; const d = e.slice(2); return '(' + d.slice(0,3) + ') ' + d.slice(3,6) + '-' + d.slice(6); };

    const oldGrid = $('hours-grid');
    const oldCard = oldGrid ? oldGrid.closest('.mt-8') || oldGrid.parentElement : null;
    if (oldCard) oldCard.style.display = 'none';           // old editor hidden (kept so older scripts don't crash)

    const wrap = document.querySelector('main > div');
    const header = wrap ? wrap.firstElementChild : null;
    if (wrap && header) {
      const card = document.createElement('section');
      card.id = 'vk-card';
      card.className = 'mb-8 rounded-3xl border border-gray-100 bg-white p-6 shadow-[0_2px_10px_rgba(0,0,0,0.04)]';
      card.style.opacity = '0';
      card.style.transition = 'opacity .15s ease';
      const sel = 'rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-[13px] focus:outline-none focus:border-gray-400';
      card.innerHTML =
        '<div class="flex items-start justify-between gap-4 flex-wrap mb-5">' +
          '<div><div class="flex items-center gap-2"><h2 class="text-[18px] font-semibold text-gray-900">Business hours</h2>' +
          '<span id="vk-now" class="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"></span></div>' +
          '<p class="text-[13.5px] text-gray-500 mt-0.5">Solana books inside these hours and follows your after-hours choice outside them.</p></div>' +
          '<div class="flex items-center gap-2 flex-wrap">' +
            '<label class="text-[12.5px] text-gray-500">Time zone <select id="vk-tz" class="' + sel + ' ml-1"></select></label>' +
            '<label class="text-[12.5px] text-gray-500">Slot <select id="vk-len" class="' + sel + ' ml-1">' +
              [15, 30, 45, 60, 90].map(n => '<option value="' + n + '">' + n + ' min</option>').join('') + '</select></label>' +
          '</div>' +
        '</div>' +
        '<div class="grid lg:grid-cols-2 gap-6">' +
          '<div>' +
            '<div id="vk-days" class="divide-y divide-gray-100 rounded-2xl border border-gray-100"></div>' +
          '</div>' +
          '<div>' +
            '<div class="text-[13px] font-semibold text-gray-900 mb-2">When you are closed</div>' +
            '<div id="vk-modes" class="space-y-2"></div>' +
            '<div id="vk-fwd-box" class="hidden mt-3">' +
              '<label class="block text-[12.5px] text-gray-500 mb-1">Forward calls to</label>' +
              '<input id="vk-fwd" type="tel" placeholder="(555) 123-4567" class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] focus:outline-none focus:border-gray-400">' +
            '</div>' +
            '<div id="vk-msg-box" class="mt-3">' +
              '<label class="block text-[12.5px] text-gray-500 mb-1">What Solana says when you are closed <span class="text-gray-400">(optional)</span></label>' +
              '<textarea id="vk-msg" rows="3" maxlength="400" class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[13.5px] leading-[1.5] focus:outline-none focus:border-gray-400"></textarea>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="flex items-center gap-3 mt-5">' +
          '<button id="vk-save" type="button" class="btn-primary min-w-[124px] inline-flex items-center justify-center px-5 py-2.5 rounded-xl font-semibold text-[13.5px]">Save hours</button>' +
          '<span id="vk-status" class="text-[13px]"></span>' +
        '</div>';
      header.insertAdjacentElement('afterend', card);

      let hours = {}, mode = 'message', tz = 'America/Chicago';
      const def = () => ({ open: '09:00', close: '17:00', closed: false });

      // ---- render ----
      const tzSel = $('vk-tz');
      function renderTz() {
        const list = ZONES.slice();
        if (!list.some(z => z[0] === tz)) list.push([tz, tz]);
        tzSel.innerHTML = list.map(z => '<option value="' + z[0] + '"' + (z[0] === tz ? ' selected' : '') + '>' + z[1] + '</option>').join('');
      }
      function renderDays() {
        const box = $('vk-days');
        box.innerHTML = '';
        DAYS.forEach(([k, label]) => {
          const h = hours[k];
          const row = document.createElement('div');
          row.className = 'flex items-center gap-3 px-4 py-2.5';
          row.innerHTML =
            '<div class="w-24 text-[13.5px] font-medium text-gray-900">' + label + '</div>' +
            '<button type="button" role="switch" class="vk-tog relative w-10 h-6 rounded-full flex-shrink-0" aria-label="Open on ' + label + '" ' +
              'style="transition:background-color .2s ease">' +
              '<span class="vk-knob absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow" ' +
              'style="transition:transform .2s cubic-bezier(.4,0,.2,1)"></span></button>' +
            '<div class="vk-times relative flex-1 h-8">' +
              '<div class="vk-open absolute inset-0 flex items-center gap-2" style="transition:opacity .15s ease">' +
                '<input type="time" data-f="open" value="' + h.open + '" class="vk-t ' + sel + '">' +
                '<span class="text-[12px] text-gray-400">to</span>' +
                '<input type="time" data-f="close" value="' + h.close + '" class="vk-t ' + sel + '">' +
              '</div>' +
              '<div class="vk-closed absolute inset-0 flex items-center text-[13px] text-gray-400" style="transition:opacity .15s ease">Closed</div>' +
            '</div>';
          box.appendChild(row);

          const tog = row.querySelector('.vk-tog'), knob = row.querySelector('.vk-knob');
          const openBox = row.querySelector('.vk-open'), closedBox = row.querySelector('.vk-closed');
          const paint = () => {
            const open = !hours[k].closed;
            tog.setAttribute('aria-checked', String(open));
            tog.style.backgroundColor = open ? '#000' : '#e5e7eb';
            knob.style.transform = 'translateX(' + (open ? '16px' : '0') + ')';
            openBox.style.opacity = open ? '1' : '0';
            openBox.style.pointerEvents = open ? 'auto' : 'none';
            closedBox.style.opacity = open ? '0' : '1';
          };
          paint();
          tog.addEventListener('click', () => { hours[k].closed = !hours[k].closed; paint(); dirty(); });
          row.querySelectorAll('.vk-t').forEach(i => i.addEventListener('change', () => { hours[k][i.dataset.f] = i.value; dirty(); }));
        });
      }
      function renderModes() {
        $('vk-modes').innerHTML = MODES.map(([k, t, d]) =>
          '<button type="button" data-m="' + k + '" class="vk-mode w-full text-left rounded-2xl border px-4 py-3 transition ' +
            (mode === k ? 'border-black ring-2 ring-black/10 bg-white' : 'border-gray-200 bg-white hover:border-gray-300') + '">' +
            '<div class="flex items-center gap-2"><span class="w-4 h-4 rounded-full border-2 flex items-center justify-center ' + (mode === k ? 'border-black' : 'border-gray-300') + '">' +
            (mode === k ? '<span class="w-2 h-2 rounded-full bg-black"></span>' : '') + '</span>' +
            '<span class="text-[14px] font-semibold text-gray-900">' + t + '</span></div>' +
            '<div class="text-[12.5px] text-gray-500 mt-0.5 ml-6">' + d + '</div></button>').join('');
        $('vk-modes').querySelectorAll('.vk-mode').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; renderModes(); dirty(); }));
        $('vk-fwd-box').classList.toggle('hidden', mode !== 'forward');
        $('vk-msg-box').classList.toggle('hidden', mode === 'forward');
        $('vk-msg').placeholder = sampleMsg();
      }
      function nextOpen() {
        // Find the next opening time in the business's time zone.
        const now = new Date();
        const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: tz, hour12: false, weekday: 'short', hour: '2-digit', minute: '2-digit' })
          .formatToParts(now).map(p => [p.type, p.value]));
        const dayIdx = ['sun','mon','tue','wed','thu','fri','sat'].indexOf(parts.weekday.slice(0, 3).toLowerCase());
        const nowMin = (Number(parts.hour) % 24) * 60 + Number(parts.minute);
        const names = { sun:'Sunday', mon:'Monday', tue:'Tuesday', wed:'Wednesday', thu:'Thursday', fri:'Friday', sat:'Saturday' };
        let openNow = false, next = '';
        for (let i = 0; i < 8; i++) {
          const k = ['sun','mon','tue','wed','thu','fri','sat'][(dayIdx + i) % 7];
          const h = hours[k];
          if (!h || h.closed || toMin(h.close) <= toMin(h.open)) continue;
          if (i === 0 && nowMin >= toMin(h.open) && nowMin < toMin(h.close)) { openNow = true; break; }
          if (i === 0 && nowMin >= toMin(h.open)) continue;
          next = (i === 0 ? 'today' : i === 1 ? 'tomorrow' : names[k]) + ' at ' + to12(h.open);
          break;
        }
        return { openNow, next };
      }
      function sampleMsg() {
        const n = nextOpen().next;
        return "Thanks for calling! We're closed right now" + (n ? ' and open again ' + n : '') + '.';
      }
      function renderNow() {
        const pill = $('vk-now');
        const { openNow } = nextOpen();
        pill.textContent = openNow ? 'Open now' : 'Closed now';
        pill.className = 'text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ' + (openNow ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600');
      }
      const status = $('vk-status');
      function dirty() { status.textContent = ''; renderNow(); $('vk-msg').placeholder = sampleMsg(); }

      tzSel.addEventListener('change', () => { tz = tzSel.value; dirty(); });
      $('vk-len').addEventListener('change', dirty);

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        const { getFirestore, doc, onSnapshot, updateDoc, getDoc, setDoc, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        const firstSnap = (ref) => new Promise((res) => { let un = null; un = onSnapshot(ref, (x) => { res(x.exists() ? x.data() : {}); setTimeout(() => un && un(), 0); }, () => res({})); });

        const auth = getAuth(app), db = getFirestore(app);
        let uid = null, myNumber = '';

        onAuthStateChanged(auth, async (user) => {
          if (!user) return;
          uid = user.uid;
          let d = {};
          try { d = await firstSnap(doc(db, 'users', uid)); } catch (e) {}
          const saved = d.hours || {};
          DAYS.forEach(([k]) => {
            const h = saved[k];
            hours[k] = h ? { open: h.open || '09:00', close: h.close || '17:00', closed: !!h.closed }
                         : Object.assign(def(), { closed: k === 'sat' || k === 'sun' });
          });
          tz = d.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Chicago';
          mode = ['message', 'book', 'forward', 'closed'].includes(d.afterHours) ? d.afterHours : 'message';
          myNumber = d.phoneNumber || '';
          $('vk-len').value = String(d.appointmentLength || 30);
          if (![...$('vk-len').options].some(o => o.selected)) $('vk-len').value = '30';
          $('vk-fwd').value = d.afterHoursForward ? fmtPhone(d.afterHoursForward) : '';
          $('vk-msg').value = d.afterHoursMessage || '';
          renderTz(); renderDays(); renderModes(); renderNow();
          requestAnimationFrame(() => { card.style.opacity = '1'; });
        });

        $('vk-save').addEventListener('click', async () => {
          if (!uid) return;
          const bad = DAYS.find(([k]) => !hours[k].closed && toMin(hours[k].close) <= toMin(hours[k].open));
          if (bad) { status.className = 'text-[13px] text-red-600'; status.textContent = bad[1] + ': closing time must be after opening time.'; return; }
          let fwd = '';
          if (mode === 'forward') {
            fwd = e164($('vk-fwd').value);
            if (!fwd) { status.className = 'text-[13px] text-red-600'; status.textContent = 'Enter a 10-digit US phone number to forward to.'; return; }
            if (fwd === myNumber) { status.className = 'text-[13px] text-red-600'; status.textContent = "That's your Solana number. Use your own cell or office number."; return; }
          }
          const btn = $('vk-save');
          status.textContent = '';
          btn.disabled = true;
          btn.innerHTML = '<span class="inline-flex items-center gap-2"><svg class="vc-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>Saving</span>';
          let ok = false;
          try {
            const ref = doc(db, 'users', uid);
            const data = {
              hours, timezone: tz,
              appointmentLength: Number($('vk-len').value) || 30,
              afterHours: mode,
              afterHoursForward: fwd,
              afterHoursMessage: $('vk-msg').value.trim().slice(0, 400)
            };
            try {
              await updateDoc(ref, data);
            } catch (e1) {
              // Your account record may not exist yet (rules can only "update" an existing one).
              let exists = null;
              try { exists = (await getDoc(ref)).exists(); } catch (e2) { exists = null; }
              if (exists === false) {
                const u = auth.currentUser || {};
                await setDoc(ref, Object.assign({
                  plan: 'none',
                  name: u.displayName || '',
                  email: u.email || '',
                  createdAt: serverTimestamp()
                }, data));
              } else {
                e1.vcRead = exists;   // true = record exists, null = couldn't even read it
                throw e1;
              }
            }
            ok = true;
            const sl = $('slot-length'); if (sl) sl.textContent = $('vk-len').value;
          } catch (e) {
            console.error('Save hours:', e);
            status.className = 'text-[13px] text-red-600';
            if (e.code === 'permission-denied' && e.vcRead === null) {
              status.textContent = "Could not save: Firestore rules aren't published yet (even reading is blocked). Publish the rules, then refresh.";
            } else if (e.code === 'permission-denied') {
              status.textContent = 'Could not save: the Firestore rules on your project are older ones. Paste the new rules and click Publish, then refresh.';
            } else {
              status.textContent = 'Could not save: ' + e.message;
            }
          }
          if (ok) {
            btn.innerHTML = '<span class="inline-flex items-center gap-2"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>Saved</span>';
            setTimeout(() => { btn.disabled = false; btn.textContent = 'Save hours'; }, 1500);
          } else {
            btn.disabled = false; btn.textContent = 'Save hours';
          }
        });
      } catch (e) {
        card.style.opacity = '1';
        status.className = 'text-[13px] text-red-600';
        status.textContent = 'Could not load your settings. Refresh the page.';
      }
    }
  </script>
"""

# ======================= call alerts (bell) on every app page =======================


_DP_ALERTS_JS = """
  <script type="module">
    /* VA_ALERTS_MARKER */
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const SW_URL = '/firebase-messaging-sw.js';
    const MSG_SDK = "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js";
    const onDashboard = !!document.getElementById('panel-home');

    const bell = [...document.querySelectorAll('nav a, nav button')].find(a => (a.innerHTML || '').indexOf('M18 8A6 6 0 0 0 6 8') !== -1);
    const supported = () => ('Notification' in window) && ('serviceWorker' in navigator) && ('PushManager' in window);

    if (bell) {
      bell.setAttribute('href', '#');
      bell.setAttribute('title', 'Call alerts');
      bell.classList.add('relative');
      const dot = document.createElement('span');
      dot.className = 'absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-green-500';
      dot.style.display = 'none';
      bell.appendChild(dot);

      const pop = document.createElement('div');
      pop.className = 'fixed z-[70] w-[330px] max-w-[calc(100vw-32px)] rounded-2xl bg-white border border-gray-200 p-5';
      pop.style.cssText += ';left:100px;bottom:24px;opacity:0;transform:translateY(6px);pointer-events:none;' +
        'transition:opacity .15s ease, transform .15s ease;box-shadow:0 12px 40px rgba(0,0,0,.16)';
      document.body.appendChild(pop);

      const toast = document.createElement('div');
      toast.className = 'fixed z-[70] left-[100px] bottom-6 w-[330px] max-w-[calc(100vw-32px)] rounded-2xl bg-black text-white p-4 cursor-pointer';
      toast.style.cssText += ';opacity:0;transform:translateY(6px);pointer-events:none;transition:opacity .15s ease, transform .15s ease';
      document.body.appendChild(toast);

      let isOpen = false, state = 'ask', note = '', busy = false;
      let uid = null, db = null, auth = null, fbApp = null, fs = null, pushDoc = {}, userDoc = null, msgReady = false;
      const token0 = () => { try { return localStorage.getItem('va_token') || ''; } catch (e) { return ''; } };
      const isOn = () => supported() && Notification.permission === 'granted' && !!pushDoc.enabled &&
        Array.isArray(pushDoc.tokens) && pushDoc.tokens.indexOf(token0()) !== -1;

      const BELL_ICON = '<div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center flex-shrink-0">' +
        '<svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg></div>';
      const SPIN = '<svg class="vc-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>';
      const btnBlack = 'btn-primary inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-[13.5px]';
      const btnPlain = 'inline-flex items-center justify-center px-4 py-2.5 rounded-xl font-semibold text-[13.5px] text-gray-600 hover:bg-gray-100';

      function render() {
        dot.style.display = isOn() ? 'block' : 'none';
        let title, body, actions;
        if (!supported()) {
          title = "Alerts aren't available here";
          body = "This browser can't show alerts. Use Chrome or Edge on a computer, or on iPhone add Vocallus to your Home Screen first.";
          actions = '';
        } else if (state === 'blocked' || (Notification.permission === 'denied' && !isOn())) {
          title = 'Alerts are blocked';
          body = 'Your browser is blocking alerts for this site. Click the lock icon next to the address bar, set Notifications to Allow, then try again.';
          actions = '<button data-a="enable" class="' + btnBlack + '">Try again</button>';
        } else if (isOn()) {
          title = 'Alerts are on';
          body = "You'll get a short summary on this device after every call Solana answers.";
          actions = '<button data-a="test" class="' + btnBlack + '">Send test alert</button>' +
                    '<button data-a="off" class="' + btnPlain + '">Turn off</button>';
        } else {
          title = 'Allow alerts on Solana calls';
          body = 'Get a short summary of every call Solana answers, right on this device.';
          actions = '<button data-a="enable" class="' + btnBlack + '">Allow alerts</button>' +
                    '<button data-a="later" class="' + btnPlain + '">Not now</button>';
        }
        pop.innerHTML =
          '<button data-a="close" aria-label="Close" class="absolute top-3 right-3 w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100">' +
            '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
          '<div class="flex items-start gap-3 pr-6">' + BELL_ICON +
            '<div><div class="text-[15px] font-semibold text-gray-900"></div><p class="text-[13.5px] text-gray-500 mt-1 leading-[1.5]"></p></div></div>' +
          '<div class="va-note text-[12.5px] mt-3"></div>' +
          (actions ? '<div class="flex items-center gap-2 mt-4">' + actions + '</div>' : '');
        pop.querySelector('.flex.items-start > div:last-child > div').textContent = title;
        pop.querySelector('.flex.items-start > div:last-child > p').textContent = body;
        const n = pop.querySelector('.va-note');
        n.textContent = note;
        n.className = 'va-note text-[12.5px] mt-3 ' + (note ? '' : 'hidden ') + (/^Could|^Alerts aren|failed/i.test(note) ? 'text-red-600' : 'text-gray-500');
        if (busy) {
          const b = pop.querySelector('[data-a="enable"], [data-a="test"]');
          if (b) { b.disabled = true; b.innerHTML = SPIN + (b.dataset.a === 'test' ? 'Sending' : 'Turning on'); }
        }
      }

      function place() {
        const r = bell.getBoundingClientRect();
        pop.style.left = Math.round(r.right + 12) + 'px';
        pop.style.bottom = Math.max(16, Math.round(window.innerHeight - r.bottom - 4)) + 'px';
        toast.style.left = pop.style.left;
      }
      function open() { note = ''; render(); place(); isOpen = true; pop.style.opacity = '1'; pop.style.transform = 'none'; pop.style.pointerEvents = 'auto'; }
      function close() { isOpen = false; pop.style.opacity = '0'; pop.style.transform = 'translateY(6px)'; pop.style.pointerEvents = 'none'; }
      function showToast(title, body) {
        place();
        toast.innerHTML = '<div class="text-[13.5px] font-semibold"></div><div class="text-[13px] text-white/75 mt-1 leading-[1.45]"></div>';
        toast.firstChild.textContent = title || 'Solana';
        toast.lastChild.textContent = body || '';
        toast.style.opacity = '1'; toast.style.transform = 'none'; toast.style.pointerEvents = 'auto';
        clearTimeout(toast._t);
        toast._t = setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateY(6px)'; toast.style.pointerEvents = 'none'; }, 6000);
      }
      toast.addEventListener('click', () => { location.href = 'history.html'; });

      bell.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); isOpen ? close() : open(); }, true);
      document.addEventListener('click', (e) => { const path = e.composedPath(); if (isOpen && path.indexOf(pop) === -1 && path.indexOf(bell) === -1) close(); });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
      window.addEventListener('resize', () => { if (isOpen) place(); });

      async function markPrompted() {
        if (!uid || !fs || (userDoc && userDoc.alertsPrompted)) return;
        try { await fs.updateDoc(fs.doc(db, 'users', uid), { alertsPrompted: true }); } catch (e) {}
      }

      async function api(path, opts) {
        const tok = await auth.currentUser.getIdToken();
        const r = await fetch(BRIDGE + path, Object.assign({}, opts || {}, { headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' } }));
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || ('Request failed (' + r.status + ')'));
        return j;
      }

      async function startMessaging(vapidKey) {
        const m = await import(MSG_SDK);
        if (!(await m.isSupported())) throw new Error("This browser can't show alerts.");
        const reg = await navigator.serviceWorker.register(SW_URL);
        await navigator.serviceWorker.ready;
        const messaging = m.getMessaging(fbApp);
        const token = await m.getToken(messaging, { vapidKey, serviceWorkerRegistration: reg });
        if (!msgReady) {
          msgReady = true;
          m.onMessage(messaging, (p) => { const n = p.notification || {}; showToast(n.title, n.body); });
        }
        return token;
      }

      async function enable() {
        if (!supported() || !uid) return;
        busy = true; note = ''; render();
        try {
          let perm = Notification.permission;
          if (perm === 'default') perm = await Notification.requestPermission();
          if (perm !== 'granted') { state = 'blocked'; busy = false; markPrompted(); render(); return; }
          const cfg = await fetch(BRIDGE + '/api/config').then(r => r.json()).catch(() => ({}));
          if (!cfg.vapidKey) throw new Error("Alerts aren't switched on for Vocallus yet. Try again later.");
          const token = await startMessaging(cfg.vapidKey);
          await fs.setDoc(fs.doc(db, 'users', uid, 'private', 'push'),
            { enabled: true, tokens: fs.arrayUnion(token), updatedAt: fs.serverTimestamp() }, { merge: true });
          try { localStorage.setItem('va_token', token); } catch (e) {}
          pushDoc = Object.assign({}, pushDoc, { enabled: true, tokens: (pushDoc.tokens || []).concat([token]) });
          markPrompted();
          state = 'on'; busy = false; note = 'Sending you a test alert…'; render();
          api('/api/alerts/test', { method: 'POST', body: '{}' })
            .then(() => { note = 'Test alert sent.'; render(); })
            .catch((e) => { note = 'Could not send a test alert: ' + e.message; render(); });
        } catch (e) {
          console.error('Alerts:', e);
          busy = false; note = (e.message && e.message.indexOf("Alerts aren") === 0) ? e.message : 'Could not turn on alerts: ' + (e.message || e); render();
        }
      }

      pop.addEventListener('click', async (e) => {
        const b = e.target.closest('[data-a]');
        if (!b || busy) return;
        const a = b.dataset.a;
        if (a === 'close' || a === 'later') { markPrompted(); close(); return; }
        if (a === 'enable') return enable();
        if (a === 'off') {
          try { await fs.setDoc(fs.doc(db, 'users', uid, 'private', 'push'), { enabled: false }, { merge: true }); pushDoc.enabled = false; } catch (err) {}
          note = ''; render(); return;
        }
        if (a === 'test') {
          busy = true; render();
          try { await api('/api/alerts/test', { method: 'POST', body: '{}' }); note = 'Test alert sent.'; }
          catch (err) { note = 'Could not send: ' + err.message; }
          busy = false; render();
        }
      });

      try {
""" + _DP_FB + """
        fbApp = app;
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        auth = getAuth(app); db = fs.getFirestore(app);
        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          uid = user.uid;
          fs.onSnapshot(fs.doc(db, 'users', uid, 'private', 'push'), (s) => { pushDoc = s.exists() ? s.data() : {}; render(); }, () => {});
          let first = true;
          fs.onSnapshot(fs.doc(db, 'users', uid), async (s) => {
            userDoc = s.exists() ? s.data() : null;
            // Account record missing (e.g. sign-up didn't finish) -> create it so Save buttons work.
            if (!s.exists() && !s.metadata.fromCache) {
              try {
                await fs.setDoc(fs.doc(db, 'users', uid), {
                  plan: 'none', name: user.displayName || '', email: user.email || '', createdAt: fs.serverTimestamp()
                }, { merge: true });
              } catch (e) {}
            }
            if (first && !s.metadata.fromCache) {
              first = false;
              // Ask once, right after sign-up, on the dashboard.
              if (onDashboard && userDoc && !userDoc.alertsPrompted && supported() && !isOn() && Notification.permission !== 'denied') {
                const tryOpen = () => {
                  const r = document.documentElement.classList;
                  if (r.contains('vo-check') || r.contains('vo-open')) return setTimeout(tryOpen, 700);
                  if (!isOn()) open();
                };
                setTimeout(tryOpen, 900);
              }
              // Already on -> keep this device's alert token fresh and show alerts while the page is open.
              if (supported() && Notification.permission === 'granted' && pushDoc.enabled) {
                try {
                  const cfg = await fetch(BRIDGE + '/api/config').then(r => r.json());
                  if (cfg.vapidKey) {
                    const token = await startMessaging(cfg.vapidKey);
                    if (token && (pushDoc.tokens || []).indexOf(token) === -1) {
                      await fs.setDoc(fs.doc(db, 'users', uid, 'private', 'push'), { tokens: fs.arrayUnion(token) }, { merge: true });
                    }
                    try { localStorage.setItem('va_token', token); } catch (e) {}
                    render();
                  }
                } catch (e) {}
              }
            }
          }, () => {});
        });
      } catch (e) { console.error('Alerts setup:', e); }
    }
  </script>
"""

# ======================= Solana page: real test call + test chat =======================

_DP_DEMO_JS = """
  <script type="module">
    /* VD_DEMO_MARKER */
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const WS_URL = BRIDGE.replace(/^http/, 'ws') + '/demo-call';
    const $ = (id) => document.getElementById(id);
    const box = $('chat-preview');
    const oldToggle = document.querySelector('.mode-btn') ? document.querySelector('.mode-btn').parentElement : null;

    if (box) {
      const agentName = () => (($('agent-name') && $('agent-name').value.trim()) || 'Solana');
      const SPIN = '<svg class="vc-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>';
      const PHONE = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';

      // Old element ids stay (hidden) so the page's older scripts don't crash.
      box.innerHTML =
        '<div hidden><div id="call-view"></div><button id="start-call"></button><div id="text-view"></div>' +
        '<div id="chat-log"></div><input id="chat-input"><button id="chat-send"></button></div>' +
        '<div id="vd-call">' +
          '<div class="flex flex-col items-center text-center py-6">' +
            '<div class="relative w-40 h-40 flex items-center justify-center mb-5">' +
              '<div id="vd-ring1" class="absolute inset-0 rounded-full bg-black" style="opacity:.05;transition:transform .1s linear"></div>' +
              '<div id="vd-ring2" class="absolute inset-4 rounded-full bg-black" style="opacity:.06;transition:transform .1s linear"></div>' +
              '<img src="../Images/logo.png" alt="" class="relative w-20 h-20 rounded-3xl shadow-sm">' +
            '</div>' +
            '<div id="vd-name" class="text-[22px] font-semibold text-gray-900"></div>' +
            '<div id="vd-status" class="text-[14px] text-gray-500 mt-1.5"></div>' +
            '<div id="vd-cap" class="mt-5 min-h-[52px] max-w-[560px] text-[15px] leading-[1.55] text-gray-700"></div>' +
            '<div class="mt-6 flex items-center gap-3">' +
              '<button id="vd-start" class="btn-primary inline-flex items-center gap-2 px-7 py-3.5 rounded-full font-semibold text-[14px]">' + PHONE + 'Start test call</button>' +
              '<button id="vd-mute" class="hidden inline-flex items-center px-6 py-3.5 rounded-full font-semibold text-[14px] border border-gray-200 bg-white hover:bg-gray-50">Mute</button>' +
              '<button id="vd-end" class="hidden inline-flex items-center px-7 py-3.5 rounded-full font-semibold text-[14px] text-white" style="background:#dc2626">End call</button>' +
            '</div>' +
            '<div id="vd-err" class="hidden mt-4 text-[13.5px] text-red-600 max-w-[480px]"></div>' +
            '<div class="mt-5 text-[12.5px] text-gray-400">Uses your saved prompt, business hours and calendar. Bookings made here are real.</div>' +
          '</div>' +
        '</div>' +
        '<div id="vd-text" class="hidden">' +
          '<div id="vd-log" class="space-y-3 mb-5 max-h-[440px] min-h-[200px] overflow-y-auto pr-1"></div>' +
          '<form id="vd-form" class="flex items-center gap-3">' +
            '<input id="vd-in" type="text" autocomplete="off" maxlength="1000" placeholder="Message Solana like a customer would" class="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-[14px] focus:outline-none focus:border-gray-400 bg-white">' +
            '<button id="vd-send" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Send</button>' +
          '</form>' +
          '<div class="flex items-center justify-between mt-2 text-[12px] text-gray-400">' +
            '<span>Uses your saved prompt, business hours and calendar.</span>' +
            '<button type="button" id="vd-clear" class="font-semibold text-gray-500 hover:text-black underline underline-offset-2">Clear chat</button>' +
          '</div>' +
        '</div>';

      // ---- Call / Text toggle with a sliding pill ----
      const tg = document.createElement('div');
      tg.className = 'relative flex bg-gray-100 rounded-full p-1';
      tg.innerHTML = '<span id="vd-pill" class="absolute top-1 bottom-1 rounded-full bg-white shadow-sm" style="transition:transform .2s cubic-bezier(.4,0,.2,1), width .2s cubic-bezier(.4,0,.2,1)"></span>' +
        '<button data-m="call" class="vd-m relative px-5 py-2 rounded-full text-[14px] font-semibold" style="transition:color .2s">Call</button>' +
        '<button data-m="text" class="vd-m relative px-5 py-2 rounded-full text-[14px] font-semibold" style="transition:color .2s">Text</button>';
      if (oldToggle) { oldToggle.style.display = 'none'; oldToggle.after(tg); } else { box.before(tg); }
      let mode = 'call';
      function movePill(anim) {
        const b = tg.querySelector('[data-m="' + mode + '"]'), pill = $('vd-pill');
        if (!anim) pill.style.transition = 'none';
        pill.style.width = b.offsetWidth + 'px';
        pill.style.transform = 'translateX(' + (b.offsetLeft - 4) + 'px)';
        if (!anim) { pill.offsetWidth; pill.style.transition = 'transform .2s cubic-bezier(.4,0,.2,1), width .2s cubic-bezier(.4,0,.2,1)'; }
        tg.querySelectorAll('.vd-m').forEach(x => { x.style.color = x.dataset.m === mode ? '#111827' : '#6b7280'; });
      }
      function setMode(m) {
        mode = m; movePill(true);
        const show = $(m === 'call' ? 'vd-call' : 'vd-text'), hide = $(m === 'call' ? 'vd-text' : 'vd-call');
        hide.classList.add('hidden');
        show.style.opacity = '0'; show.classList.remove('hidden');
        requestAnimationFrame(() => { show.style.transition = 'opacity .15s ease'; show.style.opacity = '1'; });
        if (m === 'text') setTimeout(() => $('vd-in').focus(), 50);
      }
      tg.querySelectorAll('.vd-m').forEach(b => b.addEventListener('click', () => setMode(b.dataset.m)));
      requestAnimationFrame(() => movePill(false));
      window.addEventListener('resize', () => movePill(false));

      const refreshName = () => { $('vd-name').textContent = agentName(); };
      refreshName();
      if ($('agent-name')) $('agent-name').addEventListener('input', refreshName);

      let auth = null, db = null, fs = null, uid = null, saved = { agentName: null, systemPrompt: null };

      // Test with what's typed: save the name + prompt first if they changed.
      async function saveIfDirty() {
        if (!uid || !fs) return;
        const name = agentName(), prompt = ($('system-prompt') && $('system-prompt').value.trim()) || '';
        if (name === saved.agentName && prompt === saved.systemPrompt) return;
        try {
          await fs.updateDoc(fs.doc(db, 'users', uid), { agentName: name, systemPrompt: prompt });
          saved = { agentName: name, systemPrompt: prompt };
        } catch (e) { console.warn('Could not save prompt before test:', e); }
      }
      async function idToken() { if (!auth || !auth.currentUser) throw new Error('Please sign in again.'); return auth.currentUser.getIdToken(); }

      // ================= Test call =================
      const WORKLET = [
        'class VcMic extends AudioWorkletProcessor {',
        '  constructor() { super(); this.ratio = sampleRate / 16000; this.pos = 0; this.acc = 0; this.n = 0; this.out = new Int16Array(800); this.len = 0; }',
        '  process(inputs) {',
        '    const ch = inputs[0] && inputs[0][0];',
        '    if (ch) for (let i = 0; i < ch.length; i++) {',
        '      this.acc += ch[i]; this.n++; this.pos += 1;',
        '      if (this.pos >= this.ratio) {',
        '        this.pos -= this.ratio;',
        '        let v = this.acc / this.n; this.acc = 0; this.n = 0;',
        '        v = Math.max(-1, Math.min(1, v));',
        '        this.out[this.len++] = v < 0 ? v * 32768 : v * 32767;',
        '        if (this.len === this.out.length) { this.port.postMessage(this.out.slice(0).buffer); this.len = 0; }',
        '      }',
        '    }',
        '    return true;',
        '  }',
        '}',
        "registerProcessor('vc-mic', VcMic);"
      ].join(String.fromCharCode(10));

      const toB64 = (buf) => { const b = new Uint8Array(buf); let s = ''; for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode.apply(null, b.subarray(i, i + 32768)); return btoa(s); };
      const fromB64 = (str) => { const s = atob(str); const b = new Uint8Array(s.length - (s.length % 2)); for (let i = 0; i < b.length; i++) b[i] = s.charCodeAt(i); return b.buffer; };
      const mmss = (s) => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');

      let ws = null, ctx = null, mic = null, micNode = null, srcNode = null, sink = null, outGain = null, anIn = null, anOut = null;
      let sources = [], nextTime = 0, muted = false, live = false, callState = 'idle', startedAt = 0, ticker = null, raf = null, connectTimer = null;
      let capWho = '', capYou = '', capAgent = '', endReason = '', switchingV = false;
      // Voice picked during a live test call -> switch it live, smoothly
      window.addEventListener('vc-voice', (e) => {
        if (callState !== 'live' || !ws || ws.readyState !== 1 || !ctx || !outGain) return;
        const d = e.detail || {};
        if (d.agentName) { try { $('vd-name') && ($('vd-name').textContent = d.agentName); } catch (x) {} }
        switchingV = true;
        setStatus('Switching voice…');
        outGain.gain.cancelScheduledValues(ctx.currentTime);
        outGain.gain.setTargetAtTime(0, ctx.currentTime, 0.07);
        ws.send(JSON.stringify({ type: 'voice', voice: d.voice, agentName: d.agentName }));
      });

      function setStatus(t) { $('vd-status').textContent = t; }
      function showErr(t) { const e = $('vd-err'); e.textContent = t; e.classList.toggle('hidden', !t); }
      function renderCaps() {
        const c = $('vd-cap');
        c.innerHTML = '';
        if (capYou) { const d = document.createElement('div'); d.className = 'text-gray-400 text-[14px]'; d.textContent = 'You: ' + capYou.trim(); c.appendChild(d); }
        if (capAgent) { const d = document.createElement('div'); d.className = 'text-gray-900 mt-1'; d.textContent = agentName() + ': ' + capAgent.trim(); c.appendChild(d); }
      }
      function setCallState(s) {
        callState = s;
        const start = $('vd-start'), mute = $('vd-mute'), end = $('vd-end');
        start.classList.toggle('hidden', s === 'live');
        mute.classList.toggle('hidden', s !== 'live');
        end.classList.toggle('hidden', s !== 'live');
        start.disabled = s === 'connecting';
        start.innerHTML = s === 'connecting' ? SPIN + 'Connecting' : PHONE + (s === 'ended' ? 'Call again' : 'Start test call');
        if (s === 'idle') setStatus('Talk to ' + agentName() + ' right here in your browser.');
        if (s === 'connecting') setStatus('Connecting…');
      }
      setCallState('idle');

      function playChunk(b64) {
        if (!ctx) return;
        const pcm = new Int16Array(fromB64(b64));
        if (!pcm.length) return;
        const buf = ctx.createBuffer(1, pcm.length, 24000);
        const ch = buf.getChannelData(0);
        for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
        const src = ctx.createBufferSource();
        src.buffer = buf; src.connect(outGain);
        const t = Math.max(nextTime, ctx.currentTime + 0.05);
        src.start(t); nextTime = t + buf.duration;
        sources.push(src);
        src.onended = () => { sources = sources.filter(x => x !== src); };
      }
      function clearAudio() { sources.forEach(s => { try { s.stop(); } catch (e) {} }); sources = []; nextTime = 0; }

      function level(an) {
        if (!an) return 0;
        const a = new Uint8Array(an.fftSize); an.getByteTimeDomainData(a);
        let sum = 0; for (let i = 0; i < a.length; i++) { const v = (a[i] - 128) / 128; sum += v * v; }
        return Math.min(1, Math.sqrt(sum / a.length) * 4);
      }
      function animate() {
        const out = level(anOut), inp = muted ? 0 : level(anIn) * 0.6;
        $('vd-ring1').style.transform = 'scale(' + (1 + Math.max(out, inp) * 0.18).toFixed(3) + ')';
        $('vd-ring2').style.transform = 'scale(' + (1 + out * 0.3).toFixed(3) + ')';
        raf = requestAnimationFrame(animate);
      }

      function cleanup() {
        live = false;
        clearTimeout(connectTimer); clearInterval(ticker); cancelAnimationFrame(raf);
        $('vd-ring1').style.transform = ''; $('vd-ring2').style.transform = '';
        try { mic && mic.getTracks().forEach(t => t.stop()); } catch (e) {}
        try { srcNode && srcNode.disconnect(); micNode && micNode.disconnect(); } catch (e) {}
        const c = ctx; ctx = null; mic = null; micNode = null; srcNode = null;
        setTimeout(() => { try { c && c.close(); } catch (e) {} }, 300);
        clearAudio();
      }
      function finish(msg) {
        if (callState === 'idle' || callState === 'ended') return;
        const secs = startedAt ? Math.round((Date.now() - startedAt) / 1000) : 0;
        try { ws && ws.readyState === 1 && ws.send(JSON.stringify({ type: 'stop' })); } catch (e) {}
        try { ws && ws.close(); } catch (e) {}
        ws = null;
        cleanup();
        setCallState(startedAt ? 'ended' : 'idle');
        if (startedAt) setStatus(msg || ('Call ended · ' + mmss(secs)));
        startedAt = 0;
      }

      async function startCall() {
        if (callState === 'connecting' || callState === 'live') return;
        if (window.vcBusiness && !(await window.vcBusiness.ensure('test'))) return;   // VO_ENSURE_TEST
        showErr(''); capYou = ''; capAgent = ''; renderCaps(); endReason = '';
        setCallState('connecting');
        try {
          ctx = new (window.AudioContext || window.webkitAudioContext)();
          await ctx.resume();
          mic = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } });
        } catch (e) {
          cleanup(); setCallState('idle');
          return showErr(e && e.name === 'NotAllowedError'
            ? 'Allow microphone access to test a call. Click the mic icon in the address bar, choose Allow, then try again.'
            : "Couldn't start your microphone. Check that one is plugged in.");
        }
        try {
          const url = URL.createObjectURL(new Blob([WORKLET], { type: 'application/javascript' }));
          await ctx.audioWorklet.addModule(url);
          srcNode = ctx.createMediaStreamSource(mic);
          micNode = new AudioWorkletNode(ctx, 'vc-mic');
          sink = ctx.createGain(); sink.gain.value = 0;
          srcNode.connect(micNode); micNode.connect(sink); sink.connect(ctx.destination);
          anIn = ctx.createAnalyser(); anIn.fftSize = 512; srcNode.connect(anIn);
          outGain = ctx.createGain(); anOut = ctx.createAnalyser(); anOut.fftSize = 512;
          outGain.connect(anOut); anOut.connect(ctx.destination);
          micNode.port.onmessage = (e) => {
            if (live && !muted && ws && ws.readyState === 1) ws.send(JSON.stringify({ type: 'audio', data: toB64(e.data) }));
          };
          await saveIfDirty();
          const token = await idToken();
          ws = new WebSocket(WS_URL);
          connectTimer = setTimeout(() => { if (callState === 'connecting') { finish(); showErr("Couldn't reach " + agentName() + '. Try again in a moment.'); } }, 15000);
          ws.onopen = () => ws.send(JSON.stringify({ type: 'start', token }));
          ws.onmessage = (ev) => {
            let m; try { m = JSON.parse(ev.data); } catch (e) { return; }
            if (m.type === 'live') {
              clearTimeout(connectTimer);
              live = true; startedAt = Date.now(); muted = false; $('vd-mute').textContent = 'Mute';
              setCallState('live'); setStatus('Live · 0:00');
              ticker = setInterval(() => setStatus(switchingV ? 'Switching voice…' : (muted ? 'Muted · ' : 'Live · ') + mmss(Math.round((Date.now() - startedAt) / 1000))), 1000);
              animate();
            } else if (m.type === 'audio') {
              playChunk(m.data);
            } else if (m.type === 'clear') {
              clearAudio();
            } else if (m.type === 'switched') {
              switchingV = false;
              clearAudio(); capAgent = ''; renderCaps();
              if (ctx && outGain) {
                outGain.gain.cancelScheduledValues(ctx.currentTime);
                outGain.gain.setValueAtTime(0, ctx.currentTime);
                outGain.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.35);
              }
              if (m.failed) showErr("Couldn't switch the voice mid-call. It will be used on your next call.");
            } else if (m.type === 'caption') {
              if (m.who === 'you') { if (capWho !== 'you') capYou = ''; capYou += m.text; }
              else { if (capWho !== 'agent') capAgent = ''; capAgent += m.text; }
              capWho = m.who; renderCaps();
            } else if (m.type === 'tool') {
              if (m.name === 'book_appointment') setStatus('Booking on your calendar…');
            } else if (m.type === 'error') {
              showErr(m.error || 'Something went wrong.');
            } else if (m.type === 'ended') {
              endReason = m.reason;
              // let the last words finish playing
              const wait = ctx ? Math.max(0, (nextTime - ctx.currentTime) * 1000) : 0;
              setTimeout(() => finish(m.reason === 'limit' ? 'Test calls are limited to 5 minutes.' : ''), Math.min(wait, 4000));
            }
          };
          ws.onclose = () => { if (callState === 'connecting') { finish(); if ($('vd-err').classList.contains('hidden')) showErr("Couldn't reach " + agentName() + '. Try again in a moment.'); } };
        } catch (e) {
          finish(); setCallState('idle');
          showErr(e.message || "Couldn't start the test call.");
        }
      }
      $('vd-start').addEventListener('click', startCall);
      $('vd-end').addEventListener('click', () => finish());
      $('vd-mute').addEventListener('click', () => {
        muted = !muted;
        $('vd-mute').textContent = muted ? 'Unmute' : 'Mute';
        $('vd-mute').style.background = muted ? '#111827' : '';
        $('vd-mute').style.color = muted ? '#fff' : '';
      });
      window.addEventListener('beforeunload', () => finish());

      // ================= Test chat =================
      const log = $('vd-log');
      let msgs = [];
      function empty() {
        log.innerHTML = '<div class="vd-empty h-[200px] flex flex-col items-center justify-center text-center">' +
          '<img src="../Images/logo.png" alt="" class="w-12 h-12 rounded-2xl mb-3">' +
          '<div class="text-[15px] font-medium text-gray-700">Say hi to ' + agentName().replace(/[<>&]/g, '') + '</div>' +
          '<div class="text-[13px] text-gray-400 mt-1">Try asking for an appointment or your hours.</div></div>';
      }
      empty();
      function bubble(role, text) {
        const e = log.querySelector('.vd-empty'); if (e) e.remove();
        const row = document.createElement('div');
        row.className = role === 'user' ? 'flex justify-end' : 'flex items-start gap-3';
        row.style.opacity = '0'; row.style.transform = 'translateY(4px)'; row.style.transition = 'opacity .15s ease, transform .15s ease';
        row.innerHTML = role === 'user'
          ? '<div class="bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[75%]"><p class="text-[14px] leading-[1.5] whitespace-pre-wrap"></p></div>'
          : '<img src="../Images/logo.png" alt="" class="w-8 h-8 rounded-xl flex-shrink-0"><div class="bg-white rounded-2xl rounded-tl-sm border border-gray-100 px-4 py-3 max-w-[75%]"><p class="text-[14px] text-gray-800 leading-[1.5] whitespace-pre-wrap"></p></div>';
        const p = row.querySelector('p');
        if (text === null) p.innerHTML = '<span class="vd-dot">•</span><span class="vd-dot">•</span><span class="vd-dot">•</span>';
        else p.textContent = text;
        log.appendChild(row);
        requestAnimationFrame(() => { row.style.opacity = '1'; row.style.transform = 'none'; });
        log.scrollTop = log.scrollHeight;
        return p;
      }
      let sending = false;
      $('vd-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = $('vd-in'), text = input.value.trim();
        if (!text || sending) return;
        sending = true; input.value = '';
        bubble('user', text);
        msgs.push({ role: 'user', text });
        const p = bubble('agent', null);
        try {
          await saveIfDirty();
          const tok = await idToken();
          const r = await fetch(BRIDGE + '/api/demo/chat', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: msgs })
          });
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(j.error || ('Request failed (' + r.status + ')'));
          p.textContent = j.reply;
          msgs.push({ role: 'model', text: j.reply });
        } catch (err) {
          msgs.pop();
          p.textContent = err.message === 'Failed to fetch' ? "Couldn't reach " + agentName() + '. Try again in a moment.' : err.message;
          p.classList.add('text-red-600');
        }
        log.scrollTop = log.scrollHeight;
        sending = false; input.focus();
      });
      $('vd-clear').addEventListener('click', () => { msgs = []; empty(); });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        auth = getAuth(app); db = fs.getFirestore(app);
        onAuthStateChanged(auth, (user) => {
          if (!user) return;
          uid = user.uid;
          fs.onSnapshot(fs.doc(db, 'users', uid), (s) => {
            const d = s.exists() ? s.data() : {};
            saved = { agentName: d.agentName || 'Solana', systemPrompt: d.systemPrompt || '' };
          }, () => {});
        });
      } catch (e) { console.error('Test panel:', e); }
    }
  </script>
"""

# ======================= dashboard: real scroll container =======================

_DP_DASH_MAIN_JS = """
  <script>
    /* VM_MAIN_MARKER */
    (function () {
      if (document.querySelector('body > main')) return;
      var panels = [].slice.call(document.querySelectorAll('body > .panel'));
      if (!panels.length) return;
      var main = document.createElement('main');
      main.className = 'flex-1 min-w-0 h-screen overflow-y-auto';
      panels[0].parentNode.insertBefore(main, panels[0]);
      panels.forEach(function (p) { main.appendChild(p); });
    })();
  </script>
"""

# ======================= Solana page: AI provider (Gemini or ChatGPT) =======================

_DP_PROVIDER_JS = """
  <script type="module">
    /* VP_PROVIDER_MARKER */
    const $ = (id) => document.getElementById(id);
    const card = $('api-setup');
    if (card) {
      const P = {
        gemini: { label: 'Gemini', sub: 'Google', img: '../Images/gem.png', prefixes: ['AIza', 'AQ.'],
                  link: 'https://aistudio.google.com/api-keys', linkText: 'Get a Google API key', hint: 'Google keys start with "AIza".' },
        openai: { label: 'ChatGPT', sub: 'OpenAI', img: '../Images/cha.png', prefixes: ['sk-'],
                  link: 'https://platform.openai.com/api-keys', linkText: 'Get an OpenAI API key', hint: 'OpenAI keys start with "sk-".' }
      };
      const SPIN = '<svg class="vc-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>';
      const CHECK = '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

      // Old element ids stay (hidden) so the page's older scripts don't crash.
      card.innerHTML =
        '<div hidden><div id="provider-grid"></div><input id="api-key"><p id="key-hint"></p><div id="key-saved"></div>' +
        '<div id="key-masked"></div><button id="key-replace"></button><div id="api-error"></div><div id="api-error-title"></div>' +
        '<div id="api-error-msg"></div><button id="save-key"></button></div>' +
        '<div class="flex items-start justify-between gap-4 flex-wrap mb-5">' +
          '<div><h2 class="text-[18px] font-semibold text-gray-900">AI provider</h2>' +
          '<p class="text-[14px] text-gray-500 mt-1">Pick the AI behind your agent. Your key is only used for your calls.</p></div>' +
          '<span id="vp-pill" class="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">Not connected</span>' +
        '</div>' +
        '<div id="vp-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5"></div>' +
        '<div id="vp-note" class="hidden mb-4 rounded-xl bg-white border border-gray-200 px-4 py-3 text-[13px] text-gray-600"></div>' +
        '<div id="vp-saved" class="hidden mb-5 flex items-center justify-between rounded-xl bg-white border border-gray-200 px-4 py-3">' +
          '<div><div class="text-[12px] font-semibold text-gray-500 uppercase tracking-wide">Saved key</div>' +
          '<div id="vp-masked" class="text-[14px] font-mono text-gray-900 mt-0.5"></div></div>' +
          '<button id="vp-replace" class="text-[13px] font-semibold text-gray-700 underline underline-offset-2 hover:text-black">Replace key</button>' +
        '</div>' +
        '<div id="vp-entry" class="mb-5">' +
          '<label class="block text-[13px] font-semibold text-gray-700 mb-2">API key</label>' +
          '<input id="vp-key" type="password" autocomplete="off" placeholder="Paste your API key" class="w-full rounded-xl border border-gray-200 px-3.5 py-3 text-[14px] focus:outline-none focus:border-gray-400 bg-white">' +
          '<p class="text-[12.5px] text-gray-500 mt-2"><span id="vp-hint"></span> ' +
          '<a id="vp-link" target="_blank" rel="noopener" class="font-semibold text-gray-800 underline underline-offset-2 hover:text-black"></a></p>' +
        '</div>' +
        '<div id="vp-err" class="hidden mb-4 rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-[13px] text-red-700"></div>' +
        '<button id="vp-save" class="btn-primary min-w-[130px] inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-[14px]">Save key</button>';

      let selected = 'gemini', saved = null, plan = 'none', uid = null, fs = null, db = null, replacing = false;
      const mask = (k) => k.slice(0, 4) + '••••••' + k.slice(-4);

      function render() {
        $('vp-grid').innerHTML = Object.keys(P).map(id => {
          const p = P[id], on = id === selected;
          return '<button data-p="' + id + '" class="vp-card rounded-2xl border-2 bg-white p-4 text-left transition ' +
            (on ? 'border-black ring-2 ring-black/10' : 'border-gray-200 hover:border-gray-300') + '">' +
            '<div class="flex items-center justify-between"><img src="' + p.img + '" alt="" class="w-8 h-8 rounded-lg">' +
            (saved && saved.provider === id ? '<span class="text-[11px] font-semibold text-green-700">Connected</span>' : '') + '</div>' +
            '<div class="text-[14px] font-semibold text-gray-900 mt-3">' + p.label + '</div>' +
            '<div class="text-[12px] text-gray-500 mt-0.5">' + p.sub + '</div></button>';
        }).join('');
        $('vp-grid').querySelectorAll('.vp-card').forEach(b => b.addEventListener('click', () => {
          selected = b.dataset.p; replacing = false; $('vp-err').classList.add('hidden'); render();
        }));
        const p = P[selected];
        const hasSaved = !!(saved && saved.apiKey && saved.provider === selected);
        $('vp-saved').classList.toggle('hidden', !hasSaved || replacing);
        $('vp-entry').classList.toggle('hidden', hasSaved && !replacing);
        $('vp-save').classList.toggle('hidden', hasSaved && !replacing);
        if (hasSaved) $('vp-masked').textContent = mask(saved.apiKey);
        $('vp-hint').textContent = p.hint;
        $('vp-link').textContent = p.linkText;
        $('vp-link').href = p.link;
        const pill = $('vp-pill');
        const connected = !!(saved && saved.apiKey);
        pill.textContent = connected ? 'Connected' : 'Not connected';
        pill.className = 'text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full ' + (connected ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600');
        const note = $('vp-note');
        const msg = plan === 'max' ? 'Your Max plan includes AI, so no key is needed. Add one only if you want to use your own.'
                  : plan === 'pro' ? '' : 'You can test for free now. Your key is used for phone calls once you are on Pro.';
        note.textContent = msg; note.classList.toggle('hidden', !msg);
      }
      render();
      $('vp-replace').addEventListener('click', () => { replacing = true; render(); $('vp-key').focus(); });

      $('vp-save').addEventListener('click', async () => {
        const err = $('vp-err'), btn = $('vp-save'), key = $('vp-key').value.trim(), p = P[selected];
        err.classList.add('hidden');
        if (!uid || !fs) { err.textContent = 'Please sign in again.'; err.classList.remove('hidden'); return; }
        if (key.length < 20 || !p.prefixes.some(x => key.indexOf(x) === 0)) {
          err.textContent = "That doesn't look like a " + p.sub + ' key. ' + p.hint;
          err.classList.remove('hidden'); return;
        }
        btn.disabled = true; btn.innerHTML = SPIN + 'Saving';
        try {
          await fs.setDoc(fs.doc(db, 'users', uid, 'private', 'ai'), {
            provider: selected, apiKey: key,
            model: selected === 'openai' ? 'gpt-realtime' : 'gemini-live',
            updatedAt: fs.serverTimestamp()
          });
          saved = { provider: selected, apiKey: key }; replacing = false;
          $('vp-key').value = '';
          btn.innerHTML = CHECK + 'Saved';
          setTimeout(() => { btn.disabled = false; btn.textContent = 'Save key'; render(); }, 1200);
        } catch (e) {
          btn.disabled = false; btn.textContent = 'Save key';
          err.textContent = 'Could not save: ' + e.message; err.classList.remove('hidden');
        }
      });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        db = fs.getFirestore(app);
        onAuthStateChanged(getAuth(app), (user) => {
          if (!user) return;
          uid = user.uid;
          fs.onSnapshot(fs.doc(db, 'users', uid, 'private', 'ai'), (s) => {
            const d = s.exists() ? s.data() : null;
            saved = d && d.apiKey && (d.provider === 'openai' || d.provider === 'gemini' || !d.provider)
              ? { provider: d.provider === 'openai' ? 'openai' : 'gemini', apiKey: d.apiKey } : null;
            if (saved && !replacing) selected = saved.provider;
            render();
          }, () => {});
          fs.onSnapshot(fs.doc(db, 'users', uid), (s) => { plan = (s.exists() && s.data().plan) || 'none'; render(); }, () => {});
        });
      } catch (e) { console.error('AI provider card:', e); }
    }
  </script>
"""

# ======================= Solana page: voice (male / female) =======================

_DP_VOICE_JS = """
  <script type="module">
    /* VV_VOICE_MARKER */
    const $ = (id) => document.getElementById(id);
    const saveBtn = $('save-prompt');
    if (saveBtn) {
      // tier: 'free' | 'pro' (Max voices can be added later with tier 'max')
      const V = [
        { id: 'default', label: 'Solana', sub: 'Default voice', tier: 'free', imgs: ['logo.png'], audio: 'solana' },
        { id: 'female', label: 'Female', sub: 'Pro voice', tier: 'pro', imgs: ['pfmale.png', 'pfemale.png', 'pfmales.png'], audio: 'pfmale' },
        { id: 'male', label: 'Male', sub: 'Pro voice', tier: 'pro', imgs: ['pmale.png'], audio: 'pmale' }
      ];
      const RANK = { free: 0, pro: 1, max: 2 };
      const planRank = (p) => p === 'max' ? 2 : p === 'pro' ? 1 : 0;
      const PLAY = '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
      const STOP = '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1.5"/></svg>';
      const wrap = document.createElement('div');
      wrap.innerHTML =
        '<label class="block text-[13px] font-semibold text-gray-700 mb-1.5">Voice</label>' +
        '<div id="vv-list" class="space-y-2"></div>' +
        '<div id="vv-up" aria-hidden="true" style="overflow:hidden;max-height:0;opacity:0;margin-top:0;transform:translateY(-6px);' +
            'transition:max-height .3s cubic-bezier(.4,0,.2,1), opacity .25s ease, transform .3s cubic-bezier(.4,0,.2,1), margin-top .3s cubic-bezier(.4,0,.2,1)">' +
          '<div class="rounded-xl bg-black text-white p-3.5">' +
            '<div id="vv-up-title" class="text-[13px] font-semibold">Pro voices come with Pro and Max</div>' +
            '<div class="text-[12px] text-white/70 mt-0.5">Upgrade to use this voice on your calls.</div>' +
            '<a href="pricing.html?back=solana" tabindex="-1" class="mt-2.5 inline-flex items-center justify-center px-3.5 py-1.5 rounded-lg bg-white text-black text-[12.5px] font-semibold hover:bg-gray-100">Upgrade</a>' +
          '</div>' +
        '</div>' +
        '<p class="text-[12px] text-gray-500 mt-2">More voices coming soon.</p>' +
        '<p id="vv-note" class="text-[12px] text-gray-400 mt-1">Press play to hear a voice.</p>' +
        '<div id="vv-live" class="hidden mt-3 rounded-xl border px-3 py-2.5 text-[12.5px] leading-[1.45]"></div>';
      saveBtn.parentNode.insertBefore(wrap, saveBtn);

      let voice = 'default', plan = 'none', uid = null, fs = null, db = null, audio = null, playing = null, authUser = null;
      const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
      const fmtNum = (n) => { let d = String(n || '').replace(/[^0-9]/g, ''); if (d.length === 11 && d[0] === '1') d = d.slice(1);
        return d.length === 10 ? '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6) : n; };
      // What the server will really use on calls (number, AI, voice) + any problem.
      let statusTimer = null;
      function refreshStatus(delay) {
        clearTimeout(statusTimer);
        statusTimer = setTimeout(async () => {
          const box = $('vv-live');
          if (!authUser) return;
          try {
            const tok = await authUser.getIdToken();
            const r = await fetch(BRIDGE + '/api/agent/status', { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) throw new Error('status ' + r.status);
            const st = await r.json();
            const v = V.find(x => x.id === st.voice) || V[0];
            const lines = [];
            let bad = false;
            if (st.phoneNumber) lines.push('Calls to <b>' + fmtNum(st.phoneNumber) + '</b> use the <b>' + v.label + '</b> voice.');
            else lines.push('No phone number on this account yet, so you can only test here.');
            if (!st.aiReady) { bad = true; lines.push('Add an API key in the AI provider card so calls can be answered.'); }
            if (st.savedVoice !== st.voice) lines.push('Your plan uses the default voice.');
            const P = {
              'eleven-missing': "Max voices aren't switched on yet: the server needs ELEVENLABS_API_KEY in Railway. Calls use the default voice until then.",
              'eleven-key': 'ElevenLabs rejected the server key (ELEVENLABS_API_KEY). Calls fall back to the default voice.',
              'eleven-voice': "ElevenLabs can't find this voice in your account. Add it to My Voices in ElevenLabs or fix the voice ID in Railway.",
              'eleven-unreachable': "Couldn't reach ElevenLabs right now."
            };
            if (st.problem && P[st.problem]) { bad = true; lines.push(P[st.problem]); }
            box.innerHTML = lines.join('<br>');
            box.className = 'mt-3 rounded-xl border px-3 py-2.5 text-[12.5px] leading-[1.45] ' +
              (bad ? 'border-red-200 bg-red-50 text-red-700' : 'border-gray-200 bg-white text-gray-600');
          } catch (e) { box.classList.add('hidden'); }
        }, delay || 0);
      }
      const allowed = (v) => planRank(plan) >= RANK[v.tier];

      function render() {
        $('vv-list').innerHTML = V.map(v => {
          const on = v.id === voice;
          const tag = v.tier === 'free' ? '' :
            '<span class="ml-1.5 inline-flex items-center rounded-full bg-black text-white px-1.5 py-[1px] text-[10px] font-bold uppercase tracking-wide">' + v.tier + '</span>';
          return '<div role="button" tabindex="0" data-v="' + v.id + '" class="vv-row flex items-center gap-3 rounded-xl border-2 bg-white px-3 py-2.5 cursor-pointer transition ' +
              (on ? 'border-black ring-2 ring-black/10' : 'border-gray-200 hover:border-gray-300') + '">' +
            '<img data-i="0" alt="" class="w-9 h-9 rounded-full object-cover bg-gray-100 flex-shrink-0">' +
            '<div class="flex-1 min-w-0"><div class="flex items-center text-[13.5px] font-semibold text-gray-900">' + v.label + tag + '</div>' +
              '<div class="text-[12px] text-gray-500">' + v.sub + '</div></div>' +
            '<button type="button" data-play="' + v.id + '" aria-label="Play ' + v.label + '" ' +
              'class="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center text-gray-800 hover:bg-gray-50 flex-shrink-0">' +
              (playing === v.id ? STOP : PLAY) + '</button>' +
          '</div>';
        }).join('');
        // pictures: try each file name in order (pfmale.png, then pfemale.png, ...)
        $('vv-list').querySelectorAll('.vv-row').forEach(row => {
          const v = V.find(x => x.id === row.dataset.v), img = row.querySelector('img');
          let i = 0;
          img.addEventListener('error', () => { i++; if (i < v.imgs.length) img.src = '../Images/' + v.imgs[i]; else img.style.visibility = 'hidden'; });
          img.src = '../Images/' + v.imgs[0];
        });
      }
      render();

      const up = $('vv-up');
      let upOpen = false;
      // Slide + fade open/closed
      function showUpgrade(show) {
        if (show === upOpen) return;
        upOpen = show;
        up.setAttribute('aria-hidden', show ? 'false' : 'true');
        up.querySelector('a').tabIndex = show ? 0 : -1;
        up.style.maxHeight = show ? up.scrollHeight + 'px' : '0';
        up.style.opacity = show ? '1' : '0';
        up.style.transform = show ? 'none' : 'translateY(-6px)';
        up.style.marginTop = show ? '8px' : '0';
      }

      function stop() { if (audio) { audio.pause(); audio = null; } playing = null; render(); }
      function play(id) {
        if (playing === id) return stop();
        stop();
        const v = V.find(x => x.id === id);
        const tryPlay = (ext, next) => {
          const a = new Audio('../Audio/' + v.audio + '.' + ext);
          a.addEventListener('ended', stop);
          a.addEventListener('error', () => { if (next) next(); else { stop(); $('vv-note').textContent = 'That voice sample is not uploaded yet.'; } }, { once: true });
          audio = a; playing = id; render();
          a.play().catch(() => {});
        };
        tryPlay('mp3', () => tryPlay('wav', null));
      }

      async function choose(id) {
        const v = V.find(x => x.id === id);
        if (!allowed(v)) {
          const t = v.tier === 'max' ? 'Max voices come with the Max plan' : 'Pro voices come with Pro and Max';
          if (upOpen && $('vv-up-title').textContent !== t) {   // switch message with a quick fade
            up.style.opacity = '0';
            setTimeout(() => { $('vv-up-title').textContent = t; up.style.opacity = '1'; }, 150);
          } else { $('vv-up-title').textContent = t; }
          showUpgrade(true); $('vv-note').textContent = ''; return;
        }
        showUpgrade(false);
        if (id === voice) return;
        voice = id; render();
        // Male voice -> "Solan", back to "Solana" for female/default (only if the name is still one of those two)
        const MALE = ['male', 'mmale', 'rmale'];
        const nameIn = $('agent-name');
        const upd = { voice: id };
        if (nameIn) {
          const cur = nameIn.value.trim();
          const want = MALE.includes(id) ? (cur === 'Solana' || cur === '' ? 'Solan' : null)
                                         : (cur === 'Solan' ? 'Solana' : null);
          if (want) {
            nameIn.value = want;
            nameIn.dispatchEvent(new Event('input', { bubbles: true }));   // updates the name shown + the default prompt
            upd.agentName = want;
            const pr = $('system-prompt');
            if (pr && pr.value.trim()) upd.systemPrompt = pr.value.trim();
          }
        }
        // live test call? switch the voice right away (VV_LIVE_SWITCH)
        window.dispatchEvent(new CustomEvent('vc-voice', { detail: { voice: id, agentName: upd.agentName || (nameIn ? nameIn.value.trim() : '') } }));
        if (uid && fs) {
          try { await fs.updateDoc(fs.doc(db, 'users', uid), upd); $('vv-note').textContent = upd.agentName ? 'Saved. Your agent is now called ' + upd.agentName + '.' : 'Saved. Used on your next call.'; refreshStatus(300); }
          catch (err) { $('vv-note').textContent = 'Could not save: ' + err.message; }
        }
      }

      $('vv-list').addEventListener('click', (e) => {
        const p = e.target.closest('[data-play]');
        if (p) { e.stopPropagation(); return play(p.dataset.play); }
        const r = e.target.closest('[data-v]');
        if (r) choose(r.dataset.v);
      });
      $('vv-list').addEventListener('keydown', (e) => {
        if ((e.key === 'Enter' || e.key === ' ') && e.target.dataset && e.target.dataset.v) { e.preventDefault(); choose(e.target.dataset.v); }
      });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        db = fs.getFirestore(app);
        onAuthStateChanged(getAuth(app), (user) => {
          if (!user) return;
          uid = user.uid; authUser = user;
          refreshStatus(0);
          fs.onSnapshot(fs.doc(db, 'users', uid), (s) => {
            const d = s.exists() ? s.data() : {};
            if (!s.metadata.fromCache) refreshStatus(400);
            plan = d.plan || 'none';
            const want = V.find(x => x.id === d.voice) || V[0];
            voice = allowed(want) ? want.id : 'default';
            if (allowed(want)) showUpgrade(false);
            render();
          }, () => {});
        });
      } catch (e) { console.error('Voice picker:', e); }
    }
  </script>
"""

# ======================= Pricing page: Back button when coming from the app =======================

_DP_PRICING_BACK_JS = """
  <script>
    /* VB_BACK_MARKER */
    (function () {
      var from = new URLSearchParams(location.search).get('back');
      if (!from) return;
      var h2 = [].slice.call(document.querySelectorAll('h2')).find(function (h) { return /Simple pricing/.test(h.textContent); });
      var box = h2 ? h2.parentElement : null;
      if (!box || !box.parentElement) return;
      var row = document.createElement('div');
      row.className = 'max-w-[900px] mx-auto mb-8';
      row.innerHTML = '<a href="' + (/^[a-z-]+$/.test(from) ? from : 'solana') + '.html" class="inline-flex items-center gap-1.5 text-[14px] font-medium text-neutral-500 hover:text-black transition">' +
        '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>Back</a>';
      row.querySelector('a').addEventListener('click', function (e) {
        if (document.referrer && document.referrer.indexOf(location.host) !== -1 && history.length > 1) { e.preventDefault(); history.back(); }
      });
      box.parentElement.insertBefore(row, box);
    })();
  </script>
"""

# ======================= Dashboard: "What does your business do?" (asked once after sign-up) =======================

_DP_ONBOARD_JS = """
  <style>
    /* VO_ONBOARD_CSS */
    .vo-row { display: grid; grid-template-columns: minmax(0,1fr) 128px 36px; gap: 8px; align-items: center;
      max-height: 64px; opacity: 1; overflow: hidden; transition: max-height .24s ease, opacity .2s ease, margin .24s ease; margin-bottom: 8px; }
    .vo-row.vo-in { max-height: 0; opacity: 0; margin-bottom: 0; }
    .vo-chip { animation: voChip .25s ease both; }
    @keyframes voChip { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
  </style>
  <script type="module">
    /* VO_ONBOARD_MARKER */
    const root = document.documentElement;
    const $ = (id) => document.getElementById(id);
    const AUTO = !!$('panel-home');                      // dashboard: ask once by itself after sign-up
    if (AUTO) root.classList.add('vo-check');           // the alerts prompt waits until this is answered
    const done = () => root.classList.remove('vo-check', 'vo-open');
    let skipped = false;
    try { skipped = sessionStorage.getItem('vo_skip') === '1'; } catch (e) {}
    const LENS = [10, 15, 20, 30, 45, 60, 75, 90, 120, 180, 240];
    const lenLabel = (m) => m < 60 ? m + ' min' : (m % 60 ? Math.floor(m / 60) + ' hr ' + (m % 60) + ' min' : (m / 60) + ' hr' + (m > 60 ? 's' : ''));
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
    const complete = (d) => !!(d && String(d.businessDescription || '').trim() && Array.isArray(d.services) && d.services.length);
    const blank = (d) => !String((d && d.businessDescription) || '').trim() && !(d && Array.isArray(d.services) && d.services.length);
    let mustFill = false;
    const REASONS = {
      test: 'Before your test call: tell Solana about your business so she answers like it’s yours.',
      testRequired: 'Add your business info to start a test call. Solana needs to know what you do to answer like it’s yours.',
      number: 'Before you get a number: tell Solana about your business so she’s ready for real callers.'
    };
    const fld = 'w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] focus:outline-none focus:border-gray-900 bg-white transition-colors';

    // ---------- the popup ----------
    const veil = document.createElement('div');
    veil.className = 'fixed inset-0 z-[90] bg-black/40 flex items-center justify-center p-4';
    veil.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .22s ease';
    veil.innerHTML =
      '<div id="vo-card" class="bg-white rounded-3xl w-full max-w-[560px] max-h-[92vh] overflow-y-auto p-7" style="transform:translateY(12px) scale(.98);transition:transform .28s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.2)">' +
        '<div class="text-[12px] font-semibold uppercase tracking-wide text-gray-400">Quick setup</div>' +
        '<h2 class="text-[22px] font-semibold text-gray-900 mt-1">Tell Solana about your business</h2>' +
        '<p class="text-[14px] text-gray-500 mt-1.5">She uses this to answer questions and book the right amount of time. You can change it any time on the Solana page.</p>' +
        '<div id="vo-reason" class="text-[13px] font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded-xl px-3.5 py-2.5" style="max-height:0;opacity:0;overflow:hidden;margin-top:0;padding-top:0;padding-bottom:0;transition:all .25s ease"></div>' +
        '<label class="block text-[13px] font-semibold text-gray-700 mt-5 mb-1.5">Business name</label>' +
        '<input id="vo-name" class="' + fld + '" placeholder="Acme Dental">' +
        '<label class="block text-[13px] font-semibold text-gray-700 mt-4 mb-1.5">What you do</label>' +
        '<textarea id="vo-about" rows="3" maxlength="1500" class="' + fld + ' leading-[1.5]" style="resize:vertical" ' +
          'placeholder="Family dental clinic in Houston. Most insurance accepted."></textarea>' +
        '<div class="flex items-end justify-between mt-5 mb-2">' +
          '<div><div class="text-[13px] font-semibold text-gray-700">Appointment types</div>' +
          '<div class="text-[12.5px] text-gray-500">What can people book, and how long does each take?</div></div>' +
        '</div>' +
        '<div id="vo-svcs"></div>' +
        '<button id="vo-add" type="button" class="inline-flex items-center gap-1.5 text-[13.5px] font-semibold text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors">' +
          '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>Add appointment type</button>' +
        '<div id="vo-err" class="hidden text-[13px] text-red-600 mt-2"></div>' +
        '<div class="flex items-center justify-end gap-2 mt-6">' +
          '<button id="vo-skip" class="px-4 py-2.5 rounded-xl text-[14px] font-semibold text-gray-600 hover:bg-gray-100 transition-colors">Skip for now</button>' +
          '<button id="vo-save" class="btn-primary min-w-[110px] px-5 py-2.5 rounded-xl text-[14px] font-semibold">Save</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(veil);
    const card = $('vo-card'), list = $('vo-svcs');
    let data = {}, uid = null, fs = null, db = null, resolver = null, gotData = false;
    const readyWaiters = [];

    function addRow(name, minutes, animate) {
      const row = document.createElement('div');
      row.className = 'vo-row' + (animate ? ' vo-in' : '');
      const sel = '<select class="vo-len ' + fld + '">' + LENS.map(m => '<option value="' + m + '"' + (m === minutes ? ' selected' : '') + '>' + lenLabel(m) + '</option>').join('') + '</select>';
      row.innerHTML = '<input class="vo-sname ' + fld + '" maxlength="60" placeholder="e.g. Cleaning" value="' + esc(name) + '">' + sel +
        '<button type="button" aria-label="Remove" class="vo-rm w-9 h-9 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-colors">' +
          '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
      if (!LENS.includes(minutes) && minutes) {
        row.querySelector('select').insertAdjacentHTML('beforeend', '<option value="' + minutes + '" selected>' + lenLabel(minutes) + '</option>');
      }
      row.querySelector('.vo-rm').onclick = () => {
        row.classList.add('vo-in');
        setTimeout(() => { row.remove(); if (!list.children.length) addRow('', 30, true); }, 240);
      };
      list.appendChild(row);
      if (animate) requestAnimationFrame(() => requestAnimationFrame(() => row.classList.remove('vo-in')));
      return row;
    }
    $('vo-add').onclick = () => { const r = addRow('', Number(data.appointmentLength) || 30, true); setTimeout(() => r.querySelector('input').focus(), 60); };

    function open(reason, required) {
      mustFill = !!required;
      $('vo-skip').textContent = mustFill ? 'Not now' : 'Skip for now';
      if (mustFill) reason = 'testRequired';
      $('vo-name').value = data.company || '';
      $('vo-about').value = data.businessDescription || '';
      list.innerHTML = '';
      const svcs = Array.isArray(data.services) ? data.services : [];
      if (svcs.length) svcs.forEach(s => addRow(s.name, Number(s.minutes) || 30, false));
      else addRow('', Number(data.appointmentLength) || 30, false);
      const r = $('vo-reason');
      if (reason && REASONS[reason]) {
        r.textContent = REASONS[reason];
        Object.assign(r.style, { maxHeight: '80px', opacity: '1', marginTop: '14px', paddingTop: '10px', paddingBottom: '10px' });
      } else Object.assign(r.style, { maxHeight: '0', opacity: '0', marginTop: '0', paddingTop: '0', paddingBottom: '0' });
      $('vo-err').classList.add('hidden');
      const b = $('vo-save'); b.disabled = false; b.textContent = 'Save';
      root.classList.add('vo-open');
      veil.style.opacity = '1'; veil.style.pointerEvents = 'auto';
      requestAnimationFrame(() => { card.style.transform = 'none'; });
      return new Promise((res) => { resolver = res; });
    }
    function close(result) {
      veil.style.opacity = '0'; veil.style.pointerEvents = 'none';
      card.style.transform = 'translateY(12px) scale(.98)';
      setTimeout(done, 220);
      const r = resolver; resolver = null;
      if (r) r(result);
    }
    $('vo-skip').onclick = () => { if (!mustFill) { try { sessionStorage.setItem('vo_skip', '1'); } catch (e) {} } close(false); };
    veil.addEventListener('mousedown', (e) => { if (e.target === veil) $('vo-skip').click(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && veil.style.pointerEvents === 'auto') $('vo-skip').click(); });
    $('vo-save').onclick = async () => {
      const err = $('vo-err');
      const about = $('vo-about').value.trim(), name = $('vo-name').value.trim();
      const services = [...list.querySelectorAll('.vo-row')].map(r => ({
        name: r.querySelector('.vo-sname').value.trim(), minutes: Number(r.querySelector('.vo-len').value) || 30
      })).filter(s => s.name);
      if (!about && !services.length) { err.textContent = 'Add what you do or at least one appointment type, or click Skip for now.'; err.classList.remove('hidden'); return; }
      if (!uid || !fs) { err.textContent = 'Please sign in again.'; err.classList.remove('hidden'); return; }
      const btn = $('vo-save'); btn.disabled = true; btn.textContent = 'Saving…';
      try {
        const upd = { businessDescription: about, services };
        if (name) upd.company = name;
        await fs.setDoc(fs.doc(db, 'users', uid), upd, { merge: true });
        data = Object.assign({}, data, upd);
        close(true);
      } catch (e) { btn.disabled = false; btn.textContent = 'Save'; err.textContent = 'Could not save: ' + e.message; err.classList.remove('hidden'); }
    };

    const whenReady = () => gotData ? Promise.resolve() : new Promise((res) => { readyWaiters.push(res); setTimeout(res, 1200); });
    window.vcBusiness = {
      open: (reason) => open(reason),
      // Used before a test call / buying a number: pops up again until it's filled in (still skippable).
      // A test call with no business info at all can't start until it's added (closing just cancels the call).
      ensure: async (reason) => {
        await whenReady();
        if (complete(data)) return true;
        const required = reason === 'test' && blank(data);
        const saved = await open(reason, required);
        return required ? !!saved : true;
      },
      data: () => data
    };

    // ---------- Solana page: show the list under "What your business does" ----------
    function renderChips() {
      const about = $('vz-about');
      if (!about) return;
      let box = $('vo-chipbox');
      if (!box) {
        box = document.createElement('div');
        box.id = 'vo-chipbox';
        box.className = 'mt-4';
        box.innerHTML = '<div class="flex items-center justify-between mb-1.5"><label class="text-[13px] font-semibold text-gray-700">Appointment types</label>' +
          '<button id="vo-edit" type="button" class="text-[12.5px] font-semibold text-gray-600 hover:text-black underline underline-offset-2">Edit</button></div>' +
          '<div id="vo-chips" class="flex flex-wrap gap-1.5"></div>';
        (about.parentElement || about).appendChild(box);
        $('vo-edit').onclick = () => open();
      }
      const svcs = Array.isArray(data.services) ? data.services : [];
      $('vo-chips').innerHTML = svcs.length
        ? svcs.map((s, i) => '<span class="vo-chip inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-1 text-[12.5px]" style="animation-delay:' + (i * 30) + 'ms">' +
            '<span class="font-semibold text-gray-900">' + esc(s.name) + '</span><span class="text-gray-400">' + lenLabel(Number(s.minutes) || 30) + '</span></span>').join('')
        : '<span class="text-[12.5px] text-gray-400">None yet. Add them so Solana books the right amount of time.</span>';
    }

    try {
""" + _DP_FB + """
      const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
      db = fs.getFirestore(app);
      onAuthStateChanged(getAuth(app), (user) => {
        if (!user) return done();
        uid = user.uid;
        let asked = false;
        fs.onSnapshot(fs.doc(db, 'users', uid), (snap) => {
          data = snap.exists() ? snap.data() : {};
          renderChips();
          if (!gotData && (snap.exists() || !snap.metadata.fromCache)) { gotData = true; readyWaiters.splice(0).forEach(f => f()); }
          if (snap.metadata.fromCache) return;
          if (asked || !AUTO) return;
          asked = true;
          if (skipped || String(data.businessDescription || '').trim()) return done();
          open();
        }, () => done());
      });
    } catch (e) { done(); }
    setTimeout(() => { if (!root.classList.contains('vo-open')) root.classList.remove('vo-check'); }, 6000);
  </script>
"""

# ======================= Solana page: "What your business does" field =======================

_DP_ABOUT_JS = """
  <script type="module">
    /* VZ_ABOUT_MARKER */
    const $ = (id) => document.getElementById(id);
    const prompt = $('system-prompt');
    const anchor = prompt ? prompt.parentElement : null;
    if (anchor && anchor.parentNode) {
      const box = document.createElement('div');
      box.innerHTML =
        '<label class="block text-[13px] font-semibold text-gray-700 mb-1.5">What your business does</label>' +
        '<textarea id="vz-about" rows="4" maxlength="1500" placeholder="e.g. Family dental clinic. Cleanings, fillings, whitening. Most insurance accepted." ' +
          'class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[13.5px] leading-[1.55] focus:outline-none focus:border-gray-400 bg-white" style="resize:vertical"></textarea>' +
        '<p id="vz-note" class="text-[12px] text-gray-400 mt-1.5">Solana only helps with things related to this.</p>';
      anchor.parentNode.insertBefore(box, anchor);
      const ta = $('vz-about'), note = $('vz-note');
      let uid = null, fs = null, db = null, saved = '';
      async function save() {
        const v = ta.value.trim();
        if (!uid || !fs || v === saved) return;
        note.textContent = 'Saving…';
        try { await fs.updateDoc(fs.doc(db, 'users', uid), { businessDescription: v }); saved = v; note.textContent = 'Saved. Used on your next call.'; }
        catch (e) { note.textContent = 'Could not save: ' + e.message; }
      }
      ta.addEventListener('blur', save);
      let t = null;
      ta.addEventListener('input', () => { clearTimeout(t); t = setTimeout(save, 1200); });
      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        db = fs.getFirestore(app);
        onAuthStateChanged(getAuth(app), (user) => {
          if (!user) return;
          uid = user.uid;
          fs.onSnapshot(fs.doc(db, 'users', uid), (s) => {
            const v = (s.exists() && s.data().businessDescription) || '';
            if (document.activeElement !== ta) { ta.value = v; saved = v.trim(); }
          }, () => {});
        });
      } catch (e) {}
    }
  </script>
"""

# ======================= Solana page: name + prompt save by themselves (no Save button) =======================

_DP_AUTOSAVE_JS = """
  <script type="module">
    /* VQ_AUTOSAVE_MARKER */
    const $ = (id) => document.getElementById(id);
    const btn = $('save-prompt'), nameIn = $('agent-name'), promptIn = $('system-prompt');
    if (btn && nameIn && promptIn) {
      btn.style.display = 'none';                          // kept in the page (other scripts use it as an anchor)
      const st = document.createElement('span');
      st.id = 'vq-state';
      st.className = 'ml-auto inline-flex items-center gap-1.5 text-[12px] text-gray-400';
      st.style.cssText = 'opacity:0;transition:opacity .2s ease';
      const row = $('vs-reset') ? $('vs-reset').parentElement : null;
      if (row) { row.classList.remove('justify-start'); row.classList.add('justify-between'); row.appendChild(st); }
      else promptIn.insertAdjacentElement('afterend', st);
      const CHECK = '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
      let hideT = null;
      const show = (html, color, stay) => {
        clearTimeout(hideT);
        st.innerHTML = html; st.style.color = color || ''; st.style.opacity = '1';
        if (!stay) hideT = setTimeout(() => { st.style.opacity = '0'; }, 1800);
      };

      let uid = null, fs = null, db = null, ready = false, last = null, timer = null, dirty = false;
      const current = () => ({ agentName: nameIn.value.trim() || 'Solana', systemPrompt: promptIn.value.trim() });
      async function save() {
        clearTimeout(timer);
        if (!ready || !uid || !fs || !dirty) return;
        const data = current();
        if (last && data.agentName === last.agentName && data.systemPrompt === last.systemPrompt) return;
        show('Saving…', '', true);
        try {
          await fs.setDoc(fs.doc(db, 'users', uid), data, { merge: true });
          last = data; dirty = false;
          show(CHECK + 'Saved', '#15803d');
        } catch (e) { show('Couldn’t save: ' + e.message, '#dc2626', true); }
      }
      const soon = () => { dirty = true; clearTimeout(timer); timer = setTimeout(save, 700); };
      nameIn.addEventListener('input', soon);
      promptIn.addEventListener('input', soon);
      nameIn.addEventListener('blur', save);
      promptIn.addEventListener('blur', save);
      document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('#vs-reset')) setTimeout(soon, 0); });
      window.addEventListener('beforeunload', () => { if (dirty) save(); });

      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        db = fs.getFirestore(app);
        onAuthStateChanged(getAuth(app), (user) => {
          if (!user) return;
          uid = user.uid;
          // wait until the page has filled in the saved name + prompt, then start saving changes
          setTimeout(() => { last = current(); ready = true; if (dirty) save(); }, 1500);
        });
      } catch (e) {}
    }
  </script>
"""

# ======================= Calendar: clean black & white week view (Google Calendar style) =======================

_DP_GCAL_JS = """
  <style>
    /* VG_CAL_CSS */
    #vg-grid .vg-col { background-image: linear-gradient(to bottom, #eeeeee 1px, transparent 1px); }
    #vg-grid .vg-ev { transition: transform .12s ease, box-shadow .12s ease; }
    #vg-grid .vg-ev:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,.12); }
    #vg-scroll::-webkit-scrollbar { width: 8px; } #vg-scroll::-webkit-scrollbar-thumb { background: #e5e5e5; border-radius: 8px; }
  </style>
  <script type="module">
    /* VG_CAL_MARKER */
    const $ = (id) => document.getElementById(id);
    const wrap = document.querySelector('main > div');
    if (wrap && $('week-view')) {
      // Old calendar UI stays in the page (hidden) so older scripts don't crash.
      ['week-view', 'list-view'].forEach(id => { const e = $(id); if (e) e.style.display = 'none'; });
      const vb = document.querySelector('.view-btn'); if (vb && vb.parentElement) vb.parentElement.style.display = 'none';
      const pv = $('prev-week'); if (pv && pv.parentElement) pv.parentElement.style.display = 'none';

      const H = 52;                                   // px per hour
      const DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
      const CHEV = (d) => '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="' + d + '"/></svg>';
      const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
      const pad = (n) => String(n).padStart(2, '0');
      const ymd = (d) => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
      const hm = (d) => pad(d.getHours()) + ':' + pad(d.getMinutes());
      const t12 = (d) => d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
      const startOfWeek = (d) => { const x = new Date(d); x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; };
      const toDate = (v) => v && v.toDate ? v.toDate() : (v ? new Date(v) : null);

      const sec = document.createElement('section');
      sec.id = 'vg-cal';
      sec.className = 'mb-8';
      sec.innerHTML =
        '<div class="flex items-center gap-1.5 flex-wrap mb-4">' +
          '<button id="vg-today" class="px-4 py-2 rounded-full border border-gray-300 text-[13.5px] font-semibold text-gray-800 hover:bg-gray-50 mr-1">Today</button>' +
          '<button id="vg-prev" aria-label="Previous week" class="w-9 h-9 rounded-full flex items-center justify-center text-gray-700 hover:bg-gray-100">' + CHEV('M15 18l-6-6 6-6') + '</button>' +
          '<button id="vg-next" aria-label="Next week" class="w-9 h-9 rounded-full flex items-center justify-center text-gray-700 hover:bg-gray-100">' + CHEV('M9 18l6-6-6-6') + '</button>' +
          '<h2 id="vg-title" class="text-[21px] font-semibold text-gray-900 ml-2 tracking-[-0.01em]"></h2>' +
          '<div class="ml-auto flex items-center gap-2">' +
            '<div id="vg-tg" class="relative flex bg-gray-100 rounded-full p-1">' +
              '<span id="vg-pill" class="absolute top-1 bottom-1 rounded-full bg-white shadow-sm" style="transition:transform .22s cubic-bezier(.4,0,.2,1), width .22s cubic-bezier(.4,0,.2,1)"></span>' +
              '<button data-v="week" class="vg-v relative px-4 py-1.5 rounded-full text-[13.5px] font-semibold">Week</button>' +
              '<button data-v="list" class="vg-v relative px-4 py-1.5 rounded-full text-[13.5px] font-semibold">Upcoming</button>' +
            '</div>' +
            '<button id="vg-ai" class="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-300 text-[13.5px] font-semibold text-gray-900 hover:bg-gray-50 transition-colors"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l1.9 5.6L19.5 9.5l-5.6 1.9L12 17l-1.9-5.6L4.5 9.5l5.6-1.9z"/><path d="M19 14l.9 2.6 2.6.9-2.6.9L19 21l-.9-2.6-2.6-.9 2.6-.9z" opacity=".7"/></svg>Organize</button>' +
            '<button id="vg-sel" style="display:none" class="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-300 text-[13.5px] font-semibold text-gray-900 hover:bg-gray-50 transition-colors">' +
              '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M8 12l3 3 5-6"/></svg><span id="vg-sel-t">Select</span></button>' +
            '<button id="vg-new" class="btn-primary inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-[13.5px] font-semibold">' +
              '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>New</button>' +
          '</div>' +
        '</div>' +
        '<div id="vg-week" class="rounded-2xl border border-gray-200 bg-white overflow-hidden" style="transition:opacity .15s ease">' +
          '<div id="vg-head" class="grid border-b border-gray-200" style="grid-template-columns:60px repeat(7,minmax(0,1fr))"></div>' +
          '<div id="vg-scroll" class="overflow-y-auto" style="max-height:620px"><div id="vg-grid" class="relative grid" style="grid-template-columns:60px repeat(7,minmax(0,1fr))"></div></div>' +
        '</div>' +
        '<div id="vg-list" class="hidden" style="transition:opacity .15s ease"></div>';
      const after = $('vk-card') || wrap.firstElementChild;
      after.insertAdjacentElement('afterend', sec);

      // ---------- Import to Google Calendar (VG_IMPORT) ----------
      const imp = document.createElement('div');
      imp.id = 'vg-import';
      imp.className = 'mt-4 flex items-center gap-4 flex-wrap rounded-2xl border border-gray-200 bg-white px-5 py-4';
      imp.innerHTML =
        '<div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center flex-shrink-0 text-gray-800">' +
          '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><path d="M12 14v5M9.5 16.5L12 19l2.5-2.5"/></svg></div>' +
        '<div class="flex-1 min-w-[220px]"><div class="text-[14.5px] font-semibold text-gray-900">Import to Google Calendar</div>' +
          '<div class="text-[13px] text-gray-500">Copy your upcoming appointments into Google Calendar in a few clicks.</div></div>' +
        '<div class="flex items-center gap-3">' +
          '<button id="vg-imp" class="btn-primary inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13.5px] font-semibold">' +
            '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>Import</button>' +
        '</div>' +
        '';
      sec.appendChild(imp);

      // ---------- modal ----------
      const veil = document.createElement('div');
      veil.className = 'fixed inset-0 z-[90] bg-black/40 flex items-center justify-center p-4';
      veil.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .18s ease';
      const fld = 'w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] text-gray-900 focus:outline-none focus:border-gray-900 bg-white';
      const lab = 'block text-[12.5px] font-semibold text-gray-600 mb-1.5';
      veil.innerHTML =
        '<form id="vg-form" class="bg-white rounded-3xl w-full max-w-[460px] p-6" style="transform:translateY(8px) scale(.98);transition:transform .22s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.22)">' +
          '<div class="flex items-center justify-between mb-4">' +
            '<h3 id="vg-mt" class="text-[19px] font-semibold text-gray-900">New appointment</h3>' +
            '<button type="button" id="vg-x" aria-label="Close" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-900 hover:bg-gray-100">' +
              '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
          '</div>' +
          '<input id="vg-title-in" placeholder="Add title" class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 px-0 py-2 text-[18px] font-semibold text-gray-900 placeholder-gray-400 focus:outline-none mb-4">' +
          '<div class="grid grid-cols-3 gap-2.5 mb-3">' +
            '<div class="col-span-3 sm:col-span-1"><label class="' + lab + '">Date</label><input id="vg-date" type="date" required class="' + fld + '"></div>' +
            '<div><label class="' + lab + '">Start</label><input id="vg-start" type="time" step="300" required class="' + fld + '"></div>' +
            '<div><label class="' + lab + '">Length</label><select id="vg-len" class="' + fld + '">' +
              [15, 30, 45, 60, 90, 120].map(n => '<option value="' + n + '">' + (n < 60 ? n + ' min' : (n / 60) + ' hr' + (n > 60 ? 's' : '')) + '</option>').join('') + '</select></div>' +
          '</div>' +
          '<div class="grid grid-cols-2 gap-2.5 mb-3">' +
            '<div><label class="' + lab + '">Customer</label><input id="vg-name" placeholder="Name" class="' + fld + '"></div>' +
            '<div><label class="' + lab + '">Phone</label><input id="vg-phone" type="tel" placeholder="(555) 123-4567" class="' + fld + '"></div>' +
          '</div>' +
          '<label class="' + lab + '">Notes</label><textarea id="vg-notes" rows="3" class="' + fld + '" style="resize:vertical"></textarea>' +
          '<div id="vg-src" class="hidden mt-3 text-[12.5px] text-gray-500"></div>' +
          '<div id="vg-err" class="hidden mt-3 text-[13px] text-red-600"></div>' +
          '<div class="flex items-center gap-2 mt-5">' +
            '<button type="button" id="vg-del" class="hidden text-[13.5px] font-semibold text-gray-500 hover:text-black underline underline-offset-2">Delete</button>' +
            '<div class="ml-auto flex items-center gap-2">' +
              '<button type="button" id="vg-cancel" class="px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-800 hover:bg-gray-50">Cancel</button>' +
              '<button type="submit" id="vg-save" class="btn-primary min-w-[96px] px-5 py-2.5 rounded-xl text-[14px] font-semibold">Save</button>' +
            '</div>' +
          '</div>' +
        '</form>';
      document.body.appendChild(veil);
      const form = $('vg-form');

      let weekStart = startOfWeek(new Date()), view = 'week', appts = [], hours = null, slot = 30, plan = 'none';
      let selectMode = false; const sel = new Set();          // VG_SELECT
      const CHK = (on, dark) => '<span class="absolute top-1 right-1 w-[18px] h-[18px] rounded-full flex items-center justify-center" style="' +
        (on ? 'background:' + (dark ? '#fff' : '#111') + ';color:' + (dark ? '#111' : '#fff')
            : 'border:2px solid ' + (dark ? 'rgba(255,255,255,.75)' : '#9ca3af') + ';background:transparent') + ';transition:all .15s ease">' +
        (on ? '<svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>' : '') + '</span>';
      let uid = null, fs = null, db = null, editing = null;

      // jump to a week from History ("Open in Calendar")
      const hd = (location.hash.match(/date=(\\d{4}-\\d{2}-\\d{2})/) || [])[1];
      if (hd) { const [y, m, d] = hd.split('-').map(Number); weekStart = startOfWeek(new Date(y, m - 1, d)); }

      function range() {
        let lo = 8, hi = 18;
        if (hours) DAYS.forEach(k => { const h = hours[k]; if (h && !h.closed) {
          lo = Math.min(lo, parseInt(h.open, 10)); hi = Math.max(hi, Math.ceil(parseInt(h.close, 10) + (+(h.close.split(':')[1] || 0) > 0 ? 1 : 0)));
        } });
        appts.forEach(a => { if (a._s >= weekStart && a._s < new Date(weekStart.getTime() + 7 * 864e5)) {
          lo = Math.min(lo, a._s.getHours()); hi = Math.max(hi, Math.min(24, a._e.getHours() + (a._e.getMinutes() ? 1 : 0)));
        } });
        return [Math.max(0, lo - 1), Math.min(24, hi + 1)];
      }

      function render() {
        const days = [...Array(7)].map((_, i) => { const d = new Date(weekStart); d.setDate(d.getDate() + i); return d; });
        const last = days[6];
        const m1 = days[0].toLocaleDateString('en-US', { month: 'long' }), m2 = last.toLocaleDateString('en-US', { month: 'long' });
        $('vg-title').textContent = m1 === m2 ? m1 + ' ' + last.getFullYear()
          : days[0].toLocaleDateString('en-US', { month: 'short' }) + ' – ' + last.toLocaleDateString('en-US', { month: 'short' }) + ' ' + last.getFullYear();
        if (view === 'list') return renderList();

        const today = ymd(new Date());
        $('vg-head').innerHTML = '<div></div>' + days.map(d => {
          const isT = ymd(d) === today;
          return '<div class="py-2.5 text-center border-l border-gray-100">' +
            '<div class="text-[11px] font-semibold tracking-[.08em] ' + (isT ? 'text-gray-900' : 'text-gray-500') + '">' + d.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase() + '</div>' +
            '<div class="mx-auto mt-1 w-9 h-9 rounded-full flex items-center justify-center text-[19px] ' +
              (isT ? 'bg-black text-white font-semibold' : 'text-gray-900') + '">' + d.getDate() + '</div></div>';
        }).join('');

        const [lo, hi] = range();
        const total = (hi - lo) * H;
        let g = '<div class="relative" style="height:' + total + 'px">';
        for (let h = lo + 1; h < hi; h++) {
          const lbl = new Date(2000, 0, 1, h).toLocaleTimeString('en-US', { hour: 'numeric' });
          g += '<div class="absolute right-2 text-[11px] text-gray-400 -translate-y-1/2" style="top:' + ((h - lo) * H) + 'px">' + lbl + '</div>';
        }
        g += '</div>';
        days.forEach((d, i) => {
          const key = DAYS[d.getDay()], hrs = hours ? hours[key] : null;
          let shade = '';
          const block = (fromMin, toMin) => {
            const a = Math.max(fromMin, lo * 60), b = Math.min(toMin, hi * 60);
            if (b > a) shade += '<div class="absolute left-0 right-0 bg-gray-50" style="top:' + ((a - lo * 60) / 60 * H) + 'px;height:' + ((b - a) / 60 * H) + 'px"></div>';
          };
          if (hours) {
            if (!hrs || hrs.closed) block(0, 1440);
            else {
              const [oh, om] = hrs.open.split(':').map(Number), [ch, cm] = hrs.close.split(':').map(Number);
              block(0, oh * 60 + om); block(ch * 60 + cm, 1440);
            }
          }
          g += '<div class="vg-col relative border-l border-gray-100 cursor-pointer" data-day="' + ymd(d) + '" style="height:' + total + 'px;background-size:100% ' + H + 'px">' + shade;
          // events, side by side when they overlap
          const evs = appts.filter(a => ymd(a._s) === ymd(d)).sort((a, b) => a._s - b._s);
          const lanes = [];
          evs.forEach(a => { let l = lanes.findIndex(end => end <= a._s); if (l === -1) { l = lanes.length; lanes.push(a._e); } else lanes[l] = a._e; a._lane = l; });
          evs.forEach(a => {
            const top = ((a._s.getHours() * 60 + a._s.getMinutes()) - lo * 60) / 60 * H;
            const ht = Math.max(22, (a._e - a._s) / 3600000 * H - 2);
            const n = lanes.length, w = 100 / n;
            const ai = a.source === 'ai';
            g += '<div class="vg-ev absolute rounded-lg px-2 py-1 overflow-hidden cursor-pointer ' +
                (ai ? 'bg-black text-white' : 'bg-white text-gray-900 border border-gray-900') + '" data-id="' + a.id + '" ' +
                'style="' + (sel.has(a.id) ? 'box-shadow:0 0 0 2px #fff,0 0 0 4px #111;z-index:5;' : '') + 'top:' + (top + 1) + 'px;height:' + ht + 'px;left:calc(' + (a._lane * w) + '% + 2px);width:calc(' + w + '% - 4px)">' +
              (selectMode ? CHK(sel.has(a.id), ai) : '') +
              '<div class="text-[12px] font-semibold leading-tight truncate' + (selectMode ? ' pr-5' : '') + '">' + esc(a.title || 'Appointment') + '</div>' +
              (ht > 30 ? '<div class="text-[11px] leading-tight truncate ' + (ai ? 'text-white/70' : 'text-gray-500') + '">' + t12(a._s) + ' – ' + t12(a._e) + '</div>' : '') +
              (ht > 46 && a.customerName ? '<div class="text-[11px] leading-tight truncate ' + (ai ? 'text-white/70' : 'text-gray-500') + '">' + esc(a.customerName) + '</div>' : '') +
            '</div>';
          });
          g += '</div>';
        });
        $('vg-grid').innerHTML = g;
        $('vg-grid').dataset.lo = lo;
      }

      function renderList() {
        const now = new Date();
        const up = appts.filter(a => a._e >= now).sort((a, b) => a._s - b._s);
        if (!up.length) {
          $('vg-list').innerHTML = '<div class="rounded-2xl border border-gray-200 bg-white py-16 text-center">' +
            '<div class="text-[15px] font-medium text-gray-800">No upcoming appointments</div>' +
            '<div class="text-[13px] text-gray-400 mt-1">Bookings from Solana and ones you add show up here.</div></div>';
          return;
        }
        let html = '<div class="rounded-2xl border border-gray-200 bg-white divide-y divide-gray-100">', lastDay = '';
        up.forEach(a => {
          const day = ymd(a._s);
          if (day !== lastDay) {
            lastDay = day;
            html += '<div class="px-5 pt-4 pb-2 text-[12px] font-semibold uppercase tracking-[.08em] text-gray-500 bg-[#fafafa]">' +
              a._s.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) + '</div>';
          }
          html += '<div class="vg-row flex items-center gap-4 px-5 py-3.5 cursor-pointer hover:bg-gray-50 transition-colors' + (sel.has(a.id) ? ' bg-gray-50' : '') + '" data-id="' + a.id + '">' +
            (selectMode ? '<span class="relative w-[18px] h-[18px] flex-shrink-0">' + CHK(sel.has(a.id), false).replace('absolute top-1 right-1', 'absolute inset-0') + '</span>' : '') +
            '<div class="w-[110px] flex-shrink-0 text-[13.5px] font-semibold text-gray-900">' + t12(a._s) + '<div class="text-[12px] font-normal text-gray-400">' + t12(a._e) + '</div></div>' +
            '<div class="w-1 self-stretch rounded-full ' + (a.source === 'ai' ? 'bg-black' : 'bg-gray-300') + '"></div>' +
            '<div class="flex-1 min-w-0"><div class="text-[14.5px] font-semibold text-gray-900 truncate">' + esc(a.title || 'Appointment') + '</div>' +
            '<div class="text-[13px] text-gray-500 truncate">' + esc([a.customerName, a.customerPhone].filter(Boolean).join(' · ')) + '</div></div>' +
            (a.source === 'ai' ? '<span class="text-[10.5px] font-bold uppercase tracking-wide bg-black text-white rounded-full px-2 py-0.5">Solana</span>' : '') +
          '</div>';
        });
        $('vg-list').innerHTML = html + '</div>';
      }

      // ---------- toggle ----------
      const tg = $('vg-tg');
      function movePill(anim) {
        const b = tg.querySelector('[data-v="' + view + '"]'), p = $('vg-pill');
        if (!anim) p.style.transition = 'none';
        p.style.width = b.offsetWidth + 'px'; p.style.transform = 'translateX(' + (b.offsetLeft - 4) + 'px)';
        if (!anim) { p.offsetWidth; p.style.transition = 'transform .22s cubic-bezier(.4,0,.2,1), width .22s cubic-bezier(.4,0,.2,1)'; }
        tg.querySelectorAll('.vg-v').forEach(x => { x.style.color = x.dataset.v === view ? '#111827' : '#6b7280'; });
      }
      function setView(v) {
        view = v; movePill(true);
        const show = $(v === 'week' ? 'vg-week' : 'vg-list'), hide = $(v === 'week' ? 'vg-list' : 'vg-week');
        hide.classList.add('hidden'); show.style.opacity = '0'; show.classList.remove('hidden');
        ['vg-prev', 'vg-next'].forEach(id => { $(id).style.visibility = v === 'week' ? 'visible' : 'hidden'; });
        render(); requestAnimationFrame(() => { show.style.opacity = '1'; });
      }
      tg.querySelectorAll('.vg-v').forEach(b => b.addEventListener('click', () => setView(b.dataset.v)));
      requestAnimationFrame(() => movePill(false));
      window.addEventListener('resize', () => movePill(false));
      const fadeWeek = (fn) => { const w = $('vg-week'); w.style.opacity = '0'; setTimeout(() => { fn(); render(); w.style.opacity = '1'; }, 120); };
      $('vg-prev').addEventListener('click', () => fadeWeek(() => weekStart.setDate(weekStart.getDate() - 7)));
      $('vg-next').addEventListener('click', () => fadeWeek(() => weekStart.setDate(weekStart.getDate() + 7)));
      $('vg-today').addEventListener('click', () => fadeWeek(() => { weekStart = startOfWeek(new Date()); }));
      setInterval(() => { if (view === 'week') render(); }, 60000);   // keep the "now" line moving

      // ---------- open / save ----------
      function openModal(a, start) {
        editing = a || null;
        $('vg-mt').textContent = a ? 'Edit appointment' : 'New appointment';
        const s = a ? a._s : start, e = a ? a._e : new Date(start.getTime() + slot * 60000);
        $('vg-title-in').value = a ? (a.title || '') : '';
        $('vg-date').value = ymd(s); $('vg-start').value = hm(s);
        const len = Math.round((e - s) / 60000);
        const sel = $('vg-len');
        if (![...sel.options].some(o => +o.value === len)) sel.insertAdjacentHTML('beforeend', '<option value="' + len + '">' + len + ' min</option>');
        sel.value = String(len);
        $('vg-name').value = a ? (a.customerName || '') : ''; $('vg-phone').value = a ? (a.customerPhone || '') : '';
        $('vg-notes').value = a ? (a.notes || '') : '';
        $('vg-del').classList.toggle('hidden', !a);
        const src = $('vg-src');
        if (a && a.source === 'ai') {
          src.innerHTML = 'Booked by Solana on a call' + (a.callId ? ' · <a href="history.html#call=' + esc(a.callId) + '" class="font-semibold text-gray-900 underline underline-offset-2">View call</a>' : '');
          src.classList.remove('hidden');
        } else src.classList.add('hidden');
        $('vg-err').classList.add('hidden');
        veil.style.opacity = '1'; veil.style.pointerEvents = 'auto';
        requestAnimationFrame(() => { form.style.transform = 'none'; });
        setTimeout(() => $('vg-title-in').focus(), 60);
      }
      function closeModal() {
        veil.style.opacity = '0'; veil.style.pointerEvents = 'none';
        form.style.transform = 'translateY(8px) scale(.98)';
        editing = null;
      }
      $('vg-x').addEventListener('click', closeModal);
      $('vg-cancel').addEventListener('click', closeModal);
      veil.addEventListener('mousedown', (e) => { if (e.target === veil) closeModal(); });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && veil.style.pointerEvents === 'auto') closeModal(); });

      $('vg-new').addEventListener('click', () => {
        const s = new Date(); s.setMinutes(Math.ceil(s.getMinutes() / 30) * 30, 0, 0); s.setHours(s.getHours() + 1);
        openModal(null, s);
      });
      $('vg-grid').addEventListener('click', (e) => {
        const ev = e.target.closest('.vg-ev');
        if (ev && !selectMode && (e.shiftKey || e.ctrlKey || e.metaKey)) { selectMode = true; return toggleSel(ev.dataset.id); }
        if (selectMode) { if (ev) toggleSel(ev.dataset.id); return; }
        if (ev) { const a = appts.find(x => x.id === ev.dataset.id); if (a) openModal(a); return; }
        const col = e.target.closest('.vg-col');
        if (!col) return;
        const r = col.getBoundingClientRect();
        const lo = +($('vg-grid').dataset.lo || 0);
        let mins = lo * 60 + Math.floor(((e.clientY - r.top) / H * 60) / slot) * slot;
        const [y, m, d] = col.dataset.day.split('-').map(Number);
        openModal(null, new Date(y, m - 1, d, Math.floor(mins / 60), mins % 60));
      });
      $('vg-list').addEventListener('click', (e) => {
        const row = e.target.closest('.vg-row'); if (!row) return;
        if (selectMode) return toggleSel(row.dataset.id);
        const a = appts.find(x => x.id === row.dataset.id); if (a) openModal(a);
      });

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const err = $('vg-err');
        if (!uid || !fs) { err.textContent = 'Please sign in again.'; err.classList.remove('hidden'); return; }
        const [y, m, d] = $('vg-date').value.split('-').map(Number), [hh, mm] = $('vg-start').value.split(':').map(Number);
        if (!y || isNaN(hh)) { err.textContent = 'Pick a date and start time.'; err.classList.remove('hidden'); return; }
        const s = new Date(y, m - 1, d, hh, mm), en = new Date(s.getTime() + (+$('vg-len').value || slot) * 60000);
        const data = {
          title: $('vg-title-in').value.trim() || 'Appointment',
          customerName: $('vg-name').value.trim(), customerPhone: $('vg-phone').value.trim(),
          notes: $('vg-notes').value.trim(),
          start: fs.Timestamp.fromDate(s), end: fs.Timestamp.fromDate(en)
        };
        const btn = $('vg-save'); btn.disabled = true; btn.textContent = 'Saving…';
        try {
          if (editing) await fs.updateDoc(fs.doc(db, 'users', uid, 'appointments', editing.id), data);
          else await fs.addDoc(fs.collection(db, 'users', uid, 'appointments'), Object.assign(data, { source: 'manual', createdAt: fs.serverTimestamp() }));
          closeModal();
        } catch (ex) { err.textContent = 'Could not save: ' + ex.message; err.classList.remove('hidden'); }
        btn.disabled = false; btn.textContent = 'Save';
      });
      // ---------- Google Calendar import file ----------
      const p2 = (n) => String(n).padStart(2, '0');
      const csvDate = (d) => p2(d.getMonth() + 1) + '/' + p2(d.getDate()) + '/' + d.getFullYear();
      const csvTime = (d) => { let h = d.getHours(); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return p2(h) + ':' + p2(d.getMinutes()) + ' ' + ap; };
      const CRLF = String.fromCharCode(13, 10), LF = String.fromCharCode(10), CR = String.fromCharCode(13);
      const cq = (v) => '"' + String(v == null ? '' : v).split(CR).join(' ').split(LF).join(' ').split('"').join('""') + '"';
      function buildCsv(list) {
        const rows = [['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'All Day Event', 'Description', 'Location', 'Private']];
        list.forEach(a => {
          const desc = [a.customerName && ('Customer: ' + a.customerName), a.customerPhone && ('Phone: ' + a.customerPhone),
            a.notes && ('Notes: ' + a.notes), a.source === 'ai' ? 'Booked by Solana (Vocallus)' : 'Added in Vocallus'].filter(Boolean).join(' | ');
          rows.push([(a.title || 'Appointment') + (a.customerName ? ' - ' + a.customerName : ''),
            csvDate(a._s), csvTime(a._s), csvDate(a._e), csvTime(a._e), 'False', desc, '', 'True']);
        });
        return rows.map(r => r.map(cq).join(',')).join(CRLF) + CRLF;
      }
      // In-page popup: download the CSV + step-by-step import instructions (VG_IMPORT_MODAL)
      const iv = document.createElement('div');
      iv.className = 'fixed inset-0 z-[92] bg-black/40 flex items-center justify-center p-4';
      iv.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .2s ease';
      const STEP = (n, html) => '<li class="flex gap-3"><span class="w-6 h-6 rounded-full bg-gray-900 text-white text-[12px] font-bold flex items-center justify-center flex-shrink-0 mt-[1px]">' + n + '</span><span class="text-[14px] text-gray-700 leading-[1.55]">' + html + '</span></li>';
      iv.innerHTML =
        '<div id="vg-ic" class="bg-white rounded-3xl w-full max-w-[520px] max-h-[90vh] overflow-y-auto p-7" style="transform:translateY(10px) scale(.98);transition:transform .26s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.22)">' +
          '<div class="flex items-start justify-between gap-4">' +
            '<div><div class="text-[12px] font-semibold uppercase tracking-wide text-gray-400">Google Calendar</div>' +
            '<h3 class="text-[21px] font-semibold text-gray-900 mt-0.5">Import your appointments</h3>' +
            '<p id="vg-icount" class="text-[14px] text-gray-500 mt-1"></p></div>' +
            '<button id="vg-ix" aria-label="Close" class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-colors flex-shrink-0">' +
              '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
          '</div>' +
          '<div id="vg-ipre" class="mt-4 rounded-2xl border border-gray-100 bg-gray-50 divide-y divide-gray-100 text-[13px]"></div>' +
          '<div class="flex flex-wrap gap-2 mt-5">' +
            '<button id="vg-icsv" class="btn-primary inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-[14px] font-semibold">' +
              '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>Download CSV</button>' +
            '<a id="vg-igo" href="https://calendar.google.com/calendar/r/settings/export" target="_blank" rel="noopener" class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-900 hover:bg-gray-50 transition-colors">' +
              'Open Google Calendar<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg></a>' +
          '</div>' +
          '<div id="vg-idone" class="text-[13px] font-semibold text-green-700" style="max-height:0;opacity:0;overflow:hidden;transition:max-height .25s ease, opacity .25s ease, margin .25s ease"></div>' +
          '<div class="text-[13px] font-semibold text-gray-900 mt-6 mb-3">How to import</div>' +
          '<ol class="space-y-3">' +
            STEP(1, 'Click <b>Download CSV</b>. It saves <b>vocallus-appointments.csv</b> to your Downloads.') +
            STEP(2, 'Click <b>Open Google Calendar</b>. It opens the <b>Import &amp; export</b> settings in a new tab.') +
            STEP(3, 'Under <b>Import</b>, click <b>Select file from your computer</b> and pick <b>vocallus-appointments.csv</b>.') +
            STEP(4, 'Choose the calendar to add them to, then click <b>Import</b>. Done!') +
          '</ol>' +
          '<p class="text-[12.5px] text-gray-400 mt-5 leading-[1.5]">This adds a copy of these appointments. Importing the same file twice makes duplicates, so next time only import new bookings. Import works on a computer, not the Google Calendar phone app.</p>' +
        '</div>';
      document.body.appendChild(iv);
      const ic = $('vg-ic');
      let impList = [];
      const upcoming = () => { const t = new Date(); t.setHours(0, 0, 0, 0); return appts.filter(a => a._e && a._e >= t).sort((a, b) => a._s - b._s); };
      function openImport() {
        impList = upcoming();
        const n = impList.length;
        $('vg-icount').textContent = n ? n + ' upcoming appointment' + (n === 1 ? '' : 's') + ' ready to add.' : 'No upcoming appointments yet.';
        $('vg-ipre').innerHTML = n ? impList.slice(0, 4).map(a =>
            '<div class="flex items-center gap-3 px-4 py-2.5"><span class="w-[118px] flex-shrink-0 font-semibold text-gray-900">' +
              a._s.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) + '</span>' +
            '<span class="text-gray-500 w-[64px] flex-shrink-0">' + t12(a._s) + '</span>' +
            '<span class="truncate text-gray-700">' + esc(a.title || 'Appointment') + (a.customerName ? ' · ' + esc(a.customerName) : '') + '</span></div>').join('') +
            (n > 4 ? '<div class="px-4 py-2 text-gray-400">+ ' + (n - 4) + ' more</div>' : '')
          : '<div class="px-4 py-6 text-center text-gray-400">Bookings from Solana and ones you add will show here.</div>';
        $('vg-icsv').disabled = !n; $('vg-icsv').style.opacity = n ? '1' : '.45';
        const d = $('vg-idone'); d.style.maxHeight = '0'; d.style.opacity = '0'; d.style.marginTop = '0';
        iv.style.opacity = '1'; iv.style.pointerEvents = 'auto';
        requestAnimationFrame(() => { ic.style.transform = 'none'; });
      }
      function closeImport() {
        iv.style.opacity = '0'; iv.style.pointerEvents = 'none';
        ic.style.transform = 'translateY(10px) scale(.98)';
      }
      $('vg-imp').addEventListener('click', openImport);
      $('vg-ix').addEventListener('click', closeImport);
      iv.addEventListener('mousedown', (e) => { if (e.target === iv) closeImport(); });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && iv.style.pointerEvents === 'auto') closeImport(); });
      $('vg-icsv').addEventListener('click', () => {
        if (!impList.length) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([buildCsv(impList)], { type: 'text/csv' }));
        a.download = 'vocallus-appointments.csv';
        a.click();          // not added to the page, so the app's link router never sees it
        setTimeout(() => URL.revokeObjectURL(a.href), 5000);
        const d = $('vg-idone');
        d.innerHTML = '✓ Downloaded vocallus-appointments.csv. Now click <b>Open Google Calendar</b>.';
        d.style.maxHeight = '60px'; d.style.opacity = '1'; d.style.marginTop = '12px';
      });

      // ---------- "Solana just booked" toast ----------
      const toast = document.createElement('div');
      toast.className = 'fixed right-5 bottom-5 z-[80] w-[320px] rounded-2xl bg-black text-white p-4';
      toast.style.cssText += ';opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .25s ease, transform .3s cubic-bezier(.16,1,.3,1);box-shadow:0 18px 50px rgba(0,0,0,.3)';
      document.body.appendChild(toast);
      let toastT = null;
      function flash(id) {
        const el = document.querySelector('.vg-ev[data-id="' + id + '"], .vg-row[data-id="' + id + '"]');
        if (!el) return;
        el.scrollIntoView({ block: 'center', behavior: 'smooth' });
        try { el.animate([{ boxShadow: '0 0 0 0 rgba(0,0,0,.55)' }, { boxShadow: '0 0 0 12px rgba(0,0,0,0)' }], { duration: 900, iterations: 3 }); } catch (e) {}
      }
      function newBooking(a) {
        toast.innerHTML = '<div class="text-[11px] font-bold uppercase tracking-wider text-white/60">New booking from Solana</div>' +
          '<div class="text-[15px] font-semibold mt-1 truncate">' + esc(a.title || 'Appointment') + (a.customerName ? ' · ' + esc(a.customerName) : '') + '</div>' +
          '<div class="text-[13px] text-white/70 mt-0.5">' + a._s.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) + ', ' + t12(a._s) + '</div>' +
          '<div class="flex gap-2 mt-3"><button data-t="show" class="px-3 py-1.5 rounded-lg bg-white text-black text-[12.5px] font-semibold">Show</button>' +
          '<button data-t="x" class="px-3 py-1.5 rounded-lg text-white/70 hover:text-white text-[12.5px] font-semibold">Dismiss</button></div>';
        toast.style.opacity = '1'; toast.style.transform = 'none'; toast.style.pointerEvents = 'auto';
        clearTimeout(toastT); toastT = setTimeout(hideToast, 9000);
        toast.onclick = (e) => {
          const t = e.target.closest('[data-t]'); if (!t) return;
          hideToast();
          if (t.dataset.t === 'show') {
            weekStart = startOfWeek(a._s);
            if (view !== 'week') setView('week'); else render();
            setTimeout(() => flash(a.id), 80);
          }
        };
      }
      function hideToast() { toast.style.opacity = '0'; toast.style.transform = 'translateY(12px)'; toast.style.pointerEvents = 'none'; }
      document.addEventListener('visibilitychange', () => { if (!document.hidden) render(); });

      // ---------- Select many: bar + bulk delete / edit ----------
      const bar = document.createElement('div');
      bar.className = 'fixed left-1/2 bottom-6 z-[85] flex items-center gap-1 rounded-2xl bg-black text-white pl-5 pr-2 py-2';
      bar.style.cssText += ';transform:translate(-50%,24px);opacity:0;pointer-events:none;transition:transform .28s cubic-bezier(.16,1,.3,1), opacity .2s ease;box-shadow:0 18px 50px rgba(0,0,0,.3)';
      const BB = 'px-3.5 py-2 rounded-xl text-[13.5px] font-semibold transition-colors';
      bar.innerHTML =
        '<span id="vg-scount" class="text-[13.5px] font-semibold mr-3 whitespace-nowrap">0 selected</span>' +
        '<button id="vg-sall" class="' + BB + ' text-white/80 hover:text-white hover:bg-white/10">Select all</button>' +
        '<button id="vg-sedit" class="' + BB + ' text-white/80 hover:text-white hover:bg-white/10">Edit</button>' +
        '<button id="vg-sdel" class="' + BB + ' text-red-300 hover:text-white hover:bg-red-600">Delete</button>' +
        '<button id="vg-sdone" aria-label="Done" class="ml-1 w-9 h-9 rounded-xl flex items-center justify-center text-white/70 hover:text-white hover:bg-white/10 transition-colors">' +
          '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
      document.body.appendChild(bar);
      function syncBar() {
        $('vg-scount').textContent = sel.size + ' selected';
        ['vg-sedit', 'vg-sdel'].forEach(id => { $(id).disabled = !sel.size; $(id).style.opacity = sel.size ? '1' : '.4'; });
        bar.style.transform = selectMode ? 'translate(-50%,0)' : 'translate(-50%,24px)';
        bar.style.opacity = selectMode ? '1' : '0'; bar.style.pointerEvents = selectMode ? 'auto' : 'none';
        $('vg-sel-t').textContent = selectMode ? 'Done' : 'Select';
        $('vg-sel').style.background = selectMode ? '#111' : ''; $('vg-sel').style.color = selectMode ? '#fff' : '';
      }
      function setSelect(on) { selectMode = on; if (!on) sel.clear(); syncBar(); render(); }
      function toggleSel(id) { sel.has(id) ? sel.delete(id) : sel.add(id); syncBar(); render(); }
      const inView = () => {
        if (view === 'list') { const now = new Date(); return appts.filter(a => a._e >= now); }
        const end = new Date(weekStart.getTime() + 7 * 864e5);
        return appts.filter(a => a._s >= weekStart && a._s < end);
      };
      $('vg-sel').addEventListener('click', () => setSelect(!selectMode));
      $('vg-sdone').addEventListener('click', () => setSelect(false));
      $('vg-sall').addEventListener('click', () => {
        const ids = inView().map(a => a.id), all = ids.length && ids.every(id => sel.has(id));
        ids.forEach(id => all ? sel.delete(id) : sel.add(id)); syncBar(); render();
      });
      document.addEventListener('keydown', (e) => {
        if (!selectMode || veil.style.pointerEvents === 'auto' || bv.style.pointerEvents === 'auto') return;
        if (/INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || '')) return;
        if (e.key === 'Escape') setSelect(false);
        if ((e.key === 'Delete' || e.key === 'Backspace') && sel.size) { e.preventDefault(); openBulk('delete'); }
      });

      // bulk popup (delete confirm / edit / AI organize)
      const bv = document.createElement('div');
      bv.className = 'fixed inset-0 z-[92] bg-black/40 flex items-center justify-center p-4';
      bv.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .2s ease';
      bv.innerHTML = '<div id="vg-bc" class="bg-white rounded-3xl w-full max-w-[460px] p-7" style="transform:translateY(10px) scale(.98);transition:transform .26s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.22)"></div>';
      document.body.appendChild(bv);
      const bc = $('vg-bc');
      let bBusy = false;
      function showBulk() { bv.style.opacity = '1'; bv.style.pointerEvents = 'auto'; requestAnimationFrame(() => { bc.style.transform = 'none'; }); }
      function closeBulk() { if (bBusy) return; try { document.activeElement && document.activeElement.blur(); } catch (e) {} bv.style.opacity = '0'; bv.style.pointerEvents = 'none'; bc.style.transform = 'translateY(10px) scale(.98)'; }
      bv.addEventListener('mousedown', (e) => { if (e.target === bv) closeBulk(); });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && bv.style.pointerEvents === 'auto') { e.stopPropagation(); closeBulk(); } }, true);
      const SPIN2 = '<svg class="w-4 h-4" style="animation:vgSpin .8s linear infinite" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>';
      if (!document.getElementById('vg-spin-css')) { const st = document.createElement('style'); st.id = 'vg-spin-css'; st.textContent = '@keyframes vgSpin{to{transform:rotate(360deg)}} @keyframes voChip{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}'; document.head.appendChild(st); }
      const fld2 = 'w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] text-gray-900 focus:outline-none focus:border-gray-900 bg-white';
      const lab2 = 'block text-[12.5px] font-semibold text-gray-600 mb-1.5';
      const BTN_ROW = (goLabel, red) =>
        '<div id="vg-berr" class="hidden mt-3 text-[13px] text-red-600"></div>' +
        '<div class="flex items-center justify-end gap-2 mt-6">' +
          '<button id="vg-bno" class="px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-800 hover:bg-gray-50 transition-colors">Cancel</button>' +
          '<button id="vg-bgo" class="min-w-[130px] px-5 py-2.5 rounded-xl text-[14px] font-semibold text-white transition-colors" style="background:' + (red ? '#dc2626' : '#111') + '">' + goLabel + '</button></div>';
      async function runBulk(label, work) {
        const go = $('vg-bgo'), err = $('vg-berr');
        if (bBusy) return;
        bBusy = true; go.disabled = true; err.classList.add('hidden');
        go.innerHTML = '<span class="inline-flex items-center gap-2">' + SPIN2 + label + '</span>';
        try { await work(); bBusy = false; closeBulk(); setSelect(false); }
        catch (ex) { bBusy = false; go.disabled = false; go.textContent = 'Try again'; err.textContent = 'Could not save: ' + ex.message; err.classList.remove('hidden'); }
      }
      function openBulk(kind) {
        const ids = [...sel].filter(id => appts.some(a => a.id === id));
        if (!ids.length) return;
        const n = ids.length, word = n + ' appointment' + (n === 1 ? '' : 's');
        if (kind === 'delete') {
          bc.innerHTML = '<h3 class="text-[20px] font-semibold text-gray-900">Delete ' + word + '?</h3>' +
            '<p class="text-[14px] text-gray-500 mt-2 leading-[1.6]">They are removed from your calendar and Solana can book those times again. This can’t be undone.</p>' + BTN_ROW('Delete', true);
          $('vg-bgo').onclick = () => runBulk('Deleting…', () => Promise.all(ids.map(id => fs.deleteDoc(fs.doc(db, 'users', uid, 'appointments', id)))));
        } else {
          bc.innerHTML = '<h3 class="text-[20px] font-semibold text-gray-900">Edit ' + word + '</h3>' +
            '<p class="text-[13.5px] text-gray-500 mt-1 mb-5">Only the fields you change are updated.</p>' +
            '<label class="' + lab2 + '">Title</label><input id="vg-btitle" placeholder="Keep current titles" class="' + fld2 + ' mb-3">' +
            '<div class="grid grid-cols-2 gap-2.5">' +
              '<div><label class="' + lab2 + '">Length</label><select id="vg-blen" class="' + fld2 + '"><option value="">Keep</option>' +
                [15, 30, 45, 60, 90, 120].map(m => '<option value="' + m + '">' + (m < 60 ? m + ' min' : (m / 60) + ' hr' + (m > 60 ? 's' : '')) + '</option>').join('') + '</select></div>' +
              '<div><label class="' + lab2 + '">Move</label><select id="vg-bmove" class="' + fld2 + '"><option value="0">Keep</option>' +
                '<option value="-10080">1 week earlier</option><option value="-1440">1 day earlier</option><option value="-60">1 hour earlier</option>' +
                '<option value="60">1 hour later</option><option value="1440">1 day later</option><option value="10080">1 week later</option></select></div>' +
            '</div>' + BTN_ROW('Save changes', false);
          $('vg-bgo').onclick = () => runBulk('Saving…', () => Promise.all(ids.map(id => {
            const a = appts.find(x => x.id === id);
            const mv = (+$('vg-bmove').value || 0) * 60000, len = +$('vg-blen').value, title = $('vg-btitle').value.trim();
            const s0 = new Date(a._s.getTime() + mv), e0 = len ? new Date(s0.getTime() + len * 60000) : new Date(a._e.getTime() + mv);
            const upd = {};
            if (title) upd.title = title;
            if (mv || len) { upd.start = fs.Timestamp.fromDate(s0); upd.end = fs.Timestamp.fromDate(e0); }
            return Object.keys(upd).length ? fs.updateDoc(fs.doc(db, 'users', uid, 'appointments', id), upd) : null;
          })));
        }
        $('vg-bno').onclick = closeBulk;
        showBulk();
      }
      $('vg-sdel').addEventListener('click', () => openBulk('delete'));
      $('vg-sedit').addEventListener('click', () => openBulk('edit'));

      // ---------- Organize (Max): fix double bookings, out-of-hours and duplicates (VG_ORGANIZE) ----------
      const SPARK_ICON = '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l1.9 5.6L19.5 9.5l-5.6 1.9L12 17l-1.9-5.6L4.5 9.5l5.6-1.9z"/><path d="M19 14l.9 2.6 2.6.9-2.6.9L19 21l-.9-2.6-2.6-.9 2.6-.9z" opacity=".7"/></svg>';
      const dayHours = (d) => {
        const h = hours ? hours[DAYS[d.getDay()]] : { open: '09:00', close: '17:00' };
        if (!h || h.closed) return null;
        const [oh, om] = String(h.open).split(':').map(Number), [ch, cm] = String(h.close).split(':').map(Number);
        return [oh * 60 + om, ch * 60 + cm];
      };
      const minsOf = (d) => d.getHours() * 60 + d.getMinutes();
      const overlaps = (s, e, list) => list.some(b => s < b._e2 && e > b._s2);
      // Next open time: later the same day first, then earlier that day, then the following days.
      function findSlot(fromDay, dur, others, earliest) {
        const step = Math.min(slot || 30, 30);
        const tryDay = (d, from) => {
          const hr = dayHours(d); if (!hr) return null;
          for (let t = Math.max(hr[0], from); t + dur <= hr[1]; t += step) {
            const s = new Date(d); s.setHours(0, 0, 0, 0); s.setMinutes(t);
            if (s < earliest) continue;
            if (!overlaps(s, new Date(s.getTime() + dur * 60000), others)) return s;
          }
          return null;
        };
        const day0 = new Date(fromDay);
        const hr0 = dayHours(day0);
        const after = hr0 ? Math.ceil((minsOf(day0) - hr0[0]) / step) * step + hr0[0] : 0;
        let s = tryDay(day0, after) || tryDay(day0, 0);
        for (let k = 1; !s && k < 14; k++) { const d = new Date(fromDay); d.setDate(d.getDate() + k); s = tryDay(d, 0); }
        return s;
      }
      function planOrganize() {
        const now = new Date(), earliest = new Date(now.getTime() + 30 * 60000), horizon = new Date(now.getTime() + 21 * 864e5);
        const list = appts.filter(a => a._s >= now && a._s < horizon).sort((a, b) => a._s - b._s)
          .map(a => Object.assign({}, a, { _s2: a._s, _e2: a._e }));
        const kept = [], fixes = [];
        list.forEach((a, i) => {
          const dur = Math.max(5, Math.round((a._e - a._s) / 60000));
          const dup = kept.find(k => +k._s2 === +a._s && (k.title || '') === (a.title || '') && (k.customerName || '') === (a.customerName || ''));
          if (dup) { fixes.push({ kind: 'delete', a, why: 'Duplicate' }); return; }
          const hr = dayHours(a._s);
          const outside = !hr || minsOf(a._s) < hr[0] || minsOf(a._s) + dur > hr[1];
          const clash = overlaps(a._s, a._e, kept);
          if (!outside && !clash) { kept.push(a); return; }
          const others = kept.concat(list.slice(i + 1).filter(x => !fixes.some(f => f.a.id === x.id)));
          const s = findSlot(a._s, dur, others, earliest);
          if (!s) { fixes.push({ kind: 'none', a, why: outside ? 'Outside your hours' : 'Double-booked' }); kept.push(a); return; }
          const moved = Object.assign({}, a, { _s2: s, _e2: new Date(s.getTime() + dur * 60000) });
          fixes.push({ kind: 'move', a, to: moved._s2, end: moved._e2, why: outside ? (hr ? 'Outside your hours' : 'Closed that day') : 'Double-booked' });
          kept.push(moved);
        });
        return fixes;
      }
      const when = (d) => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) + ', ' + t12(d);
      $('vg-ai').addEventListener('click', () => {
        if (plan !== 'max') {
          bc.innerHTML =
            '<div class="w-11 h-11 rounded-2xl bg-black text-white flex items-center justify-center mb-4">' + SPARK_ICON + '</div>' +
            '<div class="inline-flex items-center rounded-full bg-black text-white px-2 py-[2px] text-[10.5px] font-bold uppercase tracking-wider mb-2">Max</div>' +
            '<h3 class="text-[20px] font-semibold text-gray-900">Organize is a Max feature</h3>' +
            '<p class="text-[14px] text-gray-500 mt-2 leading-[1.6]">Organize tidies your calendar in one click: it finds double bookings, appointments outside your hours and duplicates, and moves them to the next open time. Upgrade to Max to use it.</p>' +
            '<div class="flex items-center justify-end gap-2 mt-6">' +
              '<button id="vg-bno" class="px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-800 hover:bg-gray-50 transition-colors">Not now</button>' +
              '<a href="pricing.html?back=calendar" class="btn-primary px-5 py-2.5 rounded-xl text-[14px] font-semibold">Upgrade to Max</a>' +
            '</div>';
          $('vg-bno').onclick = closeBulk;
          return showBulk();
        }
        const fixes = planOrganize(), doable = fixes.filter(f => f.kind !== 'none');
        const head = '<div class="w-11 h-11 rounded-2xl bg-black text-white flex items-center justify-center mb-4">' + SPARK_ICON + '</div>';
        if (!fixes.length) {
          bc.innerHTML = head + '<h3 class="text-[20px] font-semibold text-gray-900">All organized</h3>' +
            '<p class="text-[14px] text-gray-500 mt-2 leading-[1.6]">No double bookings, nothing outside your hours and no duplicates in the next 3 weeks.</p>' +
            '<div class="flex justify-end mt-6"><button id="vg-bno" class="btn-primary px-5 py-2.5 rounded-xl text-[14px] font-semibold">Done</button></div>';
          $('vg-bno').onclick = closeBulk;
          return showBulk();
        }
        bc.innerHTML = head +
          '<h3 class="text-[20px] font-semibold text-gray-900">Organize your calendar</h3>' +
          '<p class="text-[14px] text-gray-500 mt-1.5">' + fixes.length + ' thing' + (fixes.length === 1 ? '' : 's') + ' to tidy in the next 3 weeks. Untick anything you want to keep.</p>' +
          '<div class="mt-4 max-h-[46vh] overflow-y-auto rounded-2xl border border-gray-100 divide-y divide-gray-100">' +
          fixes.map((f, i) =>
            '<label class="flex items-start gap-3 px-4 py-3 ' + (f.kind === 'none' ? 'opacity-60' : 'cursor-pointer hover:bg-gray-50') + ' transition-colors" style="animation:voChip .25s ease both;animation-delay:' + (i * 35) + 'ms">' +
              '<input type="checkbox" data-i="' + i + '" class="vg-ofix mt-1 w-4 h-4 accent-black"' + (f.kind === 'none' ? ' disabled' : ' checked') + '>' +
              '<div class="min-w-0 flex-1"><div class="text-[14px] font-semibold text-gray-900 truncate">' + esc(f.a.title || 'Appointment') + (f.a.customerName ? ' · ' + esc(f.a.customerName) : '') + '</div>' +
              '<div class="text-[13px] text-gray-500 mt-0.5">' +
                (f.kind === 'move' ? when(f.a._s) + ' <span class="text-gray-400">→</span> <b class="text-gray-900">' + when(f.to) + '</b>'
                  : f.kind === 'delete' ? 'Remove duplicate at ' + when(f.a._s) : when(f.a._s) + ' · no open time found, move it yourself') + '</div></div>' +
              '<span class="text-[11px] font-semibold uppercase tracking-wide rounded-full px-2 py-0.5 flex-shrink-0 ' + (f.kind === 'delete' ? 'bg-gray-100 text-gray-600' : 'bg-black text-white') + '">' + f.why + '</span>' +
            '</label>').join('') +
          '</div>' +
          '<p class="text-[12.5px] text-gray-400 mt-3">Let customers know if their time changes.</p>' +
          BTN_ROW(doable.length ? 'Apply' : 'Done', false);
        $('vg-bno').onclick = closeBulk;
        $('vg-bgo').onclick = () => {
          const picked = [...bc.querySelectorAll('.vg-ofix:checked')].map(x => fixes[+x.dataset.i]);
          if (!picked.length) return closeBulk();
          runBulk('Organizing…', () => Promise.all(picked.map(f => f.kind === 'delete'
            ? fs.deleteDoc(fs.doc(db, 'users', uid, 'appointments', f.a.id))
            : fs.updateDoc(fs.doc(db, 'users', uid, 'appointments', f.a.id), { start: fs.Timestamp.fromDate(f.to), end: fs.Timestamp.fromDate(f.end) }))));
        };
        showBulk();
      });

      $('vg-del').addEventListener('click', async () => {
        if (!editing || !confirm('Delete this appointment?')) return;
        try { await fs.deleteDoc(fs.doc(db, 'users', uid, 'appointments', editing.id)); closeModal(); }
        catch (ex) { const err = $('vg-err'); err.textContent = 'Could not delete: ' + ex.message; err.classList.remove('hidden'); }
      });

      render();
      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        fs = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
        db = fs.getFirestore(app);
        onAuthStateChanged(getAuth(app), (user) => {
          if (!user) return;
          uid = user.uid;
          fs.onSnapshot(fs.doc(db, 'users', uid), (s) => {
            const d = s.exists() ? s.data() : {};
            hours = d.hours || null; slot = Number(d.appointmentLength) || 30; plan = d.plan || 'none'; render();
          }, () => {});
          let scrolled = false, firstLoad = true, unsub = null;
          const subscribe = () => {
            if (unsub) { try { unsub(); } catch (e) {} }
            unsub = fs.onSnapshot(fs.collection(db, 'users', uid, 'appointments'), (s) => {
              appts = s.docs.map(x => { const a = Object.assign({ id: x.id }, x.data()); a._s = toDate(a.start); a._e = toDate(a.end) || (a._s ? new Date(a._s.getTime() + slot * 60000) : null); return a; })
                .filter(a => a._s && !isNaN(a._s));
              const fresh = (firstLoad || s.metadata.fromCache) ? [] : s.docChanges()
                .filter(c => c.type === 'added' && !c.doc.metadata.hasPendingWrites)
                .map(c => appts.find(a => a.id === c.doc.id))
                .filter(a => a && a.source === 'ai' && (!a.createdAt || toDate(a.createdAt) > new Date(Date.now() - 180000)));
              if (!s.metadata.fromCache) firstLoad = false;
              render();
              if (!scrolled) {            // start the view near the first working hour
                scrolled = true;
                const lo = +($('vg-grid').dataset.lo || 0);
                $('vg-scroll').scrollTop = Math.max(0, (8 - lo) * H - 10);
              }
              if (fresh.length) newBooking(fresh[fresh.length - 1]);
            }, (err) => { console.error('Calendar sync:', err); setTimeout(subscribe, 3000); });   // reconnect if the live link drops
          };
          subscribe();
          window.addEventListener('online', subscribe);
        });
      } catch (e) { console.error('Calendar:', e); }
    }
  </script>
"""

# ======================= Checkout: reliable card form (waits for sign-in, shows errors) =======================

_DP_CHECKOUT_JS = """
  <style>
    /* VX_CHECKOUT_CSS */
    @keyframes vxPulse { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
    .vx-skel { background: #f1f1f1; border-radius: 12px; animation: vxPulse 1.4s ease-in-out infinite; }
    @keyframes vxSpin { to { transform: rotate(360deg); } }
    .vx-spin { animation: vxSpin .8s linear infinite; }
  </style>
  <script type="module">
    /* VX_CHECKOUT_MARKER */
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const $ = (id) => document.getElementById(id);
    const plan = (new URLSearchParams(location.search).get('plan') || '').toLowerCase();
    const wrap = $('pay-wrap'), host = $('payment-element'), oldBtn = $('pay-btn');
    if ((plan === 'pro' || plan === 'max') && wrap && host && oldBtn) {
      const PRICE = plan === 'pro' ? '$14.99/month' : '$99.99/month';
      const NAME = plan === 'pro' ? 'Pro' : 'Max';
      const pkMatch = [...document.scripts].map(s => s.textContent || '').join(' ').match(/Stripe\\(['"](pk_[A-Za-z0-9_]+)['"]\\)/);
      const PK = pkMatch ? pkMatch[1] : '';
      const SPIN = '<svg class="vx-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>';

      const btn = oldBtn.cloneNode(true);            // drop any old click handlers
      oldBtn.replaceWith(btn);
      btn.textContent = 'Subscribe — ' + PRICE;
      btn.disabled = true; btn.style.opacity = '.55'; btn.style.transition = 'opacity .2s ease';

      const status = document.createElement('div');
      status.className = 'hidden mb-5 rounded-xl border px-4 py-3 text-[14px] leading-[1.5]';
      status.style.transition = 'opacity .2s ease';
      wrap.insertBefore(status, wrap.firstChild);
      function say(kind, html) {
        status.className = 'mb-5 rounded-xl border px-4 py-3 text-[14px] leading-[1.5] ' +
          (kind === 'err' ? 'border-red-200 bg-red-50 text-red-800' : kind === 'ok' ? 'border-green-200 bg-green-50 text-green-800' : 'border-gray-200 bg-gray-50 text-gray-700');
        status.innerHTML = html;
      }
      function hideSay() { status.className = 'hidden'; }

      const skeleton = '<div id="vx-skel" style="transition:opacity .2s ease">' +
        '<div class="flex items-center gap-2 text-[13px] text-gray-500 mb-4">' + SPIN + 'Loading secure payment form…</div>' +
        '<div class="vx-skel h-11 mb-3"></div><div class="grid grid-cols-2 gap-3 mb-3"><div class="vx-skel h-11"></div><div class="vx-skel h-11"></div></div>' +
        '<div class="vx-skel h-11"></div></div>';

      let stripe = null, elements = null, starting = false;

      async function waitForStripe() {
        for (let i = 0; i < 100 && !window.Stripe; i++) await new Promise(r => setTimeout(r, 100));
        if (!window.Stripe) throw new Error("The payment form couldn't load. Turn off ad blockers for this page and refresh.");
        if (!PK) throw new Error('Payments are not set up on this page yet.');
        return window.Stripe(PK);
      }

      async function start(user) {
        if (starting) return;
        starting = true;
        hideSay();
        host.innerHTML = skeleton;
        btn.disabled = true; btn.style.opacity = '.55'; btn.textContent = 'Subscribe — ' + PRICE;
        try {
          stripe = stripe || await waitForStripe();
          const token = await user.getIdToken();
          let r;
          try {
            r = await fetch(BRIDGE + '/api/billing/subscribe', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
              body: JSON.stringify({ plan })
            });
          } catch (e) { throw new Error("Couldn't reach Vocallus. Check your connection and try again."); }
          const data = await r.json().catch(() => ({}));
          if (r.status === 409) {
            host.innerHTML = '';
            btn.style.display = 'none';
            say('ok', '<div class="font-semibold">' + (data.error || "You're already on " + NAME + '.') + '</div><a href="dashboard.html" class="inline-block mt-2 font-semibold underline">Go to dashboard</a>');
            return;
          }
          if (!r.ok) throw new Error(data.error || ('Checkout failed (' + r.status + ').'));
          if (data.updated) return done('Your plan was changed to ' + NAME + '.');
          if (!data.clientSecret) throw new Error('Checkout could not start. Please try again.');

          elements = stripe.elements({
            clientSecret: data.clientSecret,
            appearance: {
              theme: 'stripe',
              variables: { colorPrimary: '#111111', colorText: '#111111', colorDanger: '#b91c1c', fontFamily: 'Plus Jakarta Sans, Inter, sans-serif', borderRadius: '12px', spacingUnit: '4px' }
            },
            fonts: [{ cssSrc: 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600' }]
          });
          const pe = elements.create('payment', { layout: 'tabs' });
          const mount = document.createElement('div');
          mount.style.cssText = 'opacity:0;transition:opacity .25s ease;height:0;overflow:hidden';
          host.appendChild(mount);
          pe.on('ready', () => {
            const sk = $('vx-skel'); if (sk) sk.remove();
            mount.style.height = ''; mount.style.overflow = '';
            requestAnimationFrame(() => { mount.style.opacity = '1'; });
            btn.disabled = false; btn.style.opacity = '1';
          });
          pe.on('loaderror', (ev) => fail((ev && ev.error && ev.error.message) || "The payment form couldn't load.", user));
          pe.mount(mount);
        } catch (e) { fail(e.message, user); }
        finally { starting = false; }
      }

      function fail(msg, user) {
        host.innerHTML = '';
        btn.disabled = true; btn.style.opacity = '.55';
        say('err', '<div class="font-semibold">' + msg + '</div><button type="button" id="vx-retry" class="mt-2 font-semibold underline">Try again</button>');
        const rb = $('vx-retry'); if (rb) rb.addEventListener('click', () => start(user));
      }

      function done(title) {
        btn.style.display = 'none';
        host.style.transition = 'opacity .2s ease'; host.style.opacity = '0';
        setTimeout(() => {
          host.innerHTML =
            '<div class="text-center py-10">' +
              '<div class="w-14 h-14 mx-auto rounded-full bg-black text-white flex items-center justify-center mb-4">' +
                '<svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>' +
              '<div class="text-[20px] font-semibold text-gray-900">' + title + '</div>' +
              '<div class="text-[14px] text-gray-500 mt-1">Taking you to your dashboard…</div></div>';
          host.style.opacity = '1';
          hideSay();
        }, 200);
        setTimeout(() => { location.href = 'dashboard.html?paid=1'; }, 1600);
      }

      btn.addEventListener('click', async () => {
        if (!stripe || !elements || btn.disabled) return;
        hideSay();
        btn.disabled = true;
        btn.innerHTML = '<span class="inline-flex items-center gap-2">' + SPIN + 'Processing…</span>';
        const res = await stripe.confirmPayment({
          elements, redirect: 'if_required',
          confirmParams: { return_url: location.origin + '/Pages/dashboard.html?paid=1' }
        });
        if (res.error) {
          say('err', res.error.message || 'Payment failed. Please try another card.');
          btn.disabled = false; btn.textContent = 'Subscribe — ' + PRICE;
        } else {
          done("You're on " + NAME + '!');
        }
      });

      host.innerHTML = skeleton;
      try {
""" + _DP_FB + """
        const { getAuth, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        let seen = false;
        onAuthStateChanged(getAuth(app), (user) => {
          if (seen) return;
          seen = true;
          if (!user) {
            host.innerHTML = '';
            say('info', '<div class="font-semibold">Sign in to subscribe.</div><a href="login.html" class="inline-block mt-2 font-semibold underline">Sign in</a>');
            return;
          }
          start(user);
        });
      } catch (e) { fail("Couldn't start checkout. Refresh the page.", null); }
    }
  </script>
"""

# ======================= Billing tab: Delete account =======================

_DP_DELETE_JS = """
  <script type="module">
    /* VA_DELETE_MARKER */
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const $ = (id) => document.getElementById(id);
    const panel = $('panel-finances');
    if (panel) {
      const card = document.createElement('div');
      card.className = 'mt-8 rounded-3xl border border-gray-200 bg-white p-7';
      card.innerHTML =
        '<h2 class="text-[17px] font-semibold text-gray-900">Delete account</h2>' +
        '<p class="text-[14px] text-gray-500 mt-1.5 max-w-[620px]">Cancels your subscription, releases your Solana number, and permanently deletes your calls, calendar and settings. This can\\'t be undone.</p>' +
        '<button id="vdl-open" class="mt-4 px-4 py-2.5 rounded-xl border border-gray-300 text-[14px] font-semibold text-gray-900 hover:bg-gray-50">Delete account…</button>';
      panel.appendChild(card);

      const veil = document.createElement('div');
      veil.className = 'fixed inset-0 z-[95] bg-black/40 flex items-center justify-center p-4';
      veil.style.cssText += ';opacity:0;pointer-events:none;transition:opacity .18s ease';
      veil.innerHTML =
        '<div id="vdl-card" class="bg-white rounded-3xl w-full max-w-[460px] p-7" style="transform:translateY(8px) scale(.98);transition:transform .22s cubic-bezier(.16,1,.3,1);box-shadow:0 24px 60px rgba(0,0,0,.22)">' +
          '<h3 class="text-[20px] font-semibold text-gray-900">Delete your account?</h3>' +
          '<ul class="mt-3 space-y-1.5 text-[14px] text-gray-600 list-disc pl-5">' +
            '<li>Your subscription is cancelled right away</li>' +
            '<li>Your Solana phone number stops working</li>' +
            '<li>All calls, appointments and settings are erased</li>' +
          '</ul>' +
          '<label class="block text-[13px] font-semibold text-gray-700 mt-5 mb-1.5">Type <span class="font-mono">DELETE</span> to confirm</label>' +
          '<input id="vdl-in" autocomplete="off" class="w-full rounded-xl border border-gray-200 px-3.5 py-3 text-[14px] focus:outline-none focus:border-gray-900">' +
          '<div id="vdl-err" class="hidden mt-3 text-[13px] text-red-600"></div>' +
          '<div class="flex items-center justify-end gap-2 mt-6">' +
            '<button id="vdl-cancel" class="px-4 py-2.5 rounded-xl border border-gray-200 text-[14px] font-semibold text-gray-800 hover:bg-gray-50">Cancel</button>' +
            '<button id="vdl-go" disabled class="btn-primary min-w-[140px] px-5 py-2.5 rounded-xl text-[14px] font-semibold" style="opacity:.45;transition:opacity .15s ease">Delete forever</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(veil);
      const box = $('vdl-card'), input = $('vdl-in'), go = $('vdl-go'), err = $('vdl-err');
      let busy = false, auth = null, signOutFn = null;

      const open = () => {
        input.value = ''; go.disabled = true; go.style.opacity = '.45'; err.classList.add('hidden');
        veil.style.opacity = '1'; veil.style.pointerEvents = 'auto';
        requestAnimationFrame(() => { box.style.transform = 'none'; });
        setTimeout(() => input.focus(), 80);
      };
      const close = () => {
        if (busy) return;
        veil.style.opacity = '0'; veil.style.pointerEvents = 'none';
        box.style.transform = 'translateY(8px) scale(.98)';
      };
      $('vdl-open').addEventListener('click', open);
      $('vdl-cancel').addEventListener('click', close);
      veil.addEventListener('mousedown', (e) => { if (e.target === veil) close(); });
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && veil.style.pointerEvents === 'auto') close(); });
      input.addEventListener('input', () => {
        const ok = input.value.trim() === 'DELETE';
        go.disabled = !ok; go.style.opacity = ok ? '1' : '.45';
      });

      go.addEventListener('click', async () => {
        if (go.disabled || !auth || !auth.currentUser) return;
        busy = true; go.disabled = true;
        go.innerHTML = '<span class="inline-flex items-center gap-2"><svg class="vc-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>Deleting…</span>';
        err.classList.add('hidden');
        try {
          const tok = await auth.currentUser.getIdToken();
          const r = await fetch(BRIDGE + '/api/account/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok },
            body: JSON.stringify({ confirm: 'DELETE' })
          });
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(j.error || ('Something went wrong (' + r.status + ').'));
          try { await signOutFn(); } catch (e) {}
          try { ['vocallus_user', 'vocallus_agent', 'va_token'].forEach(k => localStorage.removeItem(k)); } catch (e) {}
          document.body.style.transition = 'opacity .25s ease'; document.body.style.opacity = '0';
          setTimeout(() => { location.href = '../index.html'; }, 260);
        } catch (e) {
          busy = false;
          err.textContent = e.message === 'Failed to fetch' ? "Couldn't reach Vocallus. Try again in a moment." : e.message;
          err.classList.remove('hidden');
          go.textContent = 'Delete forever'; go.disabled = false; go.style.opacity = '1';
        }
      });

      try {
""" + _DP_FB + """
        const A = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        auth = A.getAuth(app);
        signOutFn = () => A.signOut(auth);
      } catch (e) {}
    }
  </script>
"""

# ======================= Account menu (person icon -> Log out / Delete account) =======================

_ACCT_BTN_HTML = (
    '<button id="vu-acct" type="button" title="Account" aria-haspopup="menu" aria-expanded="false" '
    'class="w-9 h-9 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-900 flex items-center justify-center transition-colors">'
    '<svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
    '</button><span id="signout-btn" hidden></span>'
)

_DP_ACCOUNT_JS = """
  <style>
    /* VU_ACCOUNT_MARKER */
    #vu-menu { position: fixed; z-index: 96; width: 240px; background: #fff; border: 1px solid #ececec; border-radius: 16px;
      box-shadow: 0 18px 50px rgba(0,0,0,.16); padding: 6px; opacity: 0; pointer-events: none;
      transform: translateY(6px) scale(.97); transform-origin: bottom left;
      transition: opacity .16s ease, transform .2s cubic-bezier(.16,1,.3,1); }
    #vu-menu.vu-open { opacity: 1; pointer-events: auto; transform: none; }
    #vu-menu .vu-item { width: 100%; display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px;
      font-size: 14px; font-weight: 600; text-align: left; transition: background-color .12s ease; }
    #vu-menu .vu-grey { color: #4b5563; } #vu-menu .vu-grey:hover { background: #f3f4f6; color: #111827; }
    #vu-menu .vu-red { color: #dc2626; } #vu-menu .vu-red:hover { background: #fef2f2; }
    #vu-veil { position: fixed; inset: 0; z-index: 97; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center;
      padding: 16px; opacity: 0; pointer-events: none; transition: opacity .18s ease; }
    #vu-veil.vu-open { opacity: 1; pointer-events: auto; }
    #vu-box { background: #fff; border-radius: 24px; width: 100%; max-width: 420px; padding: 28px; box-shadow: 0 24px 60px rgba(0,0,0,.22);
      transform: translateY(8px) scale(.98); transition: transform .22s cubic-bezier(.16,1,.3,1); }
    #vu-veil.vu-open #vu-box { transform: none; }
    #vu-menu .vu-item { background: none; border: 0; cursor: pointer; font-family: inherit; }
    #vu-menu svg, #vu-box .vu-warn svg { width: 18px; height: 18px; flex-shrink: 0; }
    #vu-who { padding: 8px 12px 10px; font-size: 12px; color: #9ca3af; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    #vu-menu .vu-line { height: 1px; background: #f3f4f6; margin: 0 4px 4px; }
    #vu-box .vu-warn { width: 44px; height: 44px; border-radius: 999px; background: #fef2f2; color: #dc2626; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
    #vu-box h3 { font-size: 20px; font-weight: 600; color: #111827; margin: 0; }
    #vu-box p { font-size: 14px; color: #6b7280; line-height: 1.6; margin: 8px 0 0; }
    #vu-box .vu-row { display: flex; justify-content: flex-end; gap: 8px; margin-top: 24px; }
    #vu-box .vu-btn { padding: 10px 16px; border-radius: 12px; font-size: 14px; font-weight: 600; font-family: inherit; cursor: pointer; transition: background-color .15s ease, opacity .15s ease; }
    #vu-cancel { background: #fff; border: 1px solid #e5e7eb; color: #1f2937; } #vu-cancel:hover { background: #f9fafb; }
    #vu-go { background: #dc2626; border: 1px solid #dc2626; color: #fff; min-width: 150px; } #vu-go:hover { background: #b91c1c; } #vu-go:disabled { opacity: .7; cursor: default; }
    #vu-err { font-size: 13px; color: #dc2626; margin-top: 12px; } #vu-err.hidden { display: none; }
    .vu-spin { animation: vuSpin .8s linear infinite; } @keyframes vuSpin { to { transform: rotate(360deg); } }
    @media (prefers-reduced-motion: reduce) { #vu-menu, #vu-veil, #vu-box { transition: none; } }
  </style>
  <script type="module">
    const BRIDGE = "https://vocallus-bridge-production.up.railway.app";
    const btn = document.getElementById('vu-acct');
    if (btn) {
      const I = (d) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + d + '</svg>';
      const menu = document.createElement('div');
      menu.id = 'vu-menu'; menu.setAttribute('role', 'menu');
      menu.innerHTML =
        '<div id="vu-who">Signed in</div>' +
        '<div class="vu-line"></div>' +
        '<button id="vu-out" class="vu-item vu-grey" role="menuitem">' + I('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line>') + 'Log out</button>' +
        '<button id="vu-del" class="vu-item vu-red" role="menuitem">' + I('<polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path>') + 'Delete account</button>';
      document.body.appendChild(menu);

      const veil = document.createElement('div');
      veil.id = 'vu-veil';
      veil.innerHTML =
        '<div id="vu-box" role="dialog" aria-modal="true">' +
          '<div class="vu-warn">' + I('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>') + '</div>' +
          '<h3>Are you sure?</h3>' +
          '<p>This cancels your subscription, turns off your Solana phone number, and permanently erases your calls, calendar and settings. This can’t be undone.</p>' +
          '<div id="vu-err" class="hidden"></div>' +
          '<div class="vu-row">' +
            '<button id="vu-cancel" class="vu-btn">Cancel</button>' +
            '<button id="vu-go" class="vu-btn">Delete account</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(veil);

      const $ = (id) => document.getElementById(id);
      let auth = null, A = null, busy = false;

      const place = () => {
        const r = btn.getBoundingClientRect();
        if (r.right + 252 <= window.innerWidth) {          // beside the sidebar icon
          menu.style.left = (r.right + 12) + 'px';
          menu.style.top = ''; menu.style.bottom = Math.max(8, window.innerHeight - r.bottom) + 'px';
          menu.style.transformOrigin = 'bottom left';
        } else {                                            // small screens: under the icon
          menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 248)) + 'px';
          menu.style.bottom = ''; menu.style.top = (r.bottom + 8) + 'px';
          menu.style.transformOrigin = 'top left';
        }
      };
      const isOpen = () => menu.classList.contains('vu-open');
      const openMenu = () => { place(); menu.classList.add('vu-open'); btn.setAttribute('aria-expanded', 'true'); };
      const closeMenu = () => { menu.classList.remove('vu-open'); btn.setAttribute('aria-expanded', 'false'); };
      btn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); isOpen() ? closeMenu() : openMenu(); });
      document.addEventListener('mousedown', (e) => { if (isOpen() && !menu.contains(e.target) && !btn.contains(e.target)) closeMenu(); });
      window.addEventListener('resize', () => { if (isOpen()) place(); });

      const leave = (to) => {
        try { ['vocallus_user', 'vocallus_agent', 'va_token'].forEach(k => localStorage.removeItem(k)); } catch (e) {}
        document.body.style.transition = 'opacity .25s ease'; document.body.style.opacity = '0';
        setTimeout(() => { location.href = to; }, 260);
      };

      $('vu-out').addEventListener('click', async () => {
        closeMenu();
        try { if (A && auth) await A.signOut(auth); } catch (e) {}
        leave('login.html');
      });

      const openConfirm = () => { $('vu-err').classList.add('hidden'); veil.classList.add('vu-open'); setTimeout(() => $('vu-cancel').focus(), 60); };
      const closeConfirm = () => { if (!busy) veil.classList.remove('vu-open'); };
      $('vu-del').addEventListener('click', () => { closeMenu(); setTimeout(openConfirm, 90); });
      $('vu-cancel').addEventListener('click', closeConfirm);
      veil.addEventListener('mousedown', (e) => { if (e.target === veil) closeConfirm(); });
      document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (veil.classList.contains('vu-open')) closeConfirm(); else if (isOpen()) closeMenu();
      });

      $('vu-go').addEventListener('click', async () => {
        const go = $('vu-go'), err = $('vu-err');
        if (busy) return;
        if (!auth || !auth.currentUser) { err.textContent = 'Still loading your account - try again in a second.'; err.classList.remove('hidden'); return; }
        busy = true; go.disabled = true; err.classList.add('hidden');
        go.innerHTML = '<span style="display:inline-flex;align-items:center;gap:8px"><svg class="vu-spin" style="width:16px;height:16px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" stroke-linecap="round"/></svg>Deleting…</span>';
        try {
          const tok = await auth.currentUser.getIdToken();
          const r = await fetch(BRIDGE + '/api/account/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok },
            body: JSON.stringify({ confirm: 'DELETE' })
          });
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(j.error || ('Something went wrong (' + r.status + ').'));
          try { await A.signOut(auth); } catch (e) {}
          leave('../index.html');
        } catch (e) {
          busy = false; go.disabled = false; go.textContent = 'Delete account';
          err.textContent = e.message === 'Failed to fetch' ? 'Couldn’t reach Vocallus. Try again in a moment.' : e.message;
          err.classList.remove('hidden');
        }
      });

      try {
""" + _DP_FB + """
        A = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
        auth = A.getAuth(app);
        A.onAuthStateChanged(auth, (u) => { if (u && u.email) $('vu-who').textContent = u.email; });
      } catch (e) {}
    }
  </script>
"""

_DP_PAGEFX_CSS = """
  <style>
    /* VF_PAGEFX */
    /* Chrome/Edge: keep the old page on screen until the new one is ready (no white flash), sidebar never blinks */
    @view-transition { navigation: auto; }
    ::view-transition-old(root), ::view-transition-new(root) { animation: none; }
    nav:has(.app-tab) { view-transition-name: vc-sidebar; }
    ::view-transition-group(vc-sidebar) { animation: none; }
    /* page content eases in */
    @keyframes vcPageIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
    body > main, main.flex-1 { animation: vcPageIn .38s cubic-bezier(.16,1,.3,1) both; }
    html.vc-leaving main { opacity: 0; transform: translateY(-4px); transition: opacity .14s ease, transform .14s ease; }
    @media (prefers-reduced-motion: reduce) { body > main, main.flex-1 { animation: none; } }
  </style>
  <script>
    /* fade the content out before going to another app page (browsers without view transitions) */
    (function () {
      if ('onpagereveal' in window) return;
      var pages = /(^|\\/)(dashboard|solana|calendar|history)(\\.html)?(\\?|#|$)/;
      document.addEventListener('click', function (e) {
        var a = e.target.closest && e.target.closest('a[href]');
        if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || a.target === '_blank') return;
        var href = a.getAttribute('href');
        if (!pages.test(href) || href.charAt(0) === '#') return;
        var here = location.pathname.split('/').pop().replace('.html', '');
        var there = href.split(/[?#]/)[0].split('/').pop().replace('.html', '');
        if (!there || there === here) return;
        e.preventDefault();
        document.documentElement.classList.add('vc-leaving');
        setTimeout(function () { location.href = href; }, 130);
      });
      window.addEventListener('pageshow', function () { document.documentElement.classList.remove('vc-leaving'); });
    })();
  </script>
"""

_APP_NAMES_AUTH = {"dashboard.html", "solana.html", "calendar.html", "history.html"}
_prev_rp_authbtn = render_page


def _dp_add(html, marker, where, snippet):
    if marker in html or where not in html:
        return html
    return html.replace(where, snippet + "\n" + where, 1)


# Wrapped in one <span> so the bullet's flex layout keeps it on one line of text.
_GOOGLE_KEY_LINK = ('<span>Bring your own <a href="https://aistudio.google.com/api-keys" target="_blank" rel="noopener" '
                    'class="underline underline-offset-2 hover:text-black">Google API key</a> or '
                    '<a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" '
                    'class="underline underline-offset-2 hover:text-black">OpenAI API key</a></span>')


def render_page(path, builder):
    html = _prev_rp_authbtn(path, builder)
    name = Path(path).name

    # ---------- every page ----------
    # Footer: drop the Contact column (placeholder email + phone)
    html = _re_auth.sub(r'\s*<div class="md:col-span-2">\s*<p[^>]*>Contact</p>\s*<ul[^>]*>.*?</ul>\s*</div>', '', html, flags=_re_auth.S)
    html = html.replace('Payments secured by Stripe', 'Secure payment')
    # Google sign-in popup says "continue to vocallus.com" (Netlify proxies /__/auth to Firebase)
    html = html.replace('"vocallus-aa81e.firebaseapp.com"', '"vocallus.com"').replace("'vocallus-aa81e.firebaseapp.com'", "'vocallus.com'")
    # Plan minutes: Pro 3,000 / Max 10,000
    html = html.replace('Up to 300 minutes / month', 'Up to 3,000 minutes / month')
    html = html.replace('Up to 1,500 minutes / month', 'Up to 10,000 minutes / month')
    html = html.replace('{ none: 0, pro: 300, max: 1500 }', '{ none: 0, pro: 3000, max: 10000 }')
    html = html.replace('Bring your own Gemini API key', _GOOGLE_KEY_LINK)

    # ---------- app pages ----------
    if name in _APP_NAMES_AUTH:
        # Sidebar: "Finances" -> "Billing" on every app page
        html = _re_auth.sub(r'>\s*Finances\s*<', '>Billing<', html)
        html = _dp_add(html, "DP_SCROLL_CSS", "</head>", _DP_SCROLL_CSS)
        # The builder's Firebase helper (window.whenFirebase) was missing on the app pages,
        # so its Save buttons, calendar and demo banner never ran. Put it back.
        _fbs = globals().get("FIREBASE_SCRIPT", "")
        if _fbs and "<!-- Firebase v10 modular SDK" not in html:
            _fbs = _fbs.replace("10.12.0", "10.12.2")
            _fbs = _fbs.replace('"vocallus-aa81e.firebaseapp.com"', '"vocallus.com"')
            _fbs = _fbs.replace("getFirestore, doc,",
                                "getFirestore, initializeFirestore, persistentLocalCache, persistentMultipleTabManager, doc,", 1)
            _fbs = _fbs.replace("const db   = getFirestore(app);",
                                "let db; try { db = initializeFirestore(app, { localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }) }); }"
                                " catch (e) { db = getFirestore(app); }", 1)
            html = html.replace("</head>", _fbs + "\n</head>", 1)
        # Netlify serves /Pages/dashboard (no .html) - make the old checks accept both.
        html = html.replace('/dashboard\\.html$/', '/dashboard(\\.html)?$/')
        if name == "dashboard.html":
            html = _dp_add(html, "VM_MAIN_MARKER", "</body>", _DP_DASH_MAIN_JS)
            html = _dp_add(html, "SF_DASH_CSS", "</head>", _DP_DASH_HEAD)
            html = _dp_add(html, "SF_DASH_MARKER", "</body>", _DP_DASH_JS)
            html = _dp_add(html, "VN_NUMBER_MARKER", "</body>", _DP_NUMBER_JS)
            html = _dp_add(html, "VC_RECENT_MARKER", "</body>", _DP_RECENT_JS)
            html = _dp_add(html, "VB_BILLING_MARKER", "</body>", _DP_BILLING_JS)
            html = _dp_add(html, "VA_DELETE_MARKER", "</body>", _DP_DELETE_JS)
            html = _dp_add(html, "VR_ROUTER_MARKER", "</body>", _DP_ROUTER_JS)
            html = _dp_add(html, "VO_ONBOARD_MARKER", "</body>", _DP_ONBOARD_JS)
        if name == "solana.html":
            html = _dp_add(html, "VS_SOLANA_MARKER", "</body>", _DP_SOLANA_JS)
            html = _dp_add(html, "VD_DEMO_MARKER", "</body>", _DP_DEMO_JS)
            html = _dp_add(html, "VP_PROVIDER_MARKER", "</body>", _DP_PROVIDER_JS)
            html = _dp_add(html, "VV_VOICE_MARKER", "</body>", _DP_VOICE_JS)
            html = _dp_add(html, "VZ_ABOUT_MARKER", "</body>", _DP_ABOUT_JS)
            html = _dp_add(html, "VQ_AUTOSAVE_MARKER", "</body>", _DP_AUTOSAVE_JS)
            html = _dp_add(html, "VO_ONBOARD_MARKER", "</body>", _DP_ONBOARD_JS)
            # "AGENT NAME" / "SYSTEM PROMPT" -> "Agent name" / "System prompt"
            html = html.replace('block text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-2',
                                'block text-[13px] font-semibold text-gray-700 mb-1.5')
            # Claude isn't offered any more (its icon is deleted)
            html = _re_auth.sub(r'\s*<button data-provider="claude".*?</button>', '', html, flags=_re_auth.S)
            html = html.replace('Gemini is required for phone calls.', 'Pick the AI behind your agent.')
        html = _dp_add(html, "VA_ALERTS_MARKER", "</body>", _DP_ALERTS_JS)
        html = _dp_add(html, "VF_PAGEFX", "</head>", _DP_PAGEFX_CSS)
        # Person icon menu replaces the old Sign out button (old id kept hidden for the old scripts)
        if 'id="vu-acct"' not in html:
            html = _re_auth.sub(r'<button id="signout-btn"[^>]*>.*?</button>', lambda m: _ACCT_BTN_HTML, html, count=1, flags=_re_auth.S)
        if 'id="vu-acct"' in html:
            html = _dp_add(html, "VU_ACCOUNT_MARKER", "</body>", _DP_ACCOUNT_JS)
        if name == "calendar.html":
            html = _dp_add(html, "VK_HOURS_MARKER", "</body>", _DP_HOURS_JS)
            html = _dp_add(html, "VG_CAL_MARKER", "</body>", _DP_GCAL_JS)
        if name == "history.html":
            html = _dp_add(html, "VH_HISTORY_MARKER", "</body>", _DP_HISTORY_JS)
        return html

    # ---------- marketing pages ----------
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/dashboard\.html" class="([^"]*px-7[^"]*)">\s*See the dashboard\s*</a>',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" data-dash-cls="__HERO_DASH_CLS__" class="\2">Talk to Sales</a>',
        html)
    html = html.replace('Get started today', 'Try for free')
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/login\.html" class="px-2 py-1\.5',
        r'<a href="\1Pages/login.html" data-auth-logout class="px-2 py-1.5',
        html)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/talk-to-sales\.html" class="hidden sm:inline-flex',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" data-dash-cls="__HEADER_DASH_CLS__" class="hidden sm:inline-flex',
        html)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/signup\.html" class="btn-primary inline-flex items-center justify-center px-5 py-2',
        r'<a href="\1Pages/signup.html" data-auth-hide class="btn-primary inline-flex items-center justify-center px-5 py-2',
        html)
    html = _dp_add(html, "AUTH_BTN_CSS_MARKER", "</head>", _AUTH_BTN_CSS)
    html = _dp_add(html, "AUTH_BTN_MARKER", "</body>", _AUTH_BTN_JS)
    if name in ("login.html", "signup.html"):
        html = _dp_add(html, "SF_LOGIN_MARKER", "</body>", _DP_LOGIN_JS)
    if name == "pricing.html":
        html = _dp_add(html, "VB_BACK_MARKER", "</body>", _DP_PRICING_BACK_JS)
    if name == "checkout.html":
        # The old checkout script gave up if sign-in wasn't ready yet (nothing showed). Switch it off;
        # VX_CHECKOUT takes over and waits for sign-in properly.
        html = _re_auth.sub(r'window\.whenFirebase && window\.whenFirebase\(async function \(fb\) \{(\s*)var user = fb\.auth\.currentUser;',
                            r'false && window.whenFirebase(async function (fb) {\1var user = fb.auth.currentUser;', html)
        html = _dp_add(html, "VX_CHECKOUT_MARKER", "</body>", _DP_CHECKOUT_JS)
    return html

# --- end deepseek_python.py ---
'''.replace("__HERO_DASH_CLS__", HERO_DASH_CLS).replace("__HEADER_DASH_CLS__", HEADER_DASH_CLS)


def strip_block(src: str, start_marker: str, end_marker: str) -> str:
    while start_marker in src:
        start = src.index(start_marker)
        end = src.find(end_marker, start)
        if end == -1:
            print(f"error: found '{start_marker}' but no end marker.")
            print("Run  git checkout -- build.py  and try again.")
            sys.exit(1)
        src = src[:start] + src[end + len(end_marker):]
        print(f"[ok] removed old block: {start_marker.strip('# -')}")
    return src


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: could not find {BUILD_PY} - put deepseek_python.py in your VP folder.")
        return 1

    src = BUILD_PY.read_text(encoding="utf-8")
    for start_marker, end_marker in OLD_BLOCKS:
        src = strip_block(src, start_marker, end_marker)

    if MAIN_GUARD not in src:
        print('error: could not find  if __name__ == "__main__":  in build.py')
        return 1

    src = src.replace(MAIN_GUARD, OVERRIDE + "\n\n" + MAIN_GUARD, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("[ok] added deepseek_python.py v15")
    for f, how in (("Audio/solana.mp3", "make_voices.py"), ("Audio/pfmale.mp3", "make_voices.py"), ("Audio/pmale.mp3", "make_voices.py"),
                   ("Images/pmale.png", ""), ("Images/pfmale.png", "")):
        if not (ROOT / f).exists() and not (ROOT / f.replace(".mp3", ".wav")).exists():
            print(f"[note] {f} not found yet" + (f" - run {how}" if how else " - add the picture"))
    (ROOT / "firebase-messaging-sw.js").write_text(SW_FILE, encoding="utf-8")
    nt = ROOT / "netlify.toml"
    toml = nt.read_text(encoding="utf-8") if nt.exists() else '[build]\n  publish = "."\n'
    if "/__/auth/*" not in toml:
        toml = toml.rstrip() + (
            '\n\n# Google sign-in through vocallus.com (proxied to Firebase)\n'
            '[[redirects]]\n  from = "/__/auth/*"\n  to = "https://vocallus-aa81e.firebaseapp.com/__/auth/:splat"\n  status = 200\n  force = true\n\n'
            '[[redirects]]\n  from = "/__/firebase/*"\n  to = "https://vocallus-aa81e.firebaseapp.com/__/firebase/:splat"\n  status = 200\n  force = true\n')
        nt.write_text(toml, encoding="utf-8")
        print("[ok] netlify.toml: Google sign-in goes through vocallus.com")
    print("[ok] wrote firebase-messaging-sw.js (call alerts)")

    print("\nRunning build.py ...\n")
    rc = subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode

    # Claude is no longer offered - remove its icon (build.py re-creates it, so delete after building).
    cla = ROOT / "Images" / "cla.png"
    if cla.exists():
        cla.unlink()
        print("[ok] deleted Images/cla.png")

    checks = [
        ("index.html", "data-auth-swap", "header/homepage buttons"),
        ("Pages/dashboard.html", "VN_NUMBER_MARKER", "Number tab"),
        ("Pages/dashboard.html", "SF_DASH_MARKER", "greeting fade"),
        ("Pages/dashboard.html", "VC_RECENT_MARKER", "recent calls"),
        ("Pages/dashboard.html", "VB_BILLING_MARKER", "Billing tab"),
        ("Pages/history.html", "VH_HISTORY_MARKER", "History page"),
        ("Pages/dashboard.html", "VR_ROUTER_MARKER", "Number/Billing tabs open directly"),
        ("Pages/solana.html", "VS_SOLANA_MARKER", "Solana prefilled name + prompt"),
        ("Pages/calendar.html", "VK_HOURS_MARKER", "Calendar business + after hours"),
        ("Pages/calendar.html", "window.whenFirebase", "Firebase helper on app pages"),
        ("Pages/solana.html", "VD_DEMO_MARKER", "Solana test call + test chat"),
        ("Pages/dashboard.html", "VA_ALERTS_MARKER", "Call alerts (bell)"),
        ("firebase-messaging-sw.js", "firebase.messaging()", "Alerts service worker"),
        ("Pages/dashboard.html", "VM_MAIN_MARKER", "Dashboard scrolls"),
        ("Pages/solana.html", "VP_PROVIDER_MARKER", "AI provider: Gemini or ChatGPT"),
        ("Pages/checkout.html", "Secure payment", "Checkout says Secure payment"),
        ("Pages/pricing.html", "platform.openai.com/api-keys", "Pricing: Google or OpenAI key links"),
        ("Pages/solana.html", "VV_VOICE_MARKER", "Voice picker (male / female)"),
        ("Pages/pricing.html", "VB_BACK_MARKER", "Pricing Back button"),
        ("Pages/history.html", "openDetail", "History: click a call for details"),
        ("Pages/calendar.html", "VG_CAL_MARKER", "Calendar: clean week view"),
        ("Pages/dashboard.html", "VO_ONBOARD_MARKER", "Sign-up question: what your business does"),
        ("Pages/solana.html", "VZ_ABOUT_MARKER", "Solana page: business description"),
        ("Pages/solana.html", "VQ_AUTOSAVE_MARKER", "Solana page: saves by itself (no Save button)"),
        ("Pages/calendar.html", "VG_IMPORT_MODAL", "Calendar: Import to Google Calendar popup"),
        ("Pages/solana.html", "VV_LIVE_SWITCH", "Test call: switch voice live"),
        ("Pages/dashboard.html", "VN_DELETE_MARKER", "Number: Delete number button"),
        ("Pages/calendar.html", "VG_ORGANIZE", "Calendar: select many, bulk edit/delete, Organize"),
        ("Pages/solana.html", "VO_ENSURE_TEST", "Setup popup before a test call"),
        ("Pages/calendar.html", "VF_PAGEFX", "Smooth page-to-page loading"),
        ("Pages/dashboard.html", "VO_ENSURE_NUMBER", "Setup popup before buying a number"),
        ("Pages/checkout.html", "VX_CHECKOUT_MARKER", "Checkout: card form loads reliably"),
        ("Pages/checkout.html", "false && window.whenFirebase", "Checkout: old script switched off"),
        ("Pages/dashboard.html", "VA_DELETE_MARKER", "Billing: Delete account"),
        ("Pages/dashboard.html", "VU_ACCOUNT_MARKER", "Account menu (dashboard)"),
        ("Pages/solana.html", "VU_ACCOUNT_MARKER", "Account menu (solana)"),
        ("Pages/calendar.html", "VU_ACCOUNT_MARKER", "Account menu (calendar)"),
        ("Pages/history.html", "VU_ACCOUNT_MARKER", "Account menu (history)"),
    ]
    print()
    for rel, marker, label in checks:
        f = ROOT / rel
        ok = f.exists() and (not marker or marker in f.read_text(encoding="utf-8"))
        print(f"[{'ok' if ok else 'warn'}] {label}{'' if ok else ' - not found in ' + rel}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
