#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit.py — unify sidebar, smooth transitions, real Solana prompts, default Gemini.

Run:
    python edit.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"
MARKER = "# --- edit.py: unified sidebar + smooth transitions + real prompts ---"
MAIN_GUARD = 'if __name__ == "__main__":'


OVERRIDE = r"""

# --- edit.py: unified sidebar + smooth transitions + real prompts ---

# ---------- CSS: fade transitions + auth gate ----------
_FADE_CSS = '''
    /* page transitions */
    body { transition: opacity .15s ease; }
    body.is-leaving { opacity: 0; }
    main, .page-body { opacity: 1; transition: opacity .2s ease; }
    body:not(.auth-ready) main, body:not(.auth-ready) .page-body { opacity: 0; }
    @media (prefers-reduced-motion: reduce) {
      body, main, .page-body { transition: none; }
      body:not(.auth-ready) main, body:not(.auth-ready) .page-body { opacity: 1; }
    }
'''

# ---------- Shared sidebar renderer ----------
_SIDEBAR_ITEMS = [
    ("home",     "dashboard.html",          "Home",     '<path d="M3 10.5L12 3l9 7.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>', "2.2"),
    ("solana",   "solana.html",             "Solana",   '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>', "2"),
    ("calendar", "calendar.html",           "Calendar", '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>', "2"),
    ("number",   "dashboard.html#number",   "Number",   '<path d="M15.05 5A5 5 0 0 1 19 8.95"></path><path d="M15.05 1A9 9 0 0 1 23 8.94"></path><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>', "2"),
    ("history",  "history.html",            "History",  '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>', "2"),
    ("finances", "dashboard.html#finances", "Finances", '<line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>', "2"),
]

def _render_sidebar(active):
    items_html = []
    for key, href, label, path, sw in _SIDEBAR_ITEMS:
        on = (key == active)
        cls = "bg-gray-200/80 text-gray-900" if on else "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
        bar = "opacity-100" if on else "opacity-0"
        items_html.append(
            '                <a href="' + href + '" data-nav="' + key + '" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors ' + cls + '">\n'
            '                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity ' + bar + '"></div>\n'
            '                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + sw + '" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>\n'
            '                    <span class="text-[11px] font-medium tracking-tight">' + label + '</span>\n'
            '                </a>'
        )
    items = "\n".join(items_html)
    return '''    <nav class="w-[88px] bg-[#f2f2f2] border-r border-gray-200 flex flex-col justify-between items-center py-6 flex-shrink-0 z-10">
        <div class="flex flex-col items-center w-full space-y-4">
            <a href="../index.html" class="mb-2 select-none">
                <img src="../Images/logo.png" alt="Vocallus" class="w-9 h-9 rounded-xl" />
            </a>
            <div class="flex flex-col w-full items-center space-y-2">
''' + items + '''
            </div>
        </div>
        <div class="flex flex-col w-full items-center space-y-4">
            <a href="#" class="text-gray-500 hover:text-gray-800 relative p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </a>
            <button id="signout-btn" title="Sign out" class="text-gray-500 hover:text-gray-800 p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
        </div>
    </nav>'''


# ---------- inject fade CSS + auth gate + smooth nav JS ----------
_prev_rp = render_page

_APP_PAGES = {"dashboard.html", "solana.html", "calendar.html", "history.html"}

_AUTH_GATE_JS = '''
  <script>
    // Hide main until Firebase auth resolves; then fade in.
    document.body.classList.remove('auth-ready');
    window.whenFirebase && window.whenFirebase(function (fb) {
      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) { window.location.replace('login.html'); return; }
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            document.body.classList.add('auth-ready');
          });
        });
      });
    });
    // Smooth internal link navigation
    (function () {
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      document.addEventListener('click', function (e) {
        if (reduce) return;
        if (e.defaultPrevented) return;
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var a = e.target.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) === '#') return;
        if (/^(https?:|mailto:|tel:)/i.test(href)) return;
        if (a.target && a.target !== '_self') return;
        try {
          var url = new URL(a.href, location.href);
          if (url.pathname === location.pathname && url.hash) return; // same page + hash: let default handle
        } catch (err) {}
        e.preventDefault();
        document.body.classList.add('is-leaving');
        setTimeout(function () { window.location.href = href; }, 150);
      });
      window.addEventListener('pageshow', function () {
        document.body.classList.remove('is-leaving');
      });
    })();
    // Hash-panel switching on dashboard
    (function () {
      if (!/dashboard\.html$/.test(location.pathname)) return;
      function activate(name) {
        document.querySelectorAll('.dash-tab').forEach(function (t) {
          var on = t.dataset.panel === name;
          t.classList.toggle('bg-gray-200/80', on);
          t.classList.toggle('text-gray-900', on);
          t.classList.toggle('text-gray-500', !on);
          var bar = t.querySelector('.dash-bar');
          if (bar) { bar.classList.toggle('opacity-100', on); bar.classList.toggle('opacity-0', !on); }
        });
        document.querySelectorAll('.panel').forEach(function (p) {
          p.classList.toggle('hidden', p.id !== 'panel-' + name);
        });
      }
      document.querySelectorAll('.app-tab[data-nav]').forEach(function (t) {
        t.addEventListener('click', function (e) {
          var href = t.getAttribute('href') || '';
          if (href.indexOf('dashboard.html#') !== 0) return; // other pages: default nav
          e.preventDefault();
          var p = href.split('#')[1];
          activate(p);
          history.replaceState(null, '', '#' + p);
        });
      });
      var initial = (location.hash || '').replace('#', '');
      if (initial && document.getElementById('panel-' + initial)) activate(initial);
      else activate('home');
    })();
  </script>
'''

def render_page(path, builder):
    html = _prev_rp(path, builder)
    name = Path(path).name
    # Inject fade CSS once
    if "page transitions" not in html:
        html = html.replace("</style>", _FADE_CSS + "\n  </style>", 1)
    # Inject auth gate + smooth nav on app pages
    if name in _APP_PAGES and "Hide main until Firebase auth resolves" not in html:
        html = html.replace("</body>", _AUTH_GATE_JS + "\n</body>", 1)
    return html


# ---------- Solana page: default prompt + live name swap + default Gemini ----------
_prev_solana = page_solana

DEFAULT_PROMPT = (
    "You are {NAME}, the friendly receptionist for {BUSINESS}. Greet callers warmly, "
    "ask how you can help, and keep every reply short and natural, like a real person "
    "on the phone. If they want an appointment, find a day and time that works, get "
    "their name, and confirm the day and time back to them. If you can't help with "
    "something, offer to take a message and say someone will call them back."
)

SOLANA_EXTRA_JS = '''
  <script>
    window.whenFirebase && window.whenFirebase(function (fb) {
      var $ = function (id) { return document.getElementById(id); };
      var DEFAULT_TPL = %DEFAULT_TPL%;
      var uid = null, business = 'our business', prevName = 'Solana';
      var nameInput = $('agent-name'), promptArea = $('system-prompt');
      if (!nameInput || !promptArea) return;

      function buildDefault(name, biz) {
        return DEFAULT_TPL.replace('{NAME}', name || 'Solana').replace('{BUSINESS}', biz || 'our business');
      }

      function applyUser(d) {
        business = (d && d.company) || 'our business';
        var name = (d && d.agentName) || 'Solana';
        var prompt = (d && d.systemPrompt) || buildDefault(name, business);
        if (!nameInput.value) nameInput.value = name;
        if (!promptArea.value) promptArea.value = prompt;
        prevName = name;
        var disp = $('agent-name-display');
        if (disp) disp.textContent = name;
      }

      fb.onAuthStateChanged(fb.auth, function (u) {
        if (!u) return;
        uid = u.uid;
        fb.getDoc(fb.doc(fb.db, 'users', uid)).then(function (snap) {
          if (snap.exists()) applyUser(snap.data());
          else applyUser({});
        });
      });

      // Live name -> prompt swap + sidebar card
      nameInput.addEventListener('input', function () {
        var oldName = prevName;
        var newName = nameInput.value || 'Solana';
        // Replace whole-word occurrences of oldName in the prompt
        if (oldName && oldName.length >= 2) {
          var re = new RegExp('\\\\b' + oldName.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b', 'gi');
          promptArea.value = promptArea.value.replace(re, newName);
        }
        prevName = newName;
        var disp = $('agent-name-display');
        if (disp) disp.textContent = newName;
      });

      // Reset to default
      var resetLink = document.createElement('button');
      resetLink.type = 'button';
      resetLink.className = 'mt-2 text-[12.5px] font-medium text-gray-500 hover:text-black underline';
      resetLink.textContent = 'Reset to default';
      resetLink.addEventListener('click', function () {
        promptArea.value = buildDefault(nameInput.value || 'Solana', business);
      });
      promptArea.parentNode.appendChild(resetLink);

      // Save both
      var saveBtn = $('save-prompt');
      if (saveBtn) {
        saveBtn.addEventListener('click', function () {
          if (!uid) return;
          var btn = this; btn.textContent = 'Saving…';
          fb.updateDoc(fb.doc(fb.db, 'users', uid), {
            agentName: nameInput.value.trim() || 'Solana',
            systemPrompt: promptArea.value.trim()
          }).then(function () {
            btn.textContent = 'Saved';
            setTimeout(function () { btn.textContent = 'Save changes'; }, 1200);
          }).catch(function () { btn.textContent = 'Save changes'; });
        });
      }

      // Presets use current agent name
      var PRESETS = {
        voice: 'You are {NAME}, a warm and friendly AI receptionist. Greet callers by name when possible, use natural conversational language, and always confirm the reason for the call before wrapping up.',
        booking: 'You are {NAME}, a booking-focused AI receptionist. Capture the caller\\'s name, preferred date, preferred time, and reason for visit, then confirm the appointment slot back to them.',
        support: 'You are {NAME}, a helpful support agent. Answer common questions clearly and briefly. If something is outside your knowledge, offer to take a callback message.'
      };
      document.querySelectorAll('.preset-btn').forEach(function (b) {
        b.addEventListener('click', function () {
          var tpl = PRESETS[b.dataset.preset] || '';
          promptArea.value = tpl.replace(/\\{NAME\\}/g, nameInput.value || 'Solana');
        });
      });

      // Default Gemini selected if no saved key
      fb.getDoc(fb.doc(fb.db, 'users', uid, 'private', 'ai')).then(function (snap) {
        var provider = snap.exists() ? (snap.data().provider || 'gemini') : 'gemini';
        var card = document.querySelector('.provider-card[data-provider="' + provider + '"]');
        if (card) card.click();
      }).catch(function () {
        var card = document.querySelector('.provider-card[data-provider="gemini"]');
        if (card) card.click();
      });
    });
  </script>
'''.replace("%DEFAULT_TPL%", repr(DEFAULT_PROMPT))

def page_solana(ctx):
    title, desc, body, main = _prev_solana(ctx)
    # Remove "Required for phone calls" if present
    body = body.replace(' <span class="ml-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">Required for phone calls</span>', '')
    return title, desc, body, main


# ---------- final render: inject solana extra script ----------
_prev_rp2 = render_page

def render_page(path, builder):
    html = _prev_rp2(path, builder)
    if Path(path).name == "solana.html" and "Reset to default" not in html:
        html = html.replace("</body>", SOLANA_EXTRA_JS + "\n</body>", 1)
    return html


# Rebind PAGES so our page_solana is used
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
]

# --- end edit.py: unified sidebar + smooth transitions + real prompts ---
"""


