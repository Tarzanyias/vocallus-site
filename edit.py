#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit.py — fix calendar shell, panel switching, number purchase, API key save.

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
MARKER = "# --- edit.py: bug fixes for calendar/panel/buy/key ---"
MAIN_GUARD = 'if __name__ == "__main__":'


OVERRIDE = r"""

# --- edit.py: bug fixes for calendar/panel/buy/key ---

# ---------------------------------------------------------------------------
# 1. render_page: route ALL four app pages through DASHBOARD_SHELL,
#    no marketing header or footer.
# ---------------------------------------------------------------------------

_prev_rp_bugfix = render_page

_APP_PAGES_FIX = {"dashboard.html", "solana.html", "calendar.html", "history.html"}

def render_page(path, builder):
    name = Path(path).name

    if name in _APP_PAGES_FIX:
        depth = len(Path(path).parts) - 1
        ctx = Ctx(depth)
        title, description, content, _main = builder(ctx)
        head = HEAD.substitute(
            title=title,
            description=description,
            css=SHARED_CSS,
            favicon=ctx.img(FAVICON_IMAGE),
        )
        extra = ""
        if name == "dashboard.html":  extra = DASH_JS
        elif name == "solana.html":   extra = SOLANA_JS
        elif name == "history.html":  extra = HISTORY_JS_V2
        elif name == "calendar.html": extra = CALENDAR_JS

        html = DASHBOARD_SHELL.substitute(
            head=head,
            content=content,
            scripts=SHARED_JS + extra,
        )
        if "page transitions" not in html:
            html = html.replace("</style>", _FADE_CSS + "\n  </style>", 1)
        if "Hide main until Firebase auth resolves" not in html:
            html = html.replace("</body>", _AUTH_GATE_JS + "\n</body>", 1)
        if name == "dashboard.html" and "PANEL_FIX_MARKER" not in html:
            html = html.replace("</body>", _DASH_PANEL_FIX_JS + "\n</body>", 1)
        if name == "solana.html" and "SOLANA_KEY_FIX_MARKER" not in html:
            html = html.replace("</body>", _SOLANA_KEY_FIX_JS + "\n</body>", 1)
        return html

    return _prev_rp_bugfix(path, builder)


# ---------------------------------------------------------------------------
# 2. Dashboard panel switching — works with .app-tab[data-nav]
# ---------------------------------------------------------------------------

_DASH_PANEL_FIX_JS = '''
  <script>
    /* PANEL_FIX_MARKER */
    (function () {
      var path = window.location.pathname.replace(/\\\\/g, '/');
      if (!/dashboard\\.html$/.test(path)) return;

      function activate(name) {
        document.querySelectorAll('.panel').forEach(function (p) {
          p.classList.toggle('hidden', p.id !== 'panel-' + name);
        });
        document.querySelectorAll('.app-tab[data-nav]').forEach(function (t) {
          var on = t.dataset.nav === name;
          t.classList.toggle('bg-gray-200/80', on);
          t.classList.toggle('text-gray-900', on);
          t.classList.toggle('text-gray-500', !on);
          var bar = t.querySelector('.app-bar');
          if (bar) {
            bar.classList.toggle('opacity-100', on);
            bar.classList.toggle('opacity-0', !on);
          }
        });
      }

      document.querySelectorAll('.app-tab[data-nav]').forEach(function (t) {
        t.addEventListener('click', function (e) {
          var href = t.getAttribute('href') || '';
          var i = href.indexOf('#');
          if (i === -1) return;
          var target = href.slice(0, i);
          if (target && target !== 'dashboard.html') return;
          var panel = href.slice(i + 1);
          if (!document.getElementById('panel-' + panel)) return;
          e.preventDefault();
          activate(panel);
          if (history.replaceState) history.replaceState(null, '', '#' + panel);
        });
      });

      var initial = (location.hash || '').replace('#', '') || 'home';
      if (!document.getElementById('panel-' + initial)) initial = 'home';
      activate(initial);

      window.addEventListener('hashchange', function () {
        var h = (location.hash || '').replace('#', '') || 'home';
        if (document.getElementById('panel-' + h)) activate(h);
      });
    })();
  </script>
'''


# ---------------------------------------------------------------------------
# 3. Number buy — read data.numbers, disable Choose, live switch
# ---------------------------------------------------------------------------

_DASH_PANEL_FIX_JS += '''
  <script>
    /* NUMBER_BUY_FIX_MARKER */
    window.whenFirebase && window.whenFirebase(function (fb) {
      var $ = function (id) { return document.getElementById(id); };
      var searchBtn = $('search-numbers');
      if (!searchBtn) return;

      searchBtn.addEventListener('click', async function () {
        var ac = ($('area-code').value || '').trim();
        var status = $('search-status');
        var results = $('search-results');
        results.innerHTML = '';
        if (!/^\\d{3}$/.test(ac)) { status.textContent = 'Enter a 3-digit area code.'; return; }
        status.textContent = 'Searching…';
        searchBtn.disabled = true;
        try {
          var r = await window.bridgeFetch('/api/numbers/search?areaCode=' + ac);
          var data = await r.json();
          if (!r.ok) throw new Error(data.error || ('Search failed (' + r.status + ')'));
          var list = (data && data.numbers) ? data.numbers : [];
          if (!list.length) {
            status.textContent = 'No numbers in that area code, try another.';
            return;
          }
          status.textContent = list.length + ' number' + (list.length === 1 ? '' : 's') + ' available';
          list.forEach(function (item) {
            var row = document.createElement('div');
            row.className = 'flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3';
            row.innerHTML =
              '<div>' +
                '<div class="font-semibold text-[15px] text-gray-900">' + (item.friendlyName || item.phoneNumber) + '</div>' +
                '<div class="text-[12px] text-gray-500">' + ((item.locality || '') + (item.region ? ', ' + item.region : '')) + '</div>' +
              '</div>' +
              '<button class="choose-btn btn-primary px-4 py-2 rounded-lg font-semibold text-[13px]">Choose</button>';
            var btn = row.querySelector('.choose-btn');
            btn.addEventListener('click', async function () {
              if (!confirm('Assign ' + (item.friendlyName || item.phoneNumber) + ' to your account?')) return;
              var allBtns = document.querySelectorAll('.choose-btn');
              allBtns.forEach(function (b) { b.disabled = true; b.style.opacity = '0.5'; });
              status.textContent = 'Setting up your number…';
              try {
                var resp = await window.bridgeFetch('/api/numbers/buy', {
                  method: 'POST',
                  body: { phoneNumber: item.phoneNumber }
                });
                var j = await resp.json();
                if (!resp.ok) throw new Error(j.error || ('Purchase failed (' + resp.status + ')'));
                status.textContent = 'Number assigned!';
              } catch (err) {
                status.textContent = err.message || String(err);
                allBtns.forEach(function (b) { b.disabled = false; b.style.opacity = ''; });
              }
            });
            results.appendChild(row);
          });
        } catch (err) {
          status.textContent = err.message || String(err);
        } finally {
          searchBtn.disabled = false;
        }
      });
    });
  </script>
'''


# ---------------------------------------------------------------------------
# 4. Solana key save — masked text, real validation, Replace button
# ---------------------------------------------------------------------------

_SOLANA_KEY_FIX_JS = '''
  <script>
    /* SOLANA_KEY_FIX_MARKER */
    window.whenFirebase && window.whenFirebase(function (fb) {
      var $ = function (id) { return document.getElementById(id); };
      var keyInput = $('api-key');
      var saveBtn  = $('save-key');
      var savedBox = $('key-saved');
      var masked   = $('key-masked');
      var replaceBtn = $('key-replace');
      if (!keyInput || !saveBtn || !savedBox) return;

      var keyDocRef = null;
      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) return;
        keyDocRef = fb.doc(fb.db, 'users', user.uid, 'private', 'ai');
        // Load existing
        fb.getDoc(keyDocRef).then(function (snap) {
          if (snap.exists()) {
            var d = snap.data();
            var k = d.apiKey || '';
            masked.textContent = k.slice(0, 4) + '\\u2026' + k.slice(-4);
            savedBox.classList.remove('hidden');
            keyInput.style.display = 'none';
            saveBtn.style.display = 'none';
          }
        });
      });

      replaceBtn.addEventListener('click', function () {
        savedBox.classList.add('hidden');
        keyInput.value = '';
        keyInput.style.display = '';
        saveBtn.style.display = '';
        keyInput.focus();
      });

      // NOTE: the original save-key listener still fires too, but our new
      // listener (added later) will handle the same click. To avoid double
      // handling, capture the click in a capture-phase listener and stop
      // propagation before the old one runs.
      saveBtn.addEventListener('click', async function (e) {
        e.stopImmediatePropagation();
        e.preventDefault();
        var errBox = $('api-error'), errTitle = $('api-error-title'), errMsg = $('api-error-msg');
        function showErr(t, m) { errTitle.textContent = t; errMsg.textContent = m; errBox.classList.remove('hidden'); }
        function hideErr() { errBox.classList.add('hidden'); }
        hideErr();

        var user = fb.auth.currentUser;
        if (!user) { showErr('Not signed in', 'Please sign in again.'); return; }

        // Provider detection: whichever .provider-card has the black ring
        var active = document.querySelector('.provider-card.border-black, .provider-card.selected');
        var provider = active ? active.dataset.provider : null;
        if (!provider) { showErr('No provider selected', 'Pick a provider above.'); return; }

        var key = keyInput.value.trim();
        if (!key) { showErr('API key required', 'Paste a key from your ' + provider + ' account.'); return; }

        var orig = saveBtn.textContent;
        saveBtn.disabled = true;
        saveBtn.textContent = 'Checking key\\u2026';
        try {
          if (provider === 'gemini') {
            var r = await fetch('https://generativelanguage.googleapis.com/v1beta/models?key=' + encodeURIComponent(key));
            if (!r.ok) throw new Error("That key didn't work. Check it and try again.");
          } else if (provider === 'openai') {
            if (key.indexOf('sk-') !== 0) throw new Error('OpenAI keys start with "sk-".');
          } else if (provider === 'claude') {
            if (key.indexOf('sk-ant-') !== 0) throw new Error('Claude keys start with "sk-ant-".');
          }
          var model = provider === 'gemini' ? 'gemini-2.5-flash'
                    : provider === 'openai' ? 'gpt-4o-mini'
                    : 'claude-3-5-haiku-20241022';
          await fb.setDoc(fb.doc(fb.db, 'users', user.uid, 'private', 'ai'), {
            provider: provider, apiKey: key, model: model
          });
          masked.textContent = key.slice(0, 4) + '\\u2026' + key.slice(-4);
          savedBox.classList.remove('hidden');
          keyInput.value = '';
          keyInput.style.display = 'none';
          saveBtn.style.display = 'none';
        } catch (err) {
          showErr('Key check failed', err.message || String(err));
        } finally {
          saveBtn.disabled = false;
          saveBtn.textContent = orig;
        }
      }, true);  // capture phase: runs before the old listener
    });
  </script>
'''


# Rebind PAGES to the latest builders
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

# --- end edit.py: bug fixes for calendar/panel/buy/key ---
"""


def patch_build_py() -> None:
    src = BUILD_PY.read_text(encoding="utf-8")

    if MARKER in src:
        print("  [skip] bug-fix override already present")
        return

    if MAIN_GUARD not in src:
        print("  [warn] main guard not found")
        sys.exit(1)

    src = src.replace(MAIN_GUARD, OVERRIDE + "\n\n" + MAIN_GUARD, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("  [ok]   appended bug-fix override")


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