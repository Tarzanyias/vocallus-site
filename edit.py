#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_python.py (v2) - signed-in buttons, smooth, solid black Dashboard.

Run from the VP folder:

    python deepseek_python.py

Signed OUT:
  Header:  Sign in | Talk to Sales | Try for free
  Hero:    [Try for free]  [Talk to Sales]
Signed IN:
  Header:  [Dashboard]                      (solid black, like Try for free)
  Hero:    [Try for free]  [Dashboard]      (Dashboard solid black)

The auth buttons stay invisible for a split second until Firebase knows if
you're signed in, then fade in - so nothing flashes or jumps.

Replaces the v1 block if you ran the old script. Undo with:  git checkout -- .
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"
MARKER = "# --- deepseek_python.py: header/hero auth buttons ---"
END_MARKER = "# --- end deepseek_python.py ---"
MAIN_GUARD = 'if __name__ == "__main__":'

HEADER_DASH_CLS = "btn-primary inline-flex items-center justify-center px-5 py-2 rounded-xl font-semibold shadow-sm"
HERO_DASH_CLS = ("inline-flex items-center justify-center px-7 py-3.5 rounded-xl "
                 "font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 "
                 "text-neutral-800 hover:bg-neutral-50 transition")

OVERRIDE = r'''

# --- deepseek_python.py: header/hero auth buttons ---
import re as _re_auth

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
    // Safety net: if Firebase is slow or blocked, show the signed-out buttons anyway.
    const fallback = setTimeout(() => root.classList.add('auth-ready'), 2500);

    document.querySelectorAll('[data-auth-swap], [data-auth-logout]').forEach(a => {
      a.dataset.label = a.textContent.trim();
      a.dataset.href0 = a.getAttribute('href');
      a.dataset.cls0 = a.className;
    });

    let doSignOut = null;
    document.querySelectorAll('[data-auth-logout]').forEach(a => {
      a.addEventListener('click', async (e) => {
        if (a.dataset.mode !== 'logout' || !doSignOut) return;   // signed out: normal "Sign in" link
        e.preventDefault();
        e.stopImmediatePropagation();
        document.body.classList.add('is-leaving');
        try { await doSignOut(); } catch (err) {}
        window.location.reload();
      }, true);
    });

    function apply(user) {
      document.querySelectorAll('[data-auth-logout]').forEach(a => {
        if (user) {
          a.textContent = 'Log out';
          a.setAttribute('href', '#');
          a.dataset.mode = 'logout';
        } else {
          a.textContent = a.dataset.label;
          a.setAttribute('href', a.dataset.href0);
          a.dataset.mode = '';
        }
      });
      document.querySelectorAll('[data-auth-swap]').forEach(a => {
        if (user) {
          a.textContent = 'Dashboard';
          a.setAttribute('href', a.dataset.dash);
          a.className = a.dataset.dashCls;
        } else {
          a.textContent = a.dataset.label;
          a.setAttribute('href', a.dataset.href0);
          a.className = a.dataset.cls0;
        }
      });
      document.querySelectorAll('[data-auth-hide]').forEach(el => {
        el.classList.toggle('auth-gone', !!user);
      });
      clearTimeout(fallback);
      requestAnimationFrame(() => root.classList.add('auth-ready'));
    }

    try {
      const { initializeApp, getApps } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
      const { getAuth, onAuthStateChanged, signOut } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      const app = getApps().length ? getApps()[0] : initializeApp({
        apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
        authDomain: "vocallus-aa81e.firebaseapp.com",
        projectId: "vocallus-aa81e",
        storageBucket: "vocallus-aa81e.firebasestorage.app",
        messagingSenderId: "997486177218",
        appId: "1:997486177218:web:7c4741dbd450549140845b"
      });
      const auth = getAuth(app);
      doSignOut = () => signOut(auth);
      onAuthStateChanged(auth, apply);
    } catch (e) {
      apply(null);
    }
  </script>
"""

_APP_NAMES_AUTH = {"dashboard.html", "solana.html", "calendar.html", "history.html"}
_prev_rp_authbtn = render_page


def render_page(path, builder):
    html = _prev_rp_authbtn(path, builder)
    if Path(path).name in _APP_NAMES_AUTH:
        return html

    # Hero: "See the dashboard" -> "Talk to Sales" (solid black "Dashboard" when signed in)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/dashboard\.html" class="([^"]*px-7[^"]*)">\s*See the dashboard\s*</a>',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" data-dash-cls="__HERO_DASH_CLS__" class="\2">Talk to Sales</a>',
        html)
    html = html.replace('Get started today', 'Try for free')

    # Header: Sign in -> Log out when signed in
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/login\.html" class="px-2 py-1\.5',
        r'<a href="\1Pages/login.html" data-auth-logout class="px-2 py-1.5',
        html)
    # Header: Talk to Sales -> solid black Dashboard when signed in
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/talk-to-sales\.html" class="hidden sm:inline-flex',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" data-dash-cls="__HEADER_DASH_CLS__" class="hidden sm:inline-flex',
        html)
    # Header: Try for free (removed when signed in)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/signup\.html" class="btn-primary inline-flex items-center justify-center px-5 py-2',
        r'<a href="\1Pages/signup.html" data-auth-hide class="btn-primary inline-flex items-center justify-center px-5 py-2',
        html)

    if "AUTH_BTN_CSS_MARKER" not in html and "</head>" in html:
        html = html.replace("</head>", _AUTH_BTN_CSS + "\n</head>", 1)
    if "AUTH_BTN_MARKER" not in html and "</body>" in html:
        html = html.replace("</body>", _AUTH_BTN_JS + "\n</body>", 1)
    return html

# --- end deepseek_python.py ---
'''.replace("__HERO_DASH_CLS__", HERO_DASH_CLS).replace("__HEADER_DASH_CLS__", HEADER_DASH_CLS)


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: could not find {BUILD_PY}")
        print("Put deepseek_python.py in the same folder as build.py (your VP folder).")
        return 1

    src = BUILD_PY.read_text(encoding="utf-8")

    # Remove the old (v1) block if it's there.
    if MARKER in src:
        start = src.index(MARKER)
        end = src.find(END_MARKER, start)
        if end == -1:
            print("error: found the old block but not its end marker - run  git checkout -- build.py  and try again")
            return 1
        src = src[:start] + src[end + len(END_MARKER):]
        print("[ok] removed old version")

    if MAIN_GUARD not in src:
        print('error: could not find  if __name__ == "__main__":  in build.py')
        return 1

    src = src.replace(MAIN_GUARD, OVERRIDE.lstrip("\n") + "\n\n" + MAIN_GUARD, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("[ok] added smooth signed-in buttons (solid black Dashboard)")

    print("\nRunning build.py ...\n")
    rc = subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode

    index = ROOT / "index.html"
    html = index.read_text(encoding="utf-8") if index.exists() else ""
    if "data-auth-swap" in html:
        print("\n[ok] index.html has the new buttons")
    else:
        print("\n[warn] couldn't find the buttons in index.html - send me index.html and I'll adjust.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
