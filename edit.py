#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_python.py (v7) - one script for all the site polish.
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

OVERRIDE = r'''# --- deepseek_python.py: header/hero auth buttons ---
import re as _re_auth

_DP_FB = """
      const { initializeApp, getApps } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
      const app = getApps().length ? getApps()[0] : initializeApp({
        apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
        authDomain: "vocallus-aa81e.firebaseapp.com",
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

        function renderHas(uid, d) {
          body.innerHTML =
            '<div class="' + card + ' mb-6">' +
              '<div class="text-[13px] text-gray-500 font-medium mb-2">Your Solana number</div>' +
              '<div class="flex items-center gap-3 flex-wrap">' +
                '<div id="vn-number" class="text-[32px] font-semibold text-gray-900 tracking-tight"></div>' +
                '<button id="vn-copy" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13px] font-semibold hover:bg-gray-50">Copy</button>' +
              '</div>' +
              '<p class="text-[14px] text-gray-500 mt-3">Solana answers this number 24/7.</p>' +
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
              if (!list.length) { status.textContent = 'No numbers in that area code, try another.'; return; }
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
          row.className = 'bg-white px-2 py-5 border-b border-gray-200';
          row.innerHTML =
            '<div class="flex items-center gap-3 flex-wrap mb-1">' +
              '<div class="vc-num text-[15px] font-semibold text-gray-900"></div>' +
              '<div class="vc-ago text-[13px] text-gray-500"></div>' +
              '<span class="vc-st ml-auto text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"></span>' +
            '</div><div class="vc-dur text-[13px] text-gray-500"></div>';
          const [label, cls] = statusPill(c.status);
          row.querySelector('.vc-num').textContent = fmtPhone(c.from);
          row.querySelector('.vc-ago').textContent = tsOf(c) ? ago(tsOf(c)) : '';
          row.querySelector('.vc-st').textContent = label;
          row.querySelector('.vc-st').className += ' ' + cls;
          row.querySelector('.vc-dur').textContent = 'Duration ' + (c.durationSec ? fmtDur(c.durationSec) : '—');
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
              row.className = 'rounded-2xl border border-gray-100 bg-white p-5 hover:shadow-sm transition';
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

# ======================= dashboard: Billing tab =======================

_DP_BILLING_JS = """
  <script type="module">
    /* VB_BILLING_MARKER */
    const panel = document.getElementById('panel-finances');
    const PLANS = {
      none: { name: 'Demo', price: 'Free', limit: 0 },
      pro:  { name: 'Pro',  price: '$14.99 / month', limit: 300 },
      max:  { name: 'Max',  price: '$99.99 / month', limit: 1500 }
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
      function activate(name) {
        if (!has(name)) name = 'home';
        document.querySelectorAll('.panel').forEach(function (p) {
          p.classList.toggle('hidden', p.id !== 'panel-' + name);
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
      row.className = 'flex items-center justify-end mt-2 text-[12px]';
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
          '<button id="vk-save" type="button" class="btn-primary px-5 py-2.5 rounded-xl font-semibold text-[13.5px]">Save hours</button>' +
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
          btn.disabled = true; btn.textContent = 'Saving…';
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
            status.className = 'text-[13px] text-green-700';
            status.textContent = 'Saved. Solana uses this on the next call.';
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
          btn.disabled = false; btn.textContent = 'Save hours';
        });
      } catch (e) {
        card.style.opacity = '1';
        status.className = 'text-[13px] text-red-600';
        status.textContent = 'Could not load your settings. Refresh the page.';
      }
    }
  </script>
"""

_APP_NAMES_AUTH = {"dashboard.html", "solana.html", "calendar.html", "history.html"}
_prev_rp_authbtn = render_page


def _dp_add(html, marker, where, snippet):
    if marker in html or where not in html:
        return html
    return html.replace(where, snippet + "\n" + where, 1)


def render_page(path, builder):
    html = _prev_rp_authbtn(path, builder)
    name = Path(path).name

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
            _fbs = _fbs.replace("getFirestore, doc,",
                                "getFirestore, initializeFirestore, persistentLocalCache, persistentMultipleTabManager, doc,", 1)
            _fbs = _fbs.replace("const db   = getFirestore(app);",
                                "let db; try { db = initializeFirestore(app, { localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }) }); }"
                                " catch (e) { db = getFirestore(app); }", 1)
            html = html.replace("</head>", _fbs + "\n</head>", 1)
        # Netlify serves /Pages/dashboard (no .html) - make the old checks accept both.
        html = html.replace('/dashboard\\.html$/', '/dashboard(\\.html)?$/')
        if name == "dashboard.html":
            html = _dp_add(html, "SF_DASH_CSS", "</head>", _DP_DASH_HEAD)
            html = _dp_add(html, "SF_DASH_MARKER", "</body>", _DP_DASH_JS)
            html = _dp_add(html, "VN_NUMBER_MARKER", "</body>", _DP_NUMBER_JS)
            html = _dp_add(html, "VC_RECENT_MARKER", "</body>", _DP_RECENT_JS)
            html = _dp_add(html, "VB_BILLING_MARKER", "</body>", _DP_BILLING_JS)
            html = _dp_add(html, "VR_ROUTER_MARKER", "</body>", _DP_ROUTER_JS)
        if name == "solana.html":
            html = _dp_add(html, "VS_SOLANA_MARKER", "</body>", _DP_SOLANA_JS)
        if name == "calendar.html":
            html = _dp_add(html, "VK_HOURS_MARKER", "</body>", _DP_HOURS_JS)
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
    print("[ok] added deepseek_python.py v7")

    print("\nRunning build.py ...\n")
    rc = subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode

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
    ]
    print()
    for rel, marker, label in checks:
        f = ROOT / rel
        ok = f.exists() and marker in f.read_text(encoding="utf-8")
        print(f"[{'ok' if ok else 'warn'}] {label}{'' if ok else ' - not found in ' + rel}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
