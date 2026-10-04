#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit.py — replace all mock data with real Firestore, wire the Number tab to
the Railway bridge, and finish the History/Finances panels.

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

MARKER = "# --- edit.py: real Firestore data ---"
MAIN_GUARD = 'if __name__ == "__main__":'


OVERRIDE = r"""

# --- edit.py: real Firestore data ---

BRIDGE = "https://vocallus-bridge-production.up.railway.app"

# Shared helper script — every app page loads Firebase via
# window.whenFirebase; this adds an authed bridge fetch.
BRIDGE_HELPER = '''
  <script>
    window.bridgeFetch = async function (path, opts) {
      if (!window.__fb) throw new Error('Firebase not ready');
      var user = window.__fb.auth.currentUser;
      if (!user) throw new Error('Not signed in');
      var token = await user.getIdToken();
      opts = opts || {};
      opts.headers = Object.assign({}, opts.headers || {}, {
        'Authorization': 'Bearer ' + token
      });
      if (opts.body && typeof opts.body === 'object') {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(opts.body);
      }
      return fetch('__BRIDGE__' + path, opts);
    };
  </script>
'''.replace('__BRIDGE__', BRIDGE)


# ---------------------------------------------------------------------------
# Dashboard — new markup
# ---------------------------------------------------------------------------

DASH_HOME = '''
    <div id="panel-home" class="panel max-w-[1200px] mx-auto px-8 py-8">

      <div class="bg-white rounded-3xl shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-gray-100 p-8 mb-8 flex justify-between items-center relative overflow-hidden h-[180px]">
        <div class="z-10 mt-[-20px]">
          <p id="today-date" class="text-gray-800 text-[22px] mb-2 font-medium"></p>
          <h1 class="text-[32px] font-semibold text-gray-900">Good morning, <span id="greeting-name">there</span></h1>
          <p id="banner-line" class="text-gray-500 text-[15px] mt-2">Loading…</p>
        </div>
        <div class="absolute right-0 top-0 bottom-0 w-[400px] pointer-events-none flex items-center justify-end">
          <svg width="400" height="180" viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg" class="absolute right-0">
            <path d="M 200 40 Q 230 20 260 40 Q 290 20 320 50" stroke="#f3f4f6" stroke-width="4" fill="none" stroke-linecap="round"/>
            <circle cx="250" cy="50" r="40" fill="#f9fafb" />
            <circle cx="300" cy="60" r="30" fill="#f9fafb" />
            <path d="M 360 30 L 260 70 L 320 90 Z" fill="#d4d4d4" />
            <path d="M 360 30 L 320 90 L 310 110 L 340 80 Z" fill="#a3a3a3" />
            <path d="M 330 80 L 350 140 L 380 90 Z" fill="#22c55e" />
            <path d="M 330 80 L 320 120 L 340 125 Z" fill="#16a34a" />
            <path d="M 230 80 L 250 120 L 290 100 Z" fill="#3b82f6" />
            <path d="M 230 80 L 240 105 L 260 100 Z" fill="#2563eb" />
          </svg>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
              <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            </div>
          </div>
          <div class="text-[13px] text-gray-500 font-medium">Calls today</div>
          <div id="stat-calls" class="text-[28px] font-semibold text-gray-900 mt-1">0</div>
        </div>
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
              <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            </div>
          </div>
          <div class="text-[13px] text-gray-500 font-medium">Booked by Solana</div>
          <div id="stat-appts" class="text-[28px] font-semibold text-gray-900 mt-1">0</div>
          <div class="text-[12px] text-gray-400 mt-1">This week</div>
        </div>
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
              <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
          </div>
          <div class="text-[13px] text-gray-500 font-medium">Avg call length</div>
          <div id="stat-avg" class="text-[28px] font-semibold text-gray-900 mt-1">0:00</div>
          <div class="text-[12px] text-gray-400 mt-1">Last 7 days</div>
        </div>
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
              <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            </div>
          </div>
          <div class="text-[13px] text-gray-500 font-medium">Minutes used</div>
          <div id="stat-minutes" class="text-[28px] font-semibold text-gray-900 mt-1">0</div>
          <div class="text-[12px] text-gray-400 mt-1">of <span id="stat-limit">0</span> this month</div>
          <div class="mt-3 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div id="minutes-bar" class="h-full bg-black rounded-full" style="width:0%"></div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-3xl border border-gray-100 p-7 mb-8 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-[19px] font-semibold text-gray-900">Call volume</h2>
            <p class="text-[13px] text-gray-500 mt-0.5">Last 7 days</p>
          </div>
        </div>
        <div id="chart" class="flex items-end justify-between gap-3 h-[180px]"></div>
        <div id="chart-labels" class="flex justify-between gap-3 mt-3 text-[12px] text-gray-400 font-medium"></div>
      </div>

      <div class="relative mb-6">
        <svg class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input id="call-search" type="text" placeholder="Search by caller number" class="w-full pl-12 pr-4 py-[14px] rounded-2xl border border-gray-300 focus:outline-none focus:border-gray-400 hover:border-gray-400 text-[15px] shadow-sm">
      </div>

      <div class="flex items-center justify-between border-b border-gray-200 mb-0">
        <div class="flex space-x-8">
          <button class="text-black font-medium pb-4 border-b-2 border-black text-[15px]">Recent calls</button>
        </div>
      </div>

      <div id="call-list" class="flex flex-col"></div>

      <div class="w-full flex flex-col gap-6 mt-8">
        <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 pt-8 pb-8">
          <div class="flex items-center mb-6">
            <div class="w-16 h-16 rounded-full bg-white flex items-center justify-center mr-4 relative border border-gray-200 flex-shrink-0">
              <img src="../Images/logo.png" class="w-full h-full rounded-full object-cover" alt="">
              <span class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-[#f9fafb]"></span>
            </div>
            <div>
              <h2 class="font-medium text-lg" id="right-agent-name">Solana</h2>
              <p class="text-[13px] text-gray-500 mt-1">Online &amp; answering</p>
            </div>
          </div>
          <div class="space-y-4">
            <div>
              <div class="text-[15px] font-medium mb-1">Current number</div>
              <div class="text-[15px] text-gray-700" id="right-number">None</div>
            </div>
            <div class="pt-2">
              <div class="text-[15px] font-medium mb-1">Plan</div>
              <div class="text-[15px] text-gray-700" id="right-plan">None</div>
            </div>
            <div class="pt-4">
              <a href="solana.html" class="text-[15px] font-medium text-black hover:underline decoration-1 underline-offset-2">Configure Solana</a>
            </div>
          </div>
        </div>

        <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 pb-8">
          <div class="flex justify-between items-center mb-6">
            <span class="font-medium text-[19px] text-gray-900">Live activity</span>
          </div>
          <div id="activity-feed" class="space-y-5">
            <div class="text-[13px] text-gray-400">No activity yet.</div>
          </div>
        </div>
      </div>
    </div>
'''

DASH_NUMBER = '''
    <div id="panel-number" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
      <div class="mb-8">
        <h1 class="text-[32px] font-semibold text-gray-900">Number</h1>
        <p class="text-gray-500 text-[15px] mt-1">The phone number Solana answers.</p>
      </div>

      <div id="number-has" class="hidden">
        <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)] mb-6">
          <div class="text-[13px] text-gray-500 font-medium mb-2">Your Solana number</div>
          <div class="flex items-center gap-3 flex-wrap">
            <div id="number-value" class="text-[32px] font-semibold text-gray-900 tracking-tight">(000) 000-0000</div>
            <button id="copy-number" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13px] font-semibold hover:bg-gray-50">Copy</button>
          </div>
          <p class="text-[14px] text-gray-500 mt-3">Solana answers this number 24/7.</p>
        </div>

        <div class="bg-[#f9fafb] rounded-3xl border border-gray-100 p-8">
          <h2 class="text-[18px] font-semibold text-gray-900 mb-2">Keep your existing business number</h2>
          <p class="text-[14px] text-gray-600 mb-5">Enter the number your customers already know, then forward it to your Solana number.</p>
          <div class="flex items-center gap-3 flex-wrap mb-5">
            <input id="forward-from" type="tel" placeholder="(555) 123-4567" class="flex-1 min-w-[220px] rounded-xl border border-gray-200 px-4 py-3 text-[15px] focus:outline-none focus:border-gray-400 bg-white">
            <button id="save-forward" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Save number</button>
          </div>
          <div class="rounded-2xl bg-white border border-gray-200 p-5">
            <div class="text-[13px] font-semibold text-gray-700 uppercase tracking-wide mb-2">How to forward</div>
            <p class="text-[14px] leading-[1.6] text-gray-600">Turn on call forwarding from your current phone line to your Solana number. Most carriers: dial <span class="font-mono font-semibold text-gray-900">*72</span> then your Solana number, and <span class="font-mono font-semibold text-gray-900">*73</span> to turn it off. Some carriers differ — check with yours.</p>
          </div>
          <p id="forward-saved" class="hidden text-[13px] font-semibold text-green-700 mt-3">Saved.</p>
        </div>
      </div>

      <div id="number-none" class="hidden">
        <div id="plan-required" class="hidden bg-white rounded-3xl border border-gray-100 p-10 text-center shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
          <h2 class="text-[22px] font-semibold text-gray-900 mb-2">Choose a plan to get your Solana number</h2>
          <p class="text-[15px] text-gray-500 mb-6">You need an active plan before we can assign a phone number.</p>
          <a href="pricing.html" class="btn-primary inline-flex items-center justify-center px-6 py-3 rounded-xl font-semibold text-[15px]">See plans</a>
        </div>

        <div id="plan-active" class="hidden grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
            <h2 class="text-[18px] font-semibold text-gray-900 mb-2">Get a new number</h2>
            <p class="text-[14px] text-gray-500 mb-5">Pick an area code and we&rsquo;ll show available numbers.</p>
            <div class="flex items-center gap-3 mb-5">
              <input id="area-code" type="text" inputmode="numeric" maxlength="3" placeholder="832" class="w-[120px] rounded-xl border border-gray-200 px-4 py-3 text-[15px] text-center tracking-widest focus:outline-none focus:border-gray-400">
              <button id="search-numbers" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Search</button>
            </div>
            <div id="search-status" class="text-[13px] text-gray-500"></div>
            <div id="search-results" class="mt-4 space-y-2 max-h-[320px] overflow-y-auto custom-scrollbar"></div>
          </div>

          <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
            <h2 class="text-[18px] font-semibold text-gray-900 mb-2">Use my existing number</h2>
            <p class="text-[14px] text-gray-500 mb-5">You still get a Solana number — you just forward your current line to it.</p>
            <button id="switch-to-buy" class="inline-flex items-center justify-center px-5 py-3 rounded-xl border border-neutral-200 text-neutral-800 font-semibold text-[14px] hover:bg-neutral-50">Get a Solana number first</button>
          </div>
        </div>
      </div>
    </div>
'''

DASH_FINANCES = '''
    <div id="panel-finances" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
      <div class="mb-8">
        <h1 class="text-[32px] font-semibold text-gray-900">Finances</h1>
        <p class="text-gray-500 text-[15px] mt-1">Plan and usage.</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="text-[13px] text-gray-500 font-medium">Current plan</div>
          <div id="fin-plan" class="text-[24px] font-semibold text-gray-900 mt-1">None</div>
        </div>
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
          <div class="text-[13px] text-gray-500 font-medium">Minutes used</div>
          <div class="text-[24px] font-semibold text-gray-900 mt-1"><span id="fin-minutes">0</span> / <span id="fin-limit">0</span></div>
        </div>
        <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6 flex items-center">
          <a href="pricing.html" class="btn-primary inline-flex items-center justify-center px-5 py-3 rounded-xl font-semibold text-[14px] w-full">Change plan</a>
        </div>
      </div>
    </div>
'''


# ---------------------------------------------------------------------------
# Dashboard JS — real Firestore
# ---------------------------------------------------------------------------

DASH_JS = '''
  <script>
    window.requireAuth && window.requireAuth();
    window.whenFirebase && window.whenFirebase(function (fb) {
      var $ = function (id) { return document.getElementById(id); };
      var uid = null, user = null, plan = 'none';
      var calls = [];
      var appts = [];
      var PLAN_LIMITS = { none: 0, pro: 300, max: 1500 };
      var bridgeBase = "https://vocallus-bridge-production.up.railway.app";

      /* ---------- helpers ---------- */
      function fmtPhone(n) {
        if (!n) return '';
        var digits = String(n).replace(/\\D/g, '');
        if (digits.length === 11 && digits[0] === '1') digits = digits.slice(1);
        if (digits.length === 10) return '(' + digits.slice(0,3) + ') ' + digits.slice(3,6) + '-' + digits.slice(6);
        return n;
      }
      function timeAgo(ts) {
        if (!ts) return '';
        var d = ts.toDate ? ts.toDate() : new Date(ts);
        var s = Math.floor((Date.now() - d.getTime()) / 1000);
        if (s < 60) return 'just now';
        if (s < 3600) return Math.floor(s/60) + ' min ago';
        if (s < 86400) return Math.floor(s/3600) + ' hr ago';
        return Math.floor(s/86400) + ' d ago';
      }
      function fmtDur(sec) {
        sec = sec || 0;
        var m = Math.floor(sec/60), s = sec % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
      }
      function startOfDay(d) { var x = new Date(d); x.setHours(0,0,0,0); return x; }
      function startOfWeek(d) {
        var x = startOfDay(d);
        var day = x.getDay();
        var diff = day === 0 ? -6 : 1 - day;
        x.setDate(x.getDate() + diff);
        return x;
      }
      function startOfMonth(d) { var x = new Date(d.getFullYear(), d.getMonth(), 1); return x; }
      function asDate(ts) { return ts && ts.toDate ? ts.toDate() : (ts ? new Date(ts) : null); }
      function greeting() {
        var h = new Date().getHours();
        if (h < 12) return 'Good morning';
        if (h < 18) return 'Good afternoon';
        return 'Good evening';
      }

      /* ---------- banner ---------- */
      var g = new Date();
      $('today-date').textContent = g.toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric' });

      /* ---------- user doc ---------- */
      function applyUser(d) {
        plan = d.plan || 'none';
        var first = (d.name || '').split(' ')[0] || user.displayName && user.displayName.split(' ')[0] || 'there';
        document.querySelector('#panel-home h1').innerHTML = greeting() + ', <span id="greeting-name">' + first + '</span>';
        $('right-agent-name').textContent = d.agentName || 'Solana';
        $('right-number').textContent = d.phoneNumber ? fmtPhone(d.phoneNumber) : 'None';
        $('right-plan').textContent = plan === 'none' ? 'None' : plan.charAt(0).toUpperCase() + plan.slice(1);
        $('fin-plan').textContent = plan === 'none' ? 'None' : plan.charAt(0).toUpperCase() + plan.slice(1);
        $('fin-limit').textContent = PLAN_LIMITS[plan] || 0;

        /* Number panel */
        if (d.phoneNumber) {
          $('number-has').classList.remove('hidden');
          $('number-none').classList.add('hidden');
          $('number-value').textContent = fmtPhone(d.phoneNumber);
          if (d.forwardingFrom) $('forward-from').value = d.forwardingFrom;
        } else {
          $('number-has').classList.add('hidden');
          $('number-none').classList.remove('hidden');
          if (plan === 'none') {
            $('plan-required').classList.remove('hidden');
            $('plan-active').classList.add('hidden');
          } else {
            $('plan-required').classList.add('hidden');
            $('plan-active').classList.remove('hidden');
          }
        }
      }

      /* ---------- stats + chart ---------- */
      function recompute() {
        var now = new Date();
        var dayStart = startOfDay(now).getTime();
        var weekStart = startOfWeek(now).getTime();
        var monthStart = startOfMonth(now).getTime();
        var sevenDaysAgo = dayStart - 6 * 86400000;

        var todayCalls = calls.filter(function (c) {
          var t = asDate(c.startedAt); return t && t.getTime() >= dayStart;
        });
        $('stat-calls').textContent = todayCalls.length;
        $('banner-line').textContent = todayCalls.length
          ? ('Solana answered ' + todayCalls.length + ' call' + (todayCalls.length === 1 ? '' : 's') + ' today')
          : 'No calls yet today';

        var aiBookings = appts.filter(function (a) {
          if (a.source !== 'ai') return false;
          var t = asDate(a.createdAt); return t && t.getTime() >= weekStart;
        });
        $('stat-appts').textContent = aiBookings.length;

        var last7 = calls.filter(function (c) {
          var t = asDate(c.startedAt); return t && t.getTime() >= sevenDaysAgo;
        });
        var totalSec = last7.reduce(function (s, c) { return s + (c.durationSec || 0); }, 0);
        var avg = last7.length ? Math.round(totalSec / last7.length) : 0;
        $('stat-avg').textContent = fmtDur(avg);

        var monthCalls = calls.filter(function (c) {
          var t = asDate(c.startedAt); return t && t.getTime() >= monthStart;
        });
        var monthSec = monthCalls.reduce(function (s, c) { return s + (c.durationSec || 0); }, 0);
        var minutes = Math.round(monthSec / 60);
        $('stat-minutes').textContent = minutes;
        $('stat-limit').textContent = PLAN_LIMITS[plan] || 0;
        $('fin-minutes').textContent = minutes;
        var pct = PLAN_LIMITS[plan] ? Math.min(100, (minutes / PLAN_LIMITS[plan]) * 100) : 0;
        $('minutes-bar').style.width = pct + '%';

        /* chart: last 7 days */
        var counts = [];
        for (var i = 6; i >= 0; i--) {
          var d0 = startOfDay(new Date(Date.now() - i * 86400000));
          var d1 = d0.getTime() + 86400000;
          var n = calls.filter(function (c) {
            var t = asDate(c.startedAt); return t && t.getTime() >= d0.getTime() && t.getTime() < d1;
          }).length;
          counts.push({ day: d0.toLocaleDateString('en-US', { weekday:'short' }), n: n });
        }
        var chart = $('chart'), labels = $('chart-labels');
        chart.innerHTML = ''; labels.innerHTML = '';
        var max = Math.max.apply(null, counts.map(function (c) { return c.n; }).concat([1]));
        counts.forEach(function (c) {
          var col = document.createElement('div');
          col.className = 'flex-1 flex flex-col justify-end';
          col.innerHTML = '<div class="rounded-t-md bg-black" style="height:' + ((c.n / max) * 100) + '%"></div>';
          chart.appendChild(col);
          var lbl = document.createElement('div');
          lbl.className = 'flex-1 text-center';
          lbl.textContent = c.day;
          labels.appendChild(lbl);
        });

        renderCalls();
        renderActivity();
      }

      /* ---------- recent calls ---------- */
      var searchQ = '';
      function renderCalls() {
        var list = $('call-list');
        var sorted = calls.slice().sort(function (a, b) {
          var ta = asDate(a.startedAt), tb = asDate(b.startedAt);
          return (tb ? tb.getTime() : 0) - (ta ? ta.getTime() : 0);
        });
        if (searchQ) {
          sorted = sorted.filter(function (c) {
            return (c.from || '').replace(/\\D/g, '').indexOf(searchQ.replace(/\\D/g, '')) !== -1;
          });
        }
        sorted = sorted.slice(0, 20);

        if (!sorted.length) {
          list.innerHTML = '<div class="py-16 text-center"><p class="text-gray-400 text-[15px]">No calls yet — call your Solana number to test it.</p></div>';
          return;
        }

        list.innerHTML = '';
        sorted.forEach(function (c) {
          var row = document.createElement('div');
          row.className = 'bg-white p-6 pb-8 border-b border-gray-200';
          var dur = c.durationSec ? fmtDur(c.durationSec) : '—';
          var status = c.status || 'completed';
          var tag = status === 'missed' ? 'bg-red-50 text-red-700' :
                    status === 'in_progress' ? 'bg-blue-50 text-blue-700' :
                    'bg-green-50 text-green-700';
          row.innerHTML =
            '<div class="flex items-center gap-3 flex-wrap mb-2">' +
              '<div class="text-[15px] font-semibold text-gray-900">' + (fmtPhone(c.from) || 'Unknown') + '</div>' +
              '<div class="text-[13px] text-gray-500">' + timeAgo(c.startedAt) + '</div>' +
              '<span class="ml-auto text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ' + tag + '">' + status.replace('_',' ') + '</span>' +
            '</div>' +
            '<div class="text-[13px] text-gray-500">Duration: ' + dur + '</div>';
          list.appendChild(row);
        });
      }
      $('call-search').addEventListener('input', function (e) {
        searchQ = e.target.value.trim();
        renderCalls();
      });

      /* ---------- activity feed ---------- */
      function renderActivity() {
        var feed = $('activity-feed');
        var events = [];
        calls.slice(0, 20).forEach(function (c) {
          var t = asDate(c.startedAt);
          if (t) events.push({ t: t, text: 'Call from ' + (fmtPhone(c.from) || 'Unknown') });
        });
        appts.filter(function (a) { return a.source === 'ai'; }).slice(0, 20).forEach(function (a) {
          var t = asDate(a.createdAt);
          if (t) {
            var start = asDate(a.start);
            var when = start ? start.toLocaleString([], { weekday:'short', hour:'numeric', minute:'2-digit' }) : '';
            events.push({ t: t, text: 'Solana booked ' + (a.customerName || 'a caller') + (when ? ' for ' + when : '') });
          }
        });
        events.sort(function (a, b) { return b.t - a.t; });
        events = events.slice(0, 8);
        if (!events.length) {
          feed.innerHTML = '<div class="text-[13px] text-gray-400">No activity yet.</div>';
          return;
        }
        feed.innerHTML = '';
        events.forEach(function (e) {
          var el = document.createElement('div');
          el.className = 'flex items-start gap-3';
          el.innerHTML = '<div class="w-8 h-8 rounded-full bg-black flex items-center justify-center flex-shrink-0 mt-0.5"><svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><div class="flex-1 min-w-0"><p class="text-[14px] text-gray-800 leading-[1.5]"></p><p class="text-[12px] text-gray-400 mt-0.5">' + timeAgo(e.t) + '</p></div>';
          el.querySelector('p').textContent = e.text;
          feed.appendChild(el);
        });
      }

      /* ---------- auth + subscriptions ---------- */
      fb.onAuthStateChanged(fb.auth, function (u) {
        if (!u) return;
        user = u; uid = u.uid;

        fb.onSnapshot(fb.doc(fb.db, 'users', uid), function (snap) {
          if (snap.exists()) applyUser(snap.data());
        });

        fb.onSnapshot(fb.collection(fb.db, 'users', uid, 'calls'), function (s) {
          calls = [];
          s.forEach(function (d) { var x = d.data(); x.id = d.id; calls.push(x); });
          recompute();
        });

        fb.onSnapshot(fb.collection(fb.db, 'users', uid, 'appointments'), function (s) {
          appts = [];
          s.forEach(function (d) { var x = d.data(); x.id = d.id; appts.push(x); });
          recompute();
        });

        var so = document.getElementById('signout-btn');
        if (so) so.addEventListener('click', function () {
          fb.signOut(fb.auth).then(function () { window.location.href = 'login.html'; });
        });
      });

      /* ---------- Number tab actions ---------- */
      $('copy-number').addEventListener('click', function () {
        var val = $('number-value').textContent;
        navigator.clipboard.writeText(val).then(function () {
          var b = $('copy-number'); b.textContent = 'Copied';
          setTimeout(function () { b.textContent = 'Copy'; }, 1200);
        });
      });

      $('save-forward').addEventListener('click', function () {
        if (!uid) return;
        var val = $('forward-from').value.trim();
        fb.updateDoc(fb.doc(fb.db, 'users', uid), { forwardingFrom: val }).then(function () {
          var s = $('forward-saved'); s.classList.remove('hidden');
          setTimeout(function () { s.classList.add('hidden'); }, 1500);
        });
      });

      $('search-numbers').addEventListener('click', async function () {
        var ac = ($('area-code').value || '').trim();
        if (!/^\\d{3}$/.test(ac)) { $('search-status').textContent = 'Enter a 3-digit area code.'; return; }
        $('search-status').textContent = 'Searching…';
        $('search-results').innerHTML = '';
        try {
          var r = await window.bridgeFetch('/api/numbers/search?areaCode=' + ac);
          var data = await r.json();
          if (!r.ok) throw new Error(data.error || ('Search failed (' + r.status + ')'));
          $('search-status').textContent = data.length + ' number' + (data.length === 1 ? '' : 's') + ' available';
          data.forEach(function (item) {
            var row = document.createElement('div');
            row.className = 'flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3';
            row.innerHTML = '<div><div class="font-semibold text-[15px] text-gray-900">' + (item.friendlyName || item.phoneNumber) + '</div><div class="text-[12px] text-gray-500">' + ((item.locality || '') + (item.region ? ', ' + item.region : '')) + '</div></div><button class="btn-primary px-4 py-2 rounded-lg font-semibold text-[13px]">Choose</button>';
            row.querySelector('button').addEventListener('click', async function () {
              if (!confirm('Assign ' + (item.friendlyName || item.phoneNumber) + ' to your account?')) return;
              try {
                var resp = await window.bridgeFetch('/api/numbers/buy', {
                  method: 'POST',
                  body: { phoneNumber: item.phoneNumber }
                });
                var j = await resp.json();
                if (!resp.ok) throw new Error(j.error || ('Purchase failed (' + resp.status + ')'));
                $('search-status').textContent = 'Number assigned!';
              } catch (err) {
                $('search-status').textContent = err.message || String(err);
              }
            });
            $('search-results').appendChild(row);
          });
        } catch (err) {
          $('search-status').textContent = err.message || String(err);
        }
      });

      $('switch-to-buy').addEventListener('click', function () {
        $('area-code').focus();
      });
    });
  </script>
'''


# ---------------------------------------------------------------------------
# History page — real data
# ---------------------------------------------------------------------------

HISTORY_BODY_V2 = '''{sidebar}
    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl border-l border-gray-200">
        <div class="max-w-[1100px] mx-auto px-8 py-8">
            <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
                <div>
                    <h1 class="text-[28px] font-semibold text-gray-900">History</h1>
                    <p class="text-gray-500 text-[14px] mt-0.5">Every call Solana has handled.</p>
                </div>
                <div class="flex bg-gray-100 rounded-full p-1">
                    <button data-range="all" class="hist-filter px-5 py-2 rounded-full text-[14px] font-semibold bg-white shadow-sm text-gray-900">All</button>
                    <button data-range="today" class="hist-filter px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">Today</button>
                    <button data-range="week" class="hist-filter px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">This week</button>
                </div>
            </div>
            <div id="history-list" class="space-y-3"></div>
        </div>
    </main>'''


HISTORY_JS_V2 = '''
  <script>
    window.requireAuth && window.requireAuth();
    window.whenFirebase && window.whenFirebase(function (fb) {
      var uid = null, calls = [], range = 'all';
      var $ = function (id) { return document.getElementById(id); };

      function asDate(ts) { return ts && ts.toDate ? ts.toDate() : (ts ? new Date(ts) : null); }
      function fmtPhone(n) {
        if (!n) return '';
        var d = String(n).replace(/\\D/g, '');
        if (d.length === 11 && d[0] === '1') d = d.slice(1);
        if (d.length === 10) return '(' + d.slice(0,3) + ') ' + d.slice(3,6) + '-' + d.slice(6);
        return n;
      }
      function fmtDur(sec) {
        sec = sec || 0; var m = Math.floor(sec/60), s = sec % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
      }
      function startOfDay(d) { var x = new Date(d); x.setHours(0,0,0,0); return x; }
      function startOfWeek(d) {
        var x = startOfDay(d); var day = x.getDay();
        var diff = day === 0 ? -6 : 1 - day;
        x.setDate(x.getDate() + diff); return x;
      }

      function render() {
        var list = $('history-list');
        var now = new Date();
        var dayStart = startOfDay(now).getTime();
        var weekStart = startOfWeek(now).getTime();
        var filtered = calls.slice().sort(function (a, b) {
          var ta = asDate(a.startedAt), tb = asDate(b.startedAt);
          return (tb ? tb.getTime() : 0) - (ta ? ta.getTime() : 0);
        }).filter(function (c) {
          var t = asDate(c.startedAt); if (!t) return false;
          if (range === 'today') return t.getTime() >= dayStart;
          if (range === 'week') return t.getTime() >= weekStart;
          return true;
        });

        if (!filtered.length) {
          list.innerHTML = '<div class="py-20 text-center"><div class="w-14 h-14 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4"><svg class="w-6 h-6 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div><p class="text-[16px] font-medium text-gray-700">No calls in this range</p><p class="text-[13.5px] text-gray-400 mt-1">Call your Solana number to test it.</p></div>';
          return;
        }

        list.innerHTML = '';
        filtered.forEach(function (c) {
          var t = asDate(c.startedAt);
          var row = document.createElement('div');
          row.className = 'rounded-2xl border border-gray-100 bg-white p-5 hover:shadow-sm transition';
          row.innerHTML =
            '<div class="flex items-start gap-4">' +
              '<div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center flex-shrink-0"><svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg></div>' +
              '<div class="flex-1 min-w-0">' +
                '<div class="flex items-center gap-2 flex-wrap">' +
                  '<div class="font-semibold text-[15px] text-gray-900">' + (fmtPhone(c.from) || 'Unknown') + '</div>' +
                  '<div class="text-[12px] text-gray-400 ml-auto">' + (t ? t.toLocaleString() : '') + '</div>' +
                '</div>' +
                '<div class="text-[13px] text-gray-500 mt-1">Duration: ' + fmtDur(c.durationSec) + ' · Status: ' + ((c.status || 'completed').replace('_',' ')) + '</div>' +
              '</div>' +
            '</div>';
          list.appendChild(row);
        });
      }

      document.querySelectorAll('.hist-filter').forEach(function (b) {
        b.addEventListener('click', function () {
          document.querySelectorAll('.hist-filter').forEach(function (x) {
            var on = x === b;
            x.classList.toggle('bg-white', on); x.classList.toggle('shadow-sm', on);
            x.classList.toggle('text-gray-900', on); x.classList.toggle('font-semibold', on);
            x.classList.toggle('text-gray-500', !on); x.classList.toggle('font-medium', !on);
          });
          range = b.dataset.range;
          render();
        });
      });

      fb.onAuthStateChanged(fb.auth, function (u) {
        if (!u) return;
        uid = u.uid;
        fb.onSnapshot(fb.collection(fb.db, 'users', uid, 'calls'), function (s) {
          calls = [];
          s.forEach(function (d) { var x = d.data(); x.id = d.id; calls.push(x); });
          render();
        });
        var so = document.getElementById('signout-btn');
        if (so) so.addEventListener('click', function () {
          fb.signOut(fb.auth).then(function () { window.location.href = 'login.html'; });
        });
      });
    });
  </script>
'''

def page_history(_ctx):
    body = HISTORY_BODY_V2.replace("{sidebar}", _render_sidebar("history"))
    return "History", "Every call Solana has handled.", body, ""


# ---------------------------------------------------------------------------
# Dashboard page — assemble fresh
# ---------------------------------------------------------------------------

def page_dashboard(_ctx):
    sidebar = _render_sidebar("home")
    body = sidebar + DASH_HOME + DASH_NUMBER + DASH_FINANCES
    return "Dashboard", "Your Vocallus dashboard.", body, ""


# ---------------------------------------------------------------------------
# Custom render: dashboard + history get our new JS
# ---------------------------------------------------------------------------

_prev_rp_final = render_page

def render_page(path, builder):
    html = _prev_rp_final(path, builder)
    name = Path(path).name
    extra = ""
    if name == "dashboard.html": extra = DASH_JS
    elif name == "history.html": extra = HISTORY_JS_V2
    if extra and "</body>" in html:
        html = html.replace("</body>", extra + "\n</body>", 1)
    if BRIDGE_HELPER not in html:
        html = html.replace("</head>", BRIDGE_HELPER + "\n</head>", 1)
    return html


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

# --- end edit.py: real Firestore data ---
"""


def patch_build_py() -> None:
    src = BUILD_PY.read_text(encoding="utf-8")

    if MARKER in src:
        print("  [skip] override already present")
        return

    if MAIN_GUARD not in src:
        print("  [warn] main guard not found")
        sys.exit(1)

    src = src.replace(MAIN_GUARD, OVERRIDE + "\n\n" + MAIN_GUARD, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("  [ok]   appended real Firestore override")


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