#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepseek_python.py - homepage + header buttons that change when you're signed in.

Run from the VP folder:

    python deepseek_python.py

Signed OUT (anyone visiting):
  Header:  Sign in | Talk to Sales | Try for free
  Hero:    [Try for free]  [Talk to Sales]        (replaces "See the dashboard")

Signed IN:
  Header:  Dashboard                               (Sign in + Try for free hidden)
  Hero:    [Try for free]  [Dashboard]

Safe to run twice. Undo with:  git checkout -- .
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"
MARKER = "# --- deepseek_python.py: header/hero auth buttons ---"
MAIN_GUARD = 'if __name__ == "__main__":'

OVERRIDE = r'''

# --- deepseek_python.py: header/hero auth buttons ---
import re as _re_auth

_AUTH_BTN_JS = """
  <script type="module">
    /* AUTH_BTN_MARKER */
    import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
    import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

    const cfg = {
      apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
      authDomain: "vocallus-aa81e.firebaseapp.com",
      projectId: "vocallus-aa81e",
      storageBucket: "vocallus-aa81e.firebasestorage.app",
      messagingSenderId: "997486177218",
      appId: "1:997486177218:web:7c4741dbd450549140845b"
    };
    const app = getApps().length ? getApps()[0] : initializeApp(cfg);

    // Remember the signed-out look so we can restore it on sign out.
    document.querySelectorAll('[data-auth-swap]').forEach(a => {
      a.dataset.label = a.textContent.trim();
      a.dataset.href0 = a.getAttribute('href');
      a.dataset.cls0 = a.className;
    });

    onAuthStateChanged(getAuth(app), (user) => {
      document.querySelectorAll('[data-auth-swap]').forEach(a => {
        if (user) {
          a.textContent = 'Dashboard';
          a.setAttribute('href', a.dataset.dash);
          a.classList.remove('hidden');          // show on phones too
          a.classList.add('inline-flex');
        } else {
          a.textContent = a.dataset.label;
          a.setAttribute('href', a.dataset.href0);
          a.className = a.dataset.cls0;
        }
      });
      document.querySelectorAll('[data-auth-hide]').forEach(el => {
        el.style.display = user ? 'none' : '';
      });
    });
  </script>
"""

_APP_NAMES_AUTH = {"dashboard.html", "solana.html", "calendar.html", "history.html"}
_prev_rp_authbtn = render_page


def render_page(path, builder):
    html = _prev_rp_authbtn(path, builder)
    if Path(path).name in _APP_NAMES_AUTH:
        return html

    # Hero: "See the dashboard" -> "Talk to Sales" (becomes "Dashboard" when signed in)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/dashboard\.html" class="([^"]*px-7[^"]*)">\s*See the dashboard\s*</a>',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" class="\2">Talk to Sales</a>',
        html)
    # Hero main button text
    html = html.replace('Get started today', 'Try for free')

    # Header: Sign in (hidden when signed in)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/login\.html" class="px-2 py-1\.5',
        r'<a href="\1Pages/login.html" data-auth-hide class="px-2 py-1.5',
        html)
    # Header: Talk to Sales -> Dashboard when signed in
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/talk-to-sales\.html" class="hidden sm:inline-flex',
        r'<a href="\1Pages/talk-to-sales.html" data-auth-swap data-dash="\1Pages/dashboard.html" class="hidden sm:inline-flex',
        html)
    # Header: Try for free (hidden when signed in)
    html = _re_auth.sub(
        r'<a href="([^"]*)Pages/signup\.html" class="btn-primary inline-flex items-center justify-center px-5 py-2',
        r'<a href="\1Pages/signup.html" data-auth-hide class="btn-primary inline-flex items-center justify-center px-5 py-2',
        html)

    if "AUTH_BTN_MARKER" not in html and "</body>" in html:
        html = html.replace("</body>", _AUTH_BTN_JS + "\n</body>", 1)
    return html

# --- end deepseek_python.py ---
'''


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: could not find {BUILD_PY}")
        print("Put deepseek_python.py in the same folder as build.py (your VP folder).")
        return 1

    src = BUILD_PY.read_text(encoding="utf-8")
    if MARKER in src:
        print("[skip] already added")
    elif MAIN_GUARD not in src:
        print('error: could not find  if __name__ == "__main__":  in build.py')
        return 1
    else:
        BUILD_PY.write_text(src.replace(MAIN_GUARD, OVERRIDE + "\n\n" + MAIN_GUARD, 1), encoding="utf-8")
        print("[ok] added signed-in / signed-out buttons")

    print("\nRunning build.py ...\n")
    rc = subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode

    index = (ROOT / "index.html").read_text(encoding="utf-8") if (ROOT / "index.html").exists() else ""
    if "data-auth-swap" in index:
        print("\n[ok] index.html has the new buttons")
    else:
        print("\n[warn] couldn't find the buttons in index.html - your builder may have changed them.")
        print("       Send me index.html and I'll adjust the script.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
