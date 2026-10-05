#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_python.py (v4) - one script for all the site polish.

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
    [data-auth-swap], [data-auth-hide], [data-auth-logout] { opacity: 0; transition: opacity .25s ease; }
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
    const fallback = setTimeout(() => root.classList.add('auth-ready'), 2500);

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
  </style>
"""

# ======================= dashboard: greeting fade =======================

_DP_DASH_HEAD = """
  <script>document.documentElement.classList.add('dash-loading');</script>
  <style>
    /* SF_DASH_CSS */
    main > * { transition: opacity .3s ease; }
    html.dash-loading main > * { opacity: 0; }
    #panel-home h1, #banner-line { opacity: 0 !important; transition: opacity .4s ease !important; }
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
    const fallback = setTimeout(() => { reveal(); showGreeting(); }, 4000);
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

        let name = '';
        try {
          const snap = await getDoc(doc(db, 'users', user.uid));
          if (snap.exists()) name = snap.data().name || '';
        } catch (e) {
          console.error('Vocallus user doc:', e);
        }
        name = (name || user.displayName || (user.email || '').split('@')[0] || 'there').trim().split(' ')[0];
        if (h1) {
          h1.innerHTML = greet() + ', <span id="greeting-name"></span>';
          h1.querySelector('#greeting-name').textContent = name;
        }

        try {
          const start = new Date(); start.setHours(0, 0, 0, 0);
          const qs = await getDocs(query(collection(db, 'users', user.uid, 'calls'),
                                         where('startedAt', '>=', Timestamp.fromDate(start))));
          const n = qs.size;
          if (banner) banner.textContent = n ? ('Solana answered ' + n + ' call' + (n === 1 ? '' : 's') + ' today')
                                             : 'No calls yet today';
        } catch (e) {
          console.error('Vocallus calls:', e);
          if (banner) banner.textContent = (e.code === 'permission-denied')
            ? 'Firestore rules are blocking call history - publish the rules that include "calls".'
            : 'No calls yet today';
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
        '<div id="vn-body" style="opacity:0;transition:opacity .3s ease"></div>' +
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

# ======================= empty states =======================

_DP_EMPTY_JS = """
  <script>
    /* VN_EMPTY_MARKER */
    (function () {
      var ICON = '<div class="w-14 h-14 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4">' +
        '<svg class="w-6 h-6 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>';
      function watch(id, test, html) {
        var el = document.getElementById(id);
        if (!el) return;
        var fix = function () {
          if (el.querySelector('[data-vempty]')) return;
          if (test.test(el.textContent || '')) el.innerHTML = html;
        };
        new MutationObserver(fix).observe(el, { childList: true, subtree: true });
        fix();
      }
      watch('call-list', /No calls/i,
        '<div data-vempty class="py-16 text-center">' + ICON +
        '<p class="text-[16px] font-medium text-gray-700">Your recent calls will show here</p>' +
        '<p class="text-[13.5px] text-gray-400 mt-1">Call your Solana number to see it in action.</p></div>');
      watch('history-list', /No calls|history will appear/i,
        '<div data-vempty class="py-20 text-center">' + ICON +
        '<p class="text-[16px] font-medium text-gray-700">This is where your call history shows</p>' +
        '<p class="text-[13.5px] text-gray-400 mt-1">Every call Solana answers appears here with the caller, time, and length.</p></div>');
    })();
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
        html = _dp_add(html, "DP_SCROLL_CSS", "</head>", _DP_SCROLL_CSS)
        if name == "dashboard.html":
            html = _dp_add(html, "SF_DASH_CSS", "</head>", _DP_DASH_HEAD)
            html = _dp_add(html, "SF_DASH_MARKER", "</body>", _DP_DASH_JS)
            html = _dp_add(html, "VN_NUMBER_MARKER", "</body>", _DP_NUMBER_JS)
        if name in ("dashboard.html", "history.html"):
            html = _dp_add(html, "VN_EMPTY_MARKER", "</body>", _DP_EMPTY_JS)
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
    print("[ok] added deepseek_python.py v4")

    print("\nRunning build.py ...\n")
    rc = subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode

    checks = [
        ("index.html", "data-auth-swap", "header/homepage buttons"),
        ("Pages/dashboard.html", "VN_NUMBER_MARKER", "Number tab"),
        ("Pages/dashboard.html", "SF_DASH_MARKER", "greeting fade"),
        ("Pages/history.html", "VN_EMPTY_MARKER", "history empty state"),
    ]
    print()
    for rel, marker, label in checks:
        f = ROOT / rel
        ok = f.exists() and marker in f.read_text(encoding="utf-8")
        print(f"[{'ok' if ok else 'warn'}] {label}{'' if ok else ' - not found in ' + rel}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