def strip_placeholders(src: str) -> int:
    """Remove leftover fake names and numbers from build.py."""
    count = 0
    for word in ["Maya", "Nina", "Patricia", "Marcus", "Daniel", "Taymoor"]:
        n = len(re.findall(r'\b' + word + r'\b', src))
        if n:
            src = re.sub(r'\b' + word + r'\b', 'Caller', src)
            count += n
    # (555) numbers
    src, n = re.subn(r'\(555\)\s*\d{3}-\d{4}', '(000) 000-0000', src); count += n
    for term in ['"+18%"', '"+4"', '"0 missed"', '"142 / 500"', '"Resets on November 1"',
                 '"Sample data"', '"Aria"']:
        n = src.count(term)
        if n:
            src = src.replace(term, '""')
            count += n
    return count


def patch_build_py() -> None:
    src = BUILD_PY.read_text(encoding="utf-8")

    if MARKER in src:
        print("  [skip] override already present")
        return

    if MAIN_GUARD not in src:
        print("  [warn] main guard not found")
        sys.exit(1)

    removed = strip_placeholders(src)
    if removed:
        print(f"  [ok]   stripped {removed} leftover placeholder(s)")

    src = src.replace(MAIN_GUARD, OVERRIDE + "\n\n" + MAIN_GUARD, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("  [ok]   appended unified sidebar + smooth transitions + real prompts")


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: could not find {BUILD_PY}")
        return 1

    print("Patching build.py …\n")
    patch_build_py()

    print("\nRunning build.py …\n")
    return subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())