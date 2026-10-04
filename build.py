#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — static site generator for Vocallus.

Run from the project root:

    python build.py

Produces:

    index.html
    Pages/products.html
    Pages/solutions.html
    Pages/pricing.html
    Pages/resources.html
    Pages/login.html
    Pages/signup.html
    Pages/talk-to-sales.html
    Pages/dashboard.html       <- sidebar layout, simulated data

Images (auto-managed in Images/):
    solana.png     — hero image (downloaded once from the original CDN URL)
    logo.png       — brand mark (generated with Pillow if missing)
    favicon.png    — same mark, used as the tab icon
    gicon.png      — Google "G" icon for the signup form (downloaded once)

Everything is idempotent — cached images stay cached, and re-running
overwrites the HTML cleanly.
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path
from string import Template

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
PAGES_DIR = ROOT / "Pages"
IMAGES_DIR = ROOT / "Images"

SITE_NAME = "Vocallus"
AGENT_NAME = "Solana"

HERO_IMAGE = "solana.png"
HERO_URL = (
    "https://cdn.prod.website-files.com/6899ec2c2b29c1edf8c20f15/"
    "69d7d901954c2651717221cc_image7.png"
)

GOOGLE_ICON = "gicon.png"
GOOGLE_URL = (
    "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c1/"
    "Google_%22G%22_logo.svg/3840px-Google_%22G%22_logo.svg.png"
)

LOGO_IMAGE = "logo.png"
FAVICON_IMAGE = "favicon.png"

BRAND_TOP = (17, 17, 17)     # #111111
BRAND_BOT = (38, 38, 38)     # #262626


# ---------------------------------------------------------------------------
# Image management
# ---------------------------------------------------------------------------


def _download(url: str, dest: Path) -> bool:
    """Download url -> dest, return True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"    [warn] download failed for {dest.name}: {exc}")
        dest.unlink(missing_ok=True)
        return False


def _make_mark(size: int):
    """Draw the Vocallus mark: white V on a black rounded square."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    steps = max(size - 1, 1)
    for y in range(size):
        t = y / steps
        color = tuple(
            int(BRAND_TOP[i] + (BRAND_BOT[i] - BRAND_TOP[i]) * t) for i in range(3)
        ) + (255,)
        gd.line([(0, y), (size, y)], fill=color)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
    )
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    stroke = max(int(size * 0.115), 2)
    pts = [
        (int(size * 0.30), int(size * 0.30)),
        (int(size * 0.50), int(size * 0.70)),
        (int(size * 0.70), int(size * 0.30)),
    ]
    d.line(pts, fill=(255, 255, 255, 255), width=stroke, joint="curve")
    cap = stroke / 2.0
    for p in (pts[0], pts[-1]):
        d.ellipse(
            [p[0] - cap, p[1] - cap, p[0] + cap, p[1] + cap],
            fill=(255, 255, 255, 255),
        )
    return img


def ensure_images() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # --- solana.png (hero) -------------------------------------------------
    hero = IMAGES_DIR / HERO_IMAGE
    if hero.exists() and hero.stat().st_size > 0:
        print(f"  [ok]   Images/{HERO_IMAGE} (cached)")
    elif _download(HERO_URL, hero):
        print(f"  [get]  Images/{HERO_IMAGE}")

    # --- gicon.png (Google) ------------------------------------------------
    gicon = IMAGES_DIR / GOOGLE_ICON
    if gicon.exists() and gicon.stat().st_size > 0:
        print(f"  [ok]   Images/{GOOGLE_ICON} (cached)")
    else:
        try:
            from PIL import Image
            req = urllib.request.Request(
                GOOGLE_URL, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            img = Image.open(io.BytesIO(raw))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(gicon, "PNG", optimize=True)
            print(f"  [get]  Images/{GOOGLE_ICON}")
        except ImportError:
            print("  [warn] Pillow missing; skipping gicon.png generation")
        except Exception as exc:
            print(f"  [warn] could not fetch gicon.png: {exc}")

    # --- logo.png + favicon.png -------------------------------------------
    need_logo = not (IMAGES_DIR / LOGO_IMAGE).exists()
    need_fav = not (IMAGES_DIR / FAVICON_IMAGE).exists()
    if need_logo or need_fav:
        try:
            mark = _make_mark(512)
            if need_logo:
                mark.save(IMAGES_DIR / LOGO_IMAGE, "PNG", optimize=True)
                print(f"  [new]  Images/{LOGO_IMAGE}")
            if need_fav:
                mark.save(IMAGES_DIR / FAVICON_IMAGE, "PNG", optimize=True)
                print(f"  [new]  Images/{FAVICON_IMAGE}")
        except ImportError:
            print("  [warn] Pillow missing; skipping logo/favicon generation")
    else:
        print(f"  [ok]   Images/{LOGO_IMAGE} (cached)")
        print(f"  [ok]   Images/{FAVICON_IMAGE} (cached)")


# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------

SHARED_CSS = """
    /* --- Fonts --------------------------------------------------------- */
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont,
                   "Segoe UI", Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    .font-inter { font-family: 'Inter', sans-serif; }

    /* --- Selection ----------------------------------------------------- */
    ::selection { background-color: #D4D4D4; color: #111111; }

    /* --- Primary button ------------------------------------------------ */
    .btn-primary {
      background-color: #111111;
      color: #FFFFFF;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .btn-primary:hover {
      background-color: #262626;
      transform: translateY(-1px);
    }
    .btn-primary:active { transform: translateY(0); }

    /* --- Nav dropdowns ------------------------------------------------- */
    .nav-trigger {
      background: transparent; border: 0; cursor: pointer;
      font: inherit;
    }
    .nav-dropdown { position: relative; }
    .nav-menu {
      position: absolute; top: 100%; left: 0;
      padding-top: 10px; min-width: 236px;
      opacity: 0; visibility: hidden;
      transform: translateY(-6px);
      transition: opacity .18s ease, transform .18s ease, visibility .18s;
      z-index: 40;
    }
    .nav-dropdown:hover .nav-menu,
    .nav-dropdown.is-open .nav-menu {
      opacity: 1; visibility: visible; transform: translateY(0);
    }
    .nav-dropdown:hover .nav-chevron,
    .nav-dropdown.is-open .nav-chevron { transform: rotate(180deg); }
    .nav-menu-inner { overflow: hidden; }

    /* --- Hash-active dropdown child ----------------------------------- */
    .nav-menu a.nav-hash-active {
      background-color: #111111 !important;
      color: #ffffff !important;
    }

    /* --- Page transitions --------------------------------------------- */
    /* Smooth fade only — no curve, no slide. */
    @keyframes pageFadeIn {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    main, .page-body {
      animation: pageFadeIn .28s ease-out both;
    }
    body.is-leaving { opacity: 0; transition: opacity .16s ease; }
    @media (prefers-reduced-motion: reduce) {
      main, .page-body { animation: none; }
      body.is-leaving { opacity: 1; transition: none; }
    }

    /* --- Hero fit ------------------------------------------------------ */
    .hero-fit { min-height: calc(100vh - 5rem); display: flex; align-items: center; }
    @media (max-width: 1023px) {
      .hero-fit { min-height: auto; padding-top: 2rem; padding-bottom: 2rem; }
    }

    /* --- Smooth scroll ------------------------------------------------- */
    html { scroll-behavior: smooth; }

    /* --- Dashboard ----------------------------------------------------- */
    .custom-scrollbar::-webkit-scrollbar { width: 8px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: #f1f1f1; }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #c1c1c1; border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
    .spark-bar { transition: height .3s cubic-bezier(0.16, 1, 0.3, 1); }

    @media (prefers-reduced-motion: reduce) {
      main, .page-body { animation: none; }
      body.is-leaving { opacity: 1; transition: none; }
      html { scroll-behavior: auto; }
    }
"""


# ---------------------------------------------------------------------------
# Shared JS — dropdowns, transitions, hash highlight
# ---------------------------------------------------------------------------

SHARED_JS = """
  <script>
    (function () {
      /* -------- Dropdown menus -------- */
      var dropdowns = document.querySelectorAll('[data-dropdown]');

      function setOpen(dd, open) {
        dd.classList.toggle('is-open', open);
        var t = dd.querySelector('.nav-trigger');
        if (t) t.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
      function closeAll(except) {
        dropdowns.forEach(function (dd) { if (dd !== except) setOpen(dd, false); });
      }

      dropdowns.forEach(function (dd) {
        var trigger = dd.querySelector('.nav-trigger');
        if (!trigger) return;
        trigger.addEventListener('click', function (e) {
          e.preventDefault(); e.stopPropagation();
          var willOpen = !dd.classList.contains('is-open');
          closeAll(dd);
          setOpen(dd, willOpen);
        });
      });

      document.addEventListener('click', function (e) {
        if (!e.target.closest('[data-dropdown]')) closeAll(null);
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeAll(null);
      });

      /* -------- Hash highlight in dropdowns -------- */
      function updateHashHighlight() {
        var hash = window.location.hash;
        document.querySelectorAll('.nav-menu a').forEach(function (a) {
          var href = a.getAttribute('href') || '';
          var idx = href.indexOf('#');
          var linkHash = idx >= 0 ? href.substring(idx) : '';
          a.classList.toggle('nav-hash-active', !!hash && linkHash === hash);
        });
      }
      window.addEventListener('hashchange', updateHashHighlight);
      window.addEventListener('load', updateHashHighlight);

      /* -------- Smooth page transitions -------- */
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduce) return;

      document.addEventListener('click', function (e) {
        if (e.defaultPrevented) return;
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

        var link = e.target.closest('a[href]');
        if (!link) return;
        var href = link.getAttribute('href');
        if (!href || href.charAt(0) === '#') return;
        if (/^(https?:|mailto:|tel:)/i.test(href)) return;
        if (link.target && link.target !== '_self') return;
        if (link.hasAttribute('download')) return;

        // Same-page navigation: let the browser handle it directly.
        try {
          var target = new URL(link.href, window.location.href);
          if (target.pathname === window.location.pathname) return;
        } catch (err) { /* fall through */ }

        e.preventDefault();
        document.body.classList.add('is-leaving');
        window.setTimeout(function () { window.location.href = href; }, 180);
        window.setTimeout(function () {
          document.body.classList.remove('is-leaving');
        }, 3000);
      });

      

      /* -------- Demo auth --------
         Sign in  ->  any email + password "123456"      -> account "demo"
         Sign up  ->  type "i" in all three fields       -> account "demo"
         Legacy   ->  full name "rat"                    -> account "rat" */

      /* -------- Lucide (if loaded) -------- */
      if (window.lucide && lucide.createIcons) lucide.createIcons();
    })();
  </script>
"""


# ---------------------------------------------------------------------------
# Head template
# ---------------------------------------------------------------------------

HEAD = Template("""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <meta name="description" content="${description}">
  <link rel="icon" type="image/png" href="${favicon}">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/lucide/0.260.0/lucide.min.js"></script>

  <style>${css}</style>
</head>""")


# ---------------------------------------------------------------------------
# Marketing shell
# ---------------------------------------------------------------------------

MARKETING_SHELL = Template("""<!DOCTYPE html>
<html lang="en">
${head}
<body class="bg-white text-neutral-900 min-h-screen flex flex-col justify-between">

${header}

  <main class="flex-1 ${main_class}">
${content}
  </main>

${footer}

${scripts}

</body>
</html>""")


# ---------------------------------------------------------------------------
# Dashboard shell
# ---------------------------------------------------------------------------

DASHBOARD_SHELL = Template("""<!DOCTYPE html>
<html lang="en">
${head}
<body class="font-inter flex h-screen overflow-hidden text-gray-800 bg-[#f2f2f2]">

${content}

${scripts}
</body>
</html>""")


# ---------------------------------------------------------------------------
# Link context
# ---------------------------------------------------------------------------


class Ctx:
    """Resolves site-relative paths for the current page depth."""

    def __init__(self, depth: int) -> None:
        self.depth = depth

    def u(self, target: str) -> str:
        if target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
            return target
        return ("../" * self.depth) + target

    def img(self, filename: str) -> str:
        return self.u(f"Images/{filename}")


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

NAV_ITEMS = [
    {
        "label": "Products",
        "href": "Pages/products.html",
        "children": [
            ("Overview", "Pages/products.html"),
            ("Call answering", "Pages/products.html#answering"),
            ("Message capture", "Pages/products.html#messages"),
            ("Call summaries", "Pages/products.html#summaries"),
        ],
    },
    {
        "label": "Solutions",
        "href": "Pages/solutions.html",
        "children": [
            ("Healthcare & dental", "Pages/solutions.html#healthcare"),
            ("Home services", "Pages/solutions.html#home-services"),
            ("Legal & professional", "Pages/solutions.html#legal"),
            ("Salons & spas", "Pages/solutions.html#salons"),
            ("Property management", "Pages/solutions.html#property"),
        ],
    },
    {"label": "Pricing", "href": "Pages/pricing.html", "children": []},
]

CHEVRON = (
    '<svg class="nav-chevron w-3.5 h-3.5 text-neutral-400 stroke-[2.5] '
    'transition-transform duration-200" fill="none" stroke="currentColor" '
    'viewBox="0 0 24 24" aria-hidden="true">'
    '<path stroke-linecap="round" stroke-linejoin="round" '
    'd="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>'
)


def _is_active(current_page: str, href: str) -> bool:
    if not current_page or "#" in href:
        return False
    href = href.split("#", 1)[0]
    if not href:
        return False
    return Path(current_page).name == Path(href).name


def render_header(ctx: Ctx, current_page: str = "") -> str:
    parts = []
    for item in NAV_ITEMS:
        label, href, children = item["label"], item["href"], item.get("children") or []
        url = ctx.u(href)
        active = _is_active(current_page, href)
        trigger_state = (
            "bg-[#111111] text-white"
            if active
            else "text-[#111111] hover:bg-neutral-50 hover:text-neutral-600"
        )

        if not children:
            parts.append(
                f'          <a href="{url}" '
                f'class="rounded-lg px-3 py-2 transition-colors {trigger_state}">'
                f"{label}</a>"
            )
            continue

        child_lines = []
        for child_label, child_href in children:
            child_state = (
                "bg-[#111111] text-white"
                if _is_active(current_page, child_href)
                else "text-neutral-700 hover:bg-neutral-50 hover:text-[#111111]"
            )
            child_lines.append(
                f'              <a href="{ctx.u(child_href)}" '
                f'class="block rounded-lg px-3.5 py-2 text-[14.5px] font-medium '
                f'transition-colors {child_state}">{child_label}</a>'
            )

        parts.append(
            '          <div class="nav-dropdown relative" data-dropdown>\n'
            '            <button type="button" aria-haspopup="true" '
            'aria-expanded="false" class="nav-trigger inline-flex items-center '
            f'gap-1.5 rounded-lg px-3 py-2 transition-colors {trigger_state}">\n'
            f"              <span>{label}</span>\n"
            f"              {CHEVRON}\n"
            "            </button>\n"
            '            <div class="nav-menu" role="menu">\n'
            '              <div class="nav-menu-inner rounded-2xl border '
            'border-neutral-100 bg-white p-2 shadow-lg shadow-neutral-200/60">\n'
            + "\n".join(child_lines) + "\n"
            "              </div>\n"
            "            </div>\n"
            "          </div>"
        )

    return f"""  <header class="w-full bg-white/95 backdrop-blur-md sticky top-0 z-30 border-b border-neutral-100">
    <div class="max-w-[1400px] mx-auto px-6 lg:px-12 h-20 flex items-center justify-between">

      <div class="flex items-center gap-10">
        <a href="{ctx.u('index.html')}" class="flex items-center gap-2.5 select-none hover:opacity-90 transition">
          <img src="{ctx.img(LOGO_IMAGE)}" alt="" class="h-9 w-9" />
          <span class="font-extrabold text-2xl tracking-tighter text-black">{SITE_NAME}</span>
        </a>

        <nav class="hidden md:flex items-center gap-1 text-[15px] font-medium text-[#111111]">
{chr(10).join(parts)}
        </nav>
      </div>

      <div class="flex items-center gap-3 sm:gap-4 text-[15px] font-medium">
        <a href="{ctx.u('Pages/login.html')}" class="px-2 py-1.5 text-neutral-700 hover:text-black transition">
          Sign in
        </a>
        <a href="{ctx.u('Pages/talk-to-sales.html')}" class="hidden sm:inline-flex items-center justify-center px-4 py-2 border border-neutral-200/90 rounded-xl text-neutral-800 font-medium hover:bg-neutral-50 transition shadow-xs">
          Talk to Sales
        </a>
        <a href="{ctx.u('Pages/signup.html')}" class="btn-primary inline-flex items-center justify-center px-5 py-2 rounded-xl font-semibold shadow-sm">
          Try for free
        </a>
      </div>

    </div>
  </header>"""


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------


def render_footer(ctx: Ctx) -> str:
    def link(label, href):
        return (
            f'<li><a href="{ctx.u(href)}" class="text-[14.5px] text-neutral-500 '
            f'hover:text-[#111111] transition-colors">{label}</a></li>'
        )

    product_links = "\n              ".join([
        link("Products", "Pages/products.html"),
        link("Solutions", "Pages/solutions.html"),
        link("Pricing", "Pages/pricing.html"),
        link("Resources", "Pages/resources.html"),
    ])
    company_links = "\n              ".join([
        link("Dashboard", "Pages/dashboard.html"),
        link("Talk to Sales", "Pages/talk-to-sales.html"),
        link("Sign up", "Pages/signup.html"),
        link("Sign in", "Pages/login.html"),
    ])

    return f"""  <footer class="border-t border-neutral-100 bg-white">
    <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-16">
      <div class="grid grid-cols-1 md:grid-cols-12 gap-10">

        <div class="md:col-span-5">
          <a href="{ctx.u('index.html')}" class="flex items-center gap-2.5 select-none">
            <img src="{ctx.img(LOGO_IMAGE)}" alt="" class="h-8 w-8" />
            <span class="font-extrabold text-xl tracking-tighter text-black">{SITE_NAME}</span>
          </a>
          <p class="mt-4 text-[14.5px] leading-[1.65] text-neutral-500 max-w-[340px]">
            Answer every call, 24/7, with {AGENT_NAME} — the AI receptionist built
            directly into your business phone system.
          </p>
        </div>

        <div class="md:col-span-3">
          <p class="text-[12.5px] font-semibold uppercase tracking-[0.08em] text-neutral-400">Product</p>
          <ul class="mt-5 space-y-3.5">
              {product_links}
          </ul>
        </div>

        <div class="md:col-span-2">
          <p class="text-[12.5px] font-semibold uppercase tracking-[0.08em] text-neutral-400">Company</p>
          <ul class="mt-5 space-y-3.5">
              {company_links}
          </ul>
        </div>

        <div class="md:col-span-2">
          <p class="text-[12.5px] font-semibold uppercase tracking-[0.08em] text-neutral-400">Contact</p>
          <ul class="mt-5 space-y-3.5">
            <li><a href="mailto:hello@vocallus.example" class="text-[14.5px] text-neutral-500 hover:text-[#111111] transition-colors">hello@vocallus.example</a></li>
            <li><a href="tel:+15550000000" class="text-[14.5px] text-neutral-500 hover:text-[#111111] transition-colors">(555) 000-0000</a></li>
          </ul>
        </div>

      </div>

      <div class="mt-14 pt-6 border-t border-neutral-100 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p class="text-[13px] text-neutral-400">&copy; 2026 {SITE_NAME}. All rights reserved.</p>
        <div class="flex items-center gap-5 text-[13px] text-neutral-400">
          <a href="#" class="hover:text-[#111111] transition-colors">Privacy</a>
          <a href="#" class="hover:text-[#111111] transition-colors">Terms</a>
          <a href="#" class="hover:text-[#111111] transition-colors">Security</a>
        </div>
      </div>
    </div>
  </footer>"""


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------


def eyebrow(text, dark=False):
    if dark:
        return (
            '<span class="inline-flex items-center rounded-full bg-white border '
            'border-white px-3.5 py-1.5 text-[13px] font-semibold text-[#111111]">'
            f"{text}</span>"
        )
    return (
        '<span class="inline-flex self-start items-center rounded-full bg-[#111111] border '
        'border-[#111111] px-3.5 py-1.5 text-[13px] font-semibold text-white">'
        f"{text}</span>"
    )


def section_wrap(anchor, inner, bg="bg-white"):
    return f"""
    <section id="{anchor}" class="scroll-mt-24 {bg}">
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-20 lg:py-28">
        {inner}
      </div>
    </section>
"""


def bullet_list(items):
    return "\n".join(
        f'<li class="flex items-start gap-3">'
        f'<span class="mt-[9px] w-2 h-2 rounded-full bg-[#111111] shrink-0"></span>'
        f'<span class="text-[15.5px] leading-[1.6] text-[#55565B]">'
        f'<strong class="text-[#111111] font-semibold">{t}</strong> {d}</span></li>'
        for t, d in items
    )


def section_centered(anchor, eyebrow_text, heading, lead, cards=None, bg="bg-white"):
    cards_html = ""
    if cards:
        cells = "\n".join(
            f'<div class="rounded-3xl border border-neutral-100 bg-white p-8 '
            f'shadow-xs hover:shadow-md hover:-translate-y-0.5 transition">'
            f'<div class="w-12 h-12 rounded-2xl bg-[#111111] flex items-center '
            f'justify-center mb-6"><span class="text-white font-bold text-[15px]">'
            f"{i:02d}</span></div>"
            f'<h3 class="text-[19px] font-bold tracking-tight text-[#111111]">{t}</h3>'
            f'<p class="mt-3 text-[15.5px] leading-[1.6] text-[#55565B]">{d}</p></div>'
            for i, (t, d) in enumerate(cards, 1)
        )
        cards_html = f"""
        <div class="mt-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {cells}
        </div>"""

    inner = f"""
        <div class="max-w-[760px] mx-auto text-center">
          {eyebrow(eyebrow_text)}
          <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[44px] font-bold leading-[1.12] tracking-[-0.03em] text-[#111111]">{heading}</h2>
          <p class="mt-5 text-[17px] sm:text-[18px] leading-[1.6] text-[#55565B] max-w-[640px] mx-auto">{lead}</p>
        </div>{cards_html}"""
    return section_wrap(anchor, inner, bg)


def stat_visual(big, sublabel, tint="neutral"):
    bg = "bg-neutral-50 border-neutral-100" if tint == "neutral" else "bg-white border-neutral-100"
    return f"""<div class="rounded-3xl {bg} border p-10 lg:p-12 flex items-center justify-center min-h-[320px]">
              <div class="text-center">
                <div class="text-[80px] lg:text-[110px] font-extrabold leading-none tracking-[-0.05em] text-[#111111]">{big}</div>
                <p class="mt-3 text-[15px] font-semibold text-[#55565B] tracking-[-0.01em]">{sublabel}</p>
              </div>
            </div>"""


def card_visual(title, lines, tint="neutral"):
    bg = "bg-neutral-50 border-neutral-100" if tint == "neutral" else "bg-white border-neutral-100"
    rows = "\n".join(
        f'<div class="flex items-center justify-between rounded-xl bg-white px-4 py-3 border border-neutral-100">'
        f'<span class="text-[14px] font-medium text-[#55565B]">{k}</span>'
        f'<span class="text-[14px] font-semibold text-[#111111]">{v}</span></div>'
        for k, v in lines
    )
    return f"""<div class="rounded-3xl {bg} border p-7 lg:p-9">
              <p class="text-[13px] font-semibold uppercase tracking-[0.08em] text-[#111111] mb-4">{title}</p>
              <div class="space-y-2.5">{rows}</div>
            </div>"""


def section_split(anchor, eyebrow_text, heading, lead, items, visual, reverse=False, bg="bg-white"):
    order_copy = "lg:order-2" if reverse else ""
    order_vis = "lg:order-1" if reverse else ""
    inner = f"""
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div class="lg:col-span-6 {order_copy}">
            {eyebrow(eyebrow_text)}
            <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[42px] font-bold leading-[1.12] tracking-[-0.03em] text-[#111111]">{heading}</h2>
            <p class="mt-5 text-[17px] leading-[1.6] text-[#55565B]">{lead}</p>
            <ul class="mt-7 space-y-3.5">{bullet_list(items)}</ul>
          </div>
          <div class="lg:col-span-6 {order_vis}">{visual}</div>
        </div>"""
    return section_wrap(anchor, inner, bg)


def section_dark(anchor, eyebrow_text, heading, lead, items):
    bullets = "\n".join(
        f'<li class="flex items-start gap-3">'
        f'<span class="mt-[9px] w-2 h-2 rounded-full bg-white shrink-0"></span>'
        f'<span class="text-[15.5px] leading-[1.6] text-neutral-300">'
        f'<strong class="text-white font-semibold">{t}</strong> {d}</span></li>'
        for t, d in items
    )
    return f"""
    <section id="{anchor}" class="scroll-mt-24 bg-[#0A0A0A] text-white">
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-20 lg:py-28">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div class="lg:col-span-6">
            {eyebrow(eyebrow_text, dark=True)}
            <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[42px] font-bold leading-[1.12] tracking-[-0.03em] text-white">{heading}</h2>
            <p class="mt-5 text-[17px] leading-[1.6] text-neutral-400">{lead}</p>
          </div>
          <div class="lg:col-span-6"><ul class="space-y-3.5">{bullets}</ul></div>
        </div>
      </div>
    </section>
"""


def section_small_grid(anchor, eyebrow_text, heading, lead, items, bg="bg-neutral-50"):
    cells = "\n".join(
        f'<div class="rounded-2xl bg-white border border-neutral-100 p-6 shadow-xs hover:shadow-sm transition">'
        f'<h3 class="text-[16.5px] font-bold tracking-tight text-[#111111]">{t}</h3>'
        f'<p class="mt-2 text-[14.5px] leading-[1.6] text-[#55565B]">{d}</p></div>'
        for t, d in items
    )
    inner = f"""
        <div class="text-center max-w-[720px] mx-auto">
          {eyebrow(eyebrow_text)}
          <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[40px] font-bold leading-[1.14] tracking-[-0.03em] text-[#111111]">{heading}</h2>
          <p class="mt-4 text-[16.5px] leading-[1.6] text-[#55565B]">{lead}</p>
        </div>
        <div class="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">{cells}</div>"""
    return section_wrap(anchor, inner, bg)


def page_hero(heading, lead):
    return f"""
      <section class="bg-white">
        <div class="max-w-[1400px] mx-auto px-6 lg:px-12 pt-16 lg:pt-24 pb-10 lg:pb-14">
          <div class="max-w-[780px]">
            <h1 class="text-4xl sm:text-5xl lg:text-[52px] font-bold leading-[1.08] tracking-[-0.035em] text-[#111111]">{heading}</h1>
            <p class="mt-6 text-[17px] sm:text-[18px] leading-[1.58] text-[#55565B] max-w-[620px]">{lead}</p>
          </div>
        </div>
      </section>"""


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------


def form_field(label, name, type_="text", placeholder="", required=True,
               autocomplete="", textarea=False):
    req = " required" if required else ""
    ac = f' autocomplete="{autocomplete}"' if autocomplete else ""
    cls = (
        "w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 "
        "text-[15px] text-neutral-900 placeholder:text-neutral-400 outline-none "
        "transition focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100"
    )
    if textarea:
        control = f'<textarea name="{name}" rows="4" placeholder="{placeholder}"{req} class="{cls}"></textarea>'
    else:
        control = f'<input type="{type_}" name="{name}" placeholder="{placeholder}"{req}{ac} class="{cls}" />'
    return f"""              <label class="block">
                <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">{label}</span>
                {control}
              </label>"""


def form_page(ctx, eyebrow_text, heading, lead, fields, submit_label, footnote, google=False, google_label="Sign up with Google"):
    google_html = ""
    if google:
        google_html = (
            '                <button type="button" class="w-full inline-flex '
            'items-center justify-center gap-2.5 rounded-xl border border-neutral-200 '
            'bg-white px-6 py-3.5 font-bold text-[16px] tracking-[-0.01em] '
            'text-neutral-800 shadow-xs hover:bg-neutral-50 transition">\n'
            f'                  <img src="{ctx.img(GOOGLE_ICON)}" alt="" class="h-5 w-5 select-none" />\n'
            f"                  {google_label}\n"
            "                </button>\n"
            '                <div class="pt-1"></div>\n'
        )
    return f"""
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-16 lg:py-24 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div class="lg:col-span-6 flex flex-col justify-center">
            {eyebrow(eyebrow_text)}
            <h1 class="mt-5 text-4xl sm:text-5xl lg:text-[52px] font-bold leading-[1.08] tracking-[-0.035em] text-[#111111]">{heading}</h1>
            <p class="mt-6 text-[17px] sm:text-[18px] leading-[1.58] text-[#55565B] max-w-[520px]">{lead}</p>
          </div>

          <div class="lg:col-span-6 flex justify-center lg:justify-end">
            <div class="w-full max-w-[460px] rounded-3xl border border-neutral-100 bg-white p-8 sm:p-10 shadow-sm">
              <form class="space-y-5" action="#" method="post" data-demo-form novalidate>
{google_html}{chr(10).join(fields)}
                <button type="submit" class="btn-primary w-full inline-flex items-center justify-center px-6 py-3.5 rounded-xl font-bold text-[16px] tracking-[-0.01em] shadow-sm hover:shadow-md">
                  {submit_label}
                </button>
              </form>
              <p class="mt-6 text-center text-[13.5px] text-neutral-500">{footnote}</p>
            </div>
          </div>
        </div>
      </div>"""


# ---------------------------------------------------------------------------
# Pricing grid
# ---------------------------------------------------------------------------


def pricing_grid(ctx, plans):
    cards = []
    for plan in plans:
        highlight = plan.get("highlight", False)
        border = "border-neutral-300 ring-2 ring-neutral-100" if highlight else "border-neutral-100"
        badge = (
            '<span class="inline-flex items-center rounded-full bg-[#111111] '
            'border border-[#111111] px-3 py-1 text-[12px] font-semibold text-white">Most popular</span>'
            if highlight else ""
        )
        features = "\n".join(
            f'              <li class="flex items-start gap-2.5 text-[15px] text-[#55565B]">'
            f'<span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-[#111111] shrink-0"></span>{f}</li>'
            for f in plan["features"]
        )
        btn_class = (
            "btn-primary" if highlight
            else "border border-neutral-200/90 text-neutral-800 hover:bg-neutral-50"
        )
        cards.append(
            f"""          <div class="rounded-3xl border {border} bg-white p-8 shadow-xs flex flex-col">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">{plan['name']}</h3>
              {badge}
            </div>
            <p class="mt-2.5 text-[15.5px] leading-[1.6] text-[#55565B]">{plan['blurb']}</p>
            <div class="mt-6 flex items-end gap-1.5">
              <span class="text-[40px] font-extrabold leading-none tracking-[-0.04em] text-[#111111]">${plan['price']}</span>
              <span class="pb-1 text-[14px] font-medium text-neutral-500">/ month</span>
            </div>
            <ul class="mt-7 space-y-3 flex-1">
{features}
            </ul>
            <div class="mt-8">
              <a href="{ctx.u('Pages/signup.html')}" class="{btn_class} inline-flex w-full items-center justify-center px-6 py-3 rounded-xl font-bold text-[15.5px] tracking-[-0.01em] transition shadow-xs">
                {plan['cta']}
              </a>
            </div>
          </div>"""
        )
    return f"""
        <div class="mt-20 grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
{chr(10).join(cards)}
        </div>"""


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def page_index(ctx: Ctx):
    title = "Home"
    description = (
        f"Avoid missed calls with {AGENT_NAME}, {SITE_NAME}'s 24/7 AI virtual "
        f"receptionist — answering, capturing, booking, and texting callers."
    )
    hero = f"""
      <section class="hero-fit bg-white">
        <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-10 lg:py-16 w-full">
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
            <div class="lg:col-span-6 flex flex-col justify-center">
              <h1 class="text-4xl sm:text-5xl lg:text-[54px] xl:text-[58px] font-bold leading-[1.08] tracking-[-0.035em] text-[#111111]">
                Answer calls 24/7 with {AGENT_NAME}
              </h1>
              <p class="mt-6 text-[17px] sm:text-[18px] leading-[1.58] text-[#55565B] max-w-[560px]">
                Avoid missed calls and opportunities with {AGENT_NAME}, {SITE_NAME}'s 24/7 AI virtual receptionist. She answers calls, takes messages, books appointments, and texts callers &mdash; right inside your business phone system. No extra tools. No separate dashboard.
              </p>
              <p class="mt-6 text-[16px] sm:text-[17px] font-bold tracking-tight text-[#111111]">
                Try {SITE_NAME} free
              </p>
              <div class="mt-7 flex flex-wrap items-center gap-4">
                <a href="{ctx.u('Pages/signup.html')}" class="btn-primary inline-flex items-center justify-center px-7 py-3.5 rounded-xl font-bold text-[16px] tracking-[-0.01em] shadow-sm hover:shadow-md">
                  Get started today
                </a>
                <a href="{ctx.u('Pages/dashboard.html')}" class="inline-flex items-center justify-center px-7 py-3.5 rounded-xl font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 text-neutral-800 hover:bg-neutral-50 transition">
                  See the dashboard
                </a>
              </div>
            </div>
            <div class="lg:col-span-6 flex justify-center lg:justify-end">
              <div class="bg-neutral-50 w-full rounded-3xl p-6 sm:p-10 lg:p-12 flex items-center justify-center shadow-xs border border-neutral-100">
                <div class="w-full flex items-center justify-center">
                  <img src="{ctx.img(HERO_IMAGE)}" alt="{AGENT_NAME} call summary and scheduling card" class="w-full h-auto object-contain drop-shadow-sm select-none rounded-xl" loading="eager" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>"""

    strip = f"""
      <section class="bg-neutral-50">
        <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-20 lg:py-24">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <a href="{ctx.u('Pages/products.html')}" class="group rounded-3xl bg-white border border-neutral-100 p-8 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Products</h3>
              <p class="mt-3 text-[15.5px] leading-[1.6] text-[#55565B]">See how {AGENT_NAME} answers, captures, and summarizes every call.</p>
              <span class="mt-6 inline-flex items-center gap-1.5 text-[14px] font-semibold text-[#111111] group-hover:gap-2.5 transition-all">Explore &rarr;</span>
            </a>
            <a href="{ctx.u('Pages/solutions.html')}" class="group rounded-3xl bg-white border border-neutral-100 p-8 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Solutions</h3>
              <p class="mt-3 text-[15.5px] leading-[1.6] text-[#55565B]">Built for clinics, home services, legal, salons, and property teams.</p>
              <span class="mt-6 inline-flex items-center gap-1.5 text-[14px] font-semibold text-[#111111] group-hover:gap-2.5 transition-all">Explore &rarr;</span>
            </a>
            <a href="{ctx.u('Pages/pricing.html')}" class="group rounded-3xl bg-white border border-neutral-100 p-8 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Pricing</h3>
              <p class="mt-3 text-[15.5px] leading-[1.6] text-[#55565B]">Simple plans that scale with your call volume. Free demo included.</p>
              <span class="mt-6 inline-flex items-center gap-1.5 text-[14px] font-semibold text-[#111111] group-hover:gap-2.5 transition-all">Explore &rarr;</span>
            </a>
          </div>
        </div>
      </section>"""

    return title, description, hero + strip, ""


def page_products(ctx: Ctx):
    title = "Products"
    description = (
        f"{AGENT_NAME} answers every call, takes detailed messages, and writes "
        f"clean summaries — right inside your {SITE_NAME} inbox."
    )
    body = (
        page_hero(
            f"Meet {AGENT_NAME}, the AI receptionist that never misses a call",
            f"{AGENT_NAME} is a 24/7 AI virtual receptionist built directly into your business phone system. She answers, qualifies, books, and follows up — so your team can stay focused on the work in front of them.",
        )
        + section_split(
            "answering", "Call answering",
            "Every call answered on the first ring",
            f"{AGENT_NAME} picks up instantly — no hold music, no phone tree, no voicemail. Callers reach a friendly voice that already knows your business.",
            [
                ("Under 1 second pickup", "no ringing, no waiting, no hang-ups."),
                ("24 hours a day", "including nights, weekends, and holidays."),
                ("Natural conversation", "callers can interrupt, ask questions, and change their mind."),
                ("Instant handoff", "warm transfers to your team when it matters."),
            ],
            visual=stat_visual("24/7", "Always on, always answering"),
        )
        + section_split(
            "messages", "Message capture",
            "Detailed messages, delivered to your inbox",
            f"When a caller needs a human, {AGENT_NAME} captures everything your team needs to follow up — without the caller repeating themselves.",
            [
                ("Name and number", "verified and formatted correctly every time."),
                ("Reason for calling", "summarized in a sentence or two."),
                ("Urgency signals", "flags the calls that need attention first."),
                ("Instant notification", "lands in your inbox before the caller hangs up."),
            ],
            visual=card_visual("Latest message", [
                ("Caller", "Maya R."), ("Reason", "Reschedule Thursday"),
                ("Urgency", "Normal"), ("Status", "In inbox"),
            ]),
            reverse=True, bg="bg-neutral-50",
        )
        + section_dark(
            "summaries", "Call summaries",
            "Every conversation, summarized in seconds",
            f"After each call, {AGENT_NAME} writes a clean summary you can scan in a glance. No more listening back through recordings to find the one detail you needed.",
            [
                ("One-line recap", "the gist of every call, at the top of the thread."),
                ("Action items", "what needs to happen next, who owns it, and when."),
                ("Full transcript", "searchable, timestamped, and always available."),
                ("Sentiment tags", "spot frustrated callers before they escalate."),
            ],
        )
    )
    return title, description, body, ""


def page_solutions(ctx: Ctx):
    title = "Solutions"
    description = (
        f"{AGENT_NAME} is built for clinics, home services, legal, salons, and "
        f"property teams — answering, qualifying, and routing every call."
    )
    body = (
        page_hero(
            "Built for the way your team already works",
            f"Whatever your call volume looks like, {AGENT_NAME} picks up instantly, follows your script, and hands off cleanly. No new phone system, no new habits.",
        )
        + section_small_grid(
            "healthcare", "Healthcare & dental",
            "Never miss a patient call again",
            "After-hours triage, appointment requests, and prescription questions — handled without adding front-desk headcount.",
            [
                ("After-hours triage", "route urgent calls to the on-call line instantly."),
                ("Appointment requests", "captured with patient name, DOB, and reason."),
                ("Prescription refills", "logged and forwarded to the right staff member."),
                ("Insurance questions", "answered with your custom FAQ script."),
            ],
        )
        + section_split(
            "home-services", "Home services",
            "Capture every job while your crews are on site",
            f"Your techs can't answer the phone with their hands full. {AGENT_NAME} picks up, qualifies the job, and gets the details into your dispatch queue.",
            [
                ("Job qualification", "service type, address, and urgency captured up front."),
                ("Instant dispatch", "high-priority calls trigger a text to the on-call tech."),
                ("Quote scheduling", "callers can book an estimate slot right on the call."),
                ("Follow-up texts", "confirms the appointment and directions automatically."),
            ],
            visual=stat_visual("< 1s", "Time to first ring"),
            reverse=True,
        )
        + section_dark(
            "legal", "Legal & professional",
            "Confidential intake, handled with care",
            "New client calls are qualified with your intake questions, then routed to the right attorney — without a receptionist reading from a script.",
            [
                ("Practice-area screening", "only qualified matters reach your team."),
                ("Conflict checks", "flags existing client names automatically."),
                ("Consultation booking", "puts qualified leads straight on the calendar."),
                ("Confidential transcripts", "encrypted and stored in your inbox only."),
            ],
        )
        + section_small_grid(
            "salons", "Salons & spas",
            "A full calendar, without lifting a finger",
            f"{AGENT_NAME} books appointments, handles reschedules, and confirms every visit by text — so no-shows drop and your chairs stay full.",
            [
                ("Instant booking", "callers grab an open slot during the call."),
                ("Reschedule & cancel", "handled automatically with policy reminders."),
                ("Text confirmations", "sent the day before to cut down on no-shows."),
                ("Stylist preferences", "captured so regulars get their usual."),
            ],
        )
        + section_split(
            "property", "Property management",
            "Every tenant request, logged and routed",
            f"Maintenance calls at 2 a.m. don't have to wake anyone up. {AGENT_NAME} captures the details, tags the urgency, and routes it to the right person.",
            [
                ("Maintenance triage", "emergency vs. routine, decided automatically."),
                ("Unit and tenant ID", "verified against your directory on the call."),
                ("After-hours routing", "true emergencies reach the on-call line."),
                ("Vendor dispatch", "routine requests queue up for the morning."),
            ],
            visual=card_visual("After hours", [
                ("Caller", "Unit 4B"), ("Issue", "Water heater"),
                ("Urgency", "Emergency"), ("Routed to", "On-call tech"),
            ]),
            reverse=True, bg="bg-neutral-50",
        )
    )
    return title, description, body, ""


def page_pricing(ctx: Ctx):
    title = "Pricing"
    description = (
        "Simple, predictable pricing for a 24/7 AI receptionist. Start with "
        "a free demo, cancel anytime."
    )
    inner = f"""
        <div class="text-center max-w-[720px] mx-auto">
          {eyebrow("Pricing")}
          <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[44px] font-bold leading-[1.12] tracking-[-0.03em] text-[#111111]">Simple pricing that scales with your call volume</h2>
          <p class="mt-5 text-[17px] leading-[1.6] text-[#55565B]">Every plan includes a free demo, unlimited users, and no setup fees. Upgrade, downgrade, or cancel whenever you like.</p>
        </div>
        """ + pricing_grid(ctx, [
        {"name": "Starter", "blurb": "For solo operators and single-line businesses.",
         "price": "49", "cta": "Try for free",
         "features": ["Up to 100 answered calls / month", "24/7 call answering",
                      "Message capture & email delivery", "Custom greeting"]},
        {"name": "Growth", "blurb": "For teams that book appointments all day long.",
         "price": "129", "cta": "Try for free", "highlight": True,
         "features": ["Up to 500 answered calls / month", "Everything in Starter",
                      "Calendar booking & rescheduling", "Two-way SMS follow-ups",
                      "Call summaries in your inbox"]},
        {"name": "Scale", "blurb": "For multi-location and high-volume operations.",
         "price": "299", "cta": "Talk to Sales",
         "features": ["Unlimited answered calls", "Everything in Growth",
                      "Multi-location routing", "CRM & helpdesk integrations",
                      "Dedicated onboarding"]},
    ])
    body = section_wrap("pricing", inner)
    return title, description, body, ""


def page_resources(ctx: Ctx):
    title = "Resources"
    description = (
        "Guides, playbooks, and customer stories to help you stop missing "
        "calls and start booking more of them."
    )
    body = (
        page_hero(
            "Guides, playbooks, and customer stories",
            "Practical reads for owners and operators who want every call answered and every opportunity captured.",
        )
        + section_centered(
            "articles", "Latest",
            "Everything you need to get more out of every call",
            "Short, actionable reads — no fluff, no 40-minute webinars.",
            [
                ("The missed-call math", "How much revenue a single unanswered ring actually costs a small business."),
                ("Writing a great AI greeting", "A five-part script template that sounds human and books more appointments."),
                ("After-hours playbook", "What to capture, what to escalate, and what to save for the morning."),
                ("Northside Dental", "From 30% missed calls to a full calendar in six weeks."),
                ("Ridgeline HVAC", "How one dispatcher now covers three service areas."),
                ("Changelog", "Every improvement shipped to the agent, in plain English."),
            ],
        )
    )
    return title, description, body, ""


def page_login(ctx: Ctx):
    title = "Sign in"
    description = f"Sign in to your {SITE_NAME} inbox."
    content = form_page(
        ctx,
        "Welcome back",
        f"Sign in to your {SITE_NAME} inbox",
        "Pick up right where you left off — every call, message, and booking in one place.",
        [
            form_field("Email", "email", "email", "you@company.com", autocomplete="email"),
            form_field("Password", "password", "password", "••••••••", autocomplete="current-password"),
        ],
        "Sign in",
        f'New to {SITE_NAME}? <a href="{ctx.u("Pages/signup.html")}" class="font-semibold text-[#111111] hover:underline">Try for free</a>',
        google=True,
        google_label="Sign in with Google",
    )
    return title, description, content, ""


def page_signup(ctx: Ctx):
    title = "Sign up"
    description = f"Try {SITE_NAME} free."
    content = form_page(
        ctx,
        "Free demo",
        f"Try {SITE_NAME} free",
        f"Set up {AGENT_NAME} in minutes. Everything stays inside your existing phone system.",
        [
            form_field("Full name", "name", "text", "Jordan Rivera", autocomplete="name"),
            form_field("Email", "email", "email", "you@company.com", autocomplete="email"),
            form_field("Company", "company", "text", "Acme Services", autocomplete="organization"),
        ],
        "Create my account",
        f'Already have an account? <a href="{ctx.u("Pages/login.html")}" class="font-semibold text-[#111111] hover:underline">Sign in</a>',
        google=True,
    )
    return title, description, content, ""


def page_talk_to_sales(ctx: Ctx):
    title = "Talk to Sales"
    description = "Tell us about your call volume and we'll show you the right plan."
    content = form_page(
        ctx,
        "Talk to Sales",
        "Let's find the right plan for your call volume",
        "Tell us a little about your business and we'll get back to you within one business day.",
        [
            form_field("Full name", "name", "text", "Jordan Rivera", autocomplete="name"),
            form_field("Work email", "email", "email", "you@company.com", autocomplete="email"),
            form_field("Company", "company", "text", "Acme Services", autocomplete="organization"),
            form_field("Monthly call volume", "volume", "text", "e.g. 400 calls / month", required=False),
            form_field("What are you trying to solve?", "message", placeholder="We miss about a third of our calls after 5pm…", required=False, textarea=True),
        ],
        "Request a demo",
        "Prefer email? Reach us at sales@vocallus.example",
    )
    return title, description, content, ""


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

DASHBOARD_BODY = r"""
    <!-- Sidebar -->
    <nav class="w-[88px] bg-[#f2f2f2] border-r border-gray-200 flex flex-col justify-between items-center py-6 flex-shrink-0 z-10">
        <div class="flex flex-col items-center w-full space-y-4">
            <a href="../index.html" class="mb-2 select-none">
                <img src="../Images/logo.png" alt="Vocallus" class="w-9 h-9 rounded-xl" />
            </a>

            <div class="flex flex-col w-full items-center space-y-2">
                <a href="dashboard.html" data-panel="home" class="dash-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl bg-gray-200/80 text-gray-900 transition-colors">
                    <div class="dash-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full opacity-100 transition-opacity"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5L12 3l9 7.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                    <span class="text-[11px] font-semibold tracking-tight">Home</span>
                </a>

                <a href="solana.html" class="flex flex-col items-center justify-center w-full py-2.5 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Solana</span>
                </a>

                <a href="dashboard.html#number" data-panel="number" class="dash-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">
                    <div class="dash-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full opacity-0 transition-opacity"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.05 5A5 5 0 0 1 19 8.95"></path><path d="M15.05 1A9 9 0 0 1 23 8.94"></path><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Number</span>
                </a>

                <a href="history.html" class="flex flex-col items-center justify-center w-full py-2.5 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span class="text-[11px] font-medium tracking-tight">History</span>
                </a>

                <a href="dashboard.html#finances" data-panel="finances" class="dash-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">
                    <div class="dash-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full opacity-0 transition-opacity"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Finances</span>
                </a>
            </div>
        </div>

        <div class="flex flex-col w-full items-center space-y-4">
            <a href="#" class="text-gray-500 hover:text-gray-800 relative p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ff5a00] rounded-full border-2 border-[#f2f2f2]"></span>
            </a>
            <button id="signout-btn" title="Sign out" class="text-gray-500 hover:text-gray-800 p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
        </div>
    </nav>

    <!-- Main -->
    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl shadow-[-5px_0_15px_-3px_rgba(0,0,0,0.1)]">
        <div id="panel-home" class="panel max-w-[1200px] mx-auto px-8 py-8">

            <!-- Welcome Banner -->
            <div class="bg-white rounded-3xl shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-gray-100 p-8 mb-8 flex justify-between items-center relative overflow-hidden h-[180px]">
                <div class="z-10 mt-[-20px]">
                    <p id="today-date" class="text-gray-800 text-[22px] mb-2 font-medium">—</p>
                    <h1 class="text-[32px] font-semibold text-gray-900">Good Morning, <span id="user-name">Taymoor A.</span></h1>
                    <p class="text-gray-500 text-[15px] mt-2">Solana handled <span class="font-semibold text-gray-900" id="banner-calls">14</span> calls for you overnight.</p>
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

            <!-- Stat Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                        </div>
                        <span class="text-[12px] font-semibold text-green-700 bg-green-100 px-2 py-1 rounded-full">+18%</span>
                    </div>
                    <div class="text-[13px] text-gray-500 font-medium">Calls answered</div>
                    <div class="text-[28px] font-semibold text-gray-900 mt-1" data-stat="answered">0</div>
                    <div class="text-[12px] text-gray-400 mt-1">Today</div>
                </div>
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                        </div>
                        <span class="text-[12px] font-semibold text-gray-600 bg-gray-200 px-2 py-1 rounded-full">0 missed</span>
                    </div>
                    <div class="text-[13px] text-gray-500 font-medium">Messages captured</div>
                    <div class="text-[28px] font-semibold text-gray-900 mt-1" data-stat="messages">0</div>
                    <div class="text-[12px] text-gray-400 mt-1">Today</div>
                </div>
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        </div>
                        <span class="text-[12px] font-semibold text-green-700 bg-green-100 px-2 py-1 rounded-full">+4</span>
                    </div>
                    <div class="text-[13px] text-gray-500 font-medium">Appointments booked</div>
                    <div class="text-[28px] font-semibold text-gray-900 mt-1" data-stat="appointments">0</div>
                    <div class="text-[12px] text-gray-400 mt-1">This week</div>
                </div>
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        </div>
                        <span class="text-[12px] font-semibold text-gray-600 bg-gray-200 px-2 py-1 rounded-full">avg</span>
                    </div>
                    <div class="text-[13px] text-gray-500 font-medium">Avg. call duration</div>
                    <div class="text-[28px] font-semibold text-gray-900 mt-1" data-stat="duration">0:00</div>
                    <div class="text-[12px] text-gray-400 mt-1">Last 24h</div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="flex flex-col lg:flex-row gap-8">
                <div class="flex-1 w-full lg:w-[68%]">
                    <div class="bg-white rounded-3xl border border-gray-100 p-7 mb-8 shadow-[0_2px_10px_rgba(0,0,0,0.03)]">
                        <div class="flex items-center justify-between mb-6">
                            <div>
                                <h2 class="text-[19px] font-semibold text-gray-900">Call volume</h2>
                                <p class="text-[13px] text-gray-500 mt-0.5">Last 7 days</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="inline-flex items-center gap-1.5 text-[13px] text-gray-600"><span class="w-2.5 h-2.5 rounded-full bg-black"></span> Answered</span>
                                <span class="inline-flex items-center gap-1.5 text-[13px] text-gray-600 ml-3"><span class="w-2.5 h-2.5 rounded-full bg-gray-300"></span> Missed</span>
                            </div>
                        </div>
                        <div id="chart" class="flex items-end justify-between gap-3 h-[180px]"></div>
                        <div id="chart-labels" class="flex justify-between gap-3 mt-3 text-[12px] text-gray-400 font-medium"></div>
                    </div>

                    <div class="relative mb-6">
                        <i data-lucide="search" class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 w-5 h-5"></i>
                        <input id="call-search" type="text" placeholder="Search calls, callers, or transcripts" class="w-full pl-12 pr-4 py-[14px] rounded-2xl border border-gray-300 focus:outline-none focus:border-gray-400 hover:border-gray-400 text-[15px] shadow-sm">
                    </div>

                    <div class="flex justify-between items-center border-b border-gray-200 mb-0">
                        <div class="flex space-x-8">
                            <button data-tab="all" class="tab-btn text-black font-medium pb-4 border-b-2 border-black text-[15px]">All calls</button>
                            <button data-tab="answered" class="tab-btn text-gray-600 hover:text-black font-medium pb-4 text-[15px]">Answered</button>
                            <button data-tab="missed" class="tab-btn text-gray-600 hover:text-black font-medium pb-4 text-[15px]">Missed</button>
                            <button data-tab="appointment" class="tab-btn text-gray-600 hover:text-black font-medium pb-4 text-[15px]">Booked</button>
                            <button data-tab="transferred" class="tab-btn text-gray-600 hover:text-black font-medium pb-4 text-[15px] flex items-center">
                                Transferred <span class="bg-[#ff5a00] text-white text-[11px] rounded-full w-5 h-5 flex items-center justify-center ml-2 leading-none">2</span>
                            </button>
                        </div>
                        <button class="flex items-center text-gray-600 border border-gray-300 rounded-full px-4 py-1.5 text-[15px] hover:bg-gray-50 transition-colors mb-2 font-medium">
                            <i data-lucide="sliders-horizontal" class="w-4 h-4 mr-2 text-green-600"></i> Filters
                        </button>
                    </div>

                    <div id="call-list" class="flex flex-col"></div>
                </div>

                <div class="w-full lg:w-[32%] flex flex-col gap-6">
                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 pt-8 pb-8">
                        <div class="flex items-center mb-6">
                            <div class="w-16 h-16 rounded-full overflow-hidden bg-white flex items-center justify-center mr-4 relative border border-gray-200">
                                <img src="../Images/logo.png" class="w-full h-full object-cover">
                                <span class="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-[#f9fafb]"></span>
                            </div>
                            <div>
                                <h2 class="font-medium text-lg">Solana</h2>
                                <p class="text-[13px] text-gray-500 mt-1">Online &amp; answering</p>
                            </div>
                        </div>
                        <div class="space-y-4">
                            <div>
                                <div class="flex justify-between items-center group cursor-pointer mb-1">
                                    <span class="text-[15px] font-medium">Current number</span>
                                    <div class="bg-white border border-gray-200 rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <i data-lucide="pencil" class="w-3.5 h-3.5 text-gray-500"></i>
                                    </div>
                                </div>
                                <div class="text-[15px] text-gray-700">(555) 000-0000</div>
                            </div>
                            <div class="pt-4">
                                <a href="#" class="text-[15px] font-medium text-black hover:underline decoration-1 underline-offset-2">Configure Solana</a>
                                <div class="mt-3 flex items-center w-full">
                                    <div class="flex-1 bg-gray-200 h-1.5 rounded-full overflow-hidden flex"><div class="bg-black w-[85%] h-full rounded-full"></div></div>
                                    <span class="text-xs font-medium text-gray-600 ml-3">85%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 pb-8">
                        <div class="flex justify-between items-center mb-6">
                            <span class="font-medium text-[19px] text-gray-900">Live activity</span>
                            <span class="flex items-center gap-1.5 text-[12px] font-semibold text-green-700">
                                <span class="relative flex h-2 w-2">
                                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75"></span>
                                    <span class="relative inline-flex rounded-full h-2 w-2 bg-green-600"></span>
                                </span>
                                Live
                            </span>
                        </div>
                        <div id="activity-feed" class="space-y-5"></div>
                    </div>

                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 flex justify-between items-center cursor-pointer hover:bg-gray-100 transition-colors">
                        <div>
                            <div class="font-medium text-[15px] text-gray-500">Plan</div>
                            <div class="font-semibold text-[19px] text-gray-900 mt-0.5">Growth</div>
                        </div>
                        <i data-lucide="chevron-right" class="w-5 h-5 text-gray-500"></i>
                    </div>

                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6">
                        <div class="flex justify-between items-center mb-3">
                            <span class="font-medium text-[19px] text-gray-900">Minutes used</span>
                            <span class="text-[14px] font-semibold text-gray-900">142 / 500</span>
                        </div>
                        <div class="w-full bg-gray-200 h-2 rounded-full overflow-hidden"><div class="bg-black h-full rounded-full" style="width: 28.4%"></div></div>
                        <p class="text-[13px] text-gray-500 mt-3">Resets on November 1</p>
                    </div>

                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6 flex justify-between items-center cursor-pointer hover:bg-gray-100 transition-colors">
                        <span class="font-medium text-[19px] text-gray-900">Settings</span>
                        <i data-lucide="chevron-down" class="w-5 h-5 text-gray-500"></i>
                    </div>

                    <div class="bg-[#f9fafb] rounded-[24px] border border-gray-100 p-6">
                        <a href="#" class="text-[15px] font-medium text-gray-900 underline decoration-gray-300 hover:no-underline flex items-center">
                            Help &amp; support <i data-lucide="external-link" class="w-4 h-4 ml-1"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div id="panel-solana" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
            <div class="mb-8">
                <h1 class="text-[32px] font-semibold text-gray-900">Solana</h1>
                <p class="text-gray-500 text-[15px] mt-1">Configure your AI receptionist.</p>
            </div>
            <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
                <h2 class="text-[19px] font-semibold text-gray-900 mb-5">Agent status</h2>
                <div class="flex items-center gap-4 mb-6">
                    <div class="w-14 h-14 rounded-full bg-black flex items-center justify-center text-white text-lg font-bold relative">
                        S
                        <span class="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white"></span>
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">Online</div>
                        <div class="text-[13px] text-gray-500">Answering calls 24/7</div>
                    </div>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center justify-between rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <span class="text-[14px] font-medium text-gray-700">Greeting</span>
                        <span class="text-[14px] text-gray-500">Hi, thanks for calling&hellip;</span>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <span class="text-[14px] font-medium text-gray-700">Voice</span>
                        <span class="text-[14px] text-gray-500">Aria</span>
                    </div>
                    <div class="flex items-center justify-between rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <span class="text-[14px] font-medium text-gray-700">Language</span>
                        <span class="text-[14px] text-gray-500">English (US)</span>
                    </div>
                </div>
            </div>
        </div>

        <div id="panel-number" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
            <div class="mb-8">
                <h1 class="text-[32px] font-semibold text-gray-900">Number</h1>
                <p class="text-gray-500 text-[15px] mt-1">The phone number Solana answers.</p>
            </div>
            <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
                <div class="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                        <div class="text-[13px] text-gray-500 font-medium">Current number</div>
                        <div class="text-[24px] font-semibold text-gray-900 mt-1">(555) 000-0000</div>
                    </div>
                    <button class="btn-primary inline-flex items-center justify-center px-5 py-2.5 rounded-xl font-semibold text-[14px]">
                        Change number
                    </button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div class="rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <div class="text-[12px] text-gray-500 font-medium">Forwarding</div>
                        <div class="text-[14px] text-gray-900 font-medium mt-0.5">On</div>
                    </div>
                    <div class="rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <div class="text-[12px] text-gray-500 font-medium">Voicemail</div>
                        <div class="text-[14px] text-gray-900 font-medium mt-0.5">Disabled</div>
                    </div>
                    <div class="rounded-xl bg-[#f9fafb] border border-gray-100 px-4 py-3">
                        <div class="text-[12px] text-gray-500 font-medium">Area code</div>
                        <div class="text-[14px] text-gray-900 font-medium mt-0.5">555</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="panel-calls" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
            <div class="mb-8">
                <h1 class="text-[32px] font-semibold text-gray-900">Calls</h1>
                <p class="text-gray-500 text-[15px] mt-1">Every call Solana has handled.</p>
            </div>
            <div class="bg-white rounded-3xl border border-gray-100 p-8 shadow-[0_2px_10px_rgba(0,0,0,0.04)]">
                <p class="text-gray-500 text-[15px]">A full call history will appear here. For now, see the list on the Home tab.</p>
            </div>
        </div>

        <div id="panel-finances" class="panel hidden max-w-[1200px] mx-auto px-8 py-8">
            <div class="mb-8">
                <h1 class="text-[32px] font-semibold text-gray-900">Finances</h1>
                <p class="text-gray-500 text-[15px] mt-1">Billing, plan, and usage.</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="text-[13px] text-gray-500 font-medium">Plan</div>
                    <div class="text-[24px] font-semibold text-gray-900 mt-1">Growth</div>
                </div>
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="text-[13px] text-gray-500 font-medium">Minutes used</div>
                    <div class="text-[24px] font-semibold text-gray-900 mt-1">142 / 500</div>
                </div>
                <div class="bg-[#f9fafb] rounded-[20px] border border-gray-100 p-6">
                    <div class="text-[13px] text-gray-500 font-medium">Next billing</div>
                    <div class="text-[24px] font-semibold text-gray-900 mt-1">Nov 1</div>
                </div>
            </div>
        </div>
    </main>
"""

DASHBOARD_JS = """
  <script>
    // ============================================================
    // SIMULATED DATA — swap each block for a Firebase read when ready.
    // ============================================================
    // TODO: getAuth().currentUser
    const mockUser = { displayName: 'Taymoor A.' };

    // TODO: Firestore query on `calls` ordered by createdAt desc.
    const mockCalls = [
        { id: 'c1', type: 'answered', caller: 'Maya R.', phone: '(415) 555-0128',
          postedAt: '6 hours ago', duration: '2:47',
          summary: 'Reschedule her Thursday appointment to Friday at 10am.',
          tags: ['Appointment', 'Reschedule'],
          action: { label: 'Moved to Fri 10:00', kind: 'booked' }, verified: true },
        { id: 'c2', type: 'answered', caller: 'Unknown', phone: '(628) 555-0114',
          postedAt: '5 hours ago', duration: '0:52',
          summary: 'Asked whether you offer emergency after-hours service. Said Solana would have someone call back within the hour.',
          tags: ['After hours', 'FAQ'],
          action: { label: 'Callback queued', kind: 'transfer' }, verified: true },
        { id: 'c3', type: 'missed', caller: 'Daniel K.', phone: '(510) 555-0177',
          postedAt: '4 hours ago', duration: '—',
          summary: 'Caller hung up before Solana finished the greeting.',
          tags: ['Missed'], action: null, verified: false },
        { id: 'c4', type: 'appointment', caller: 'Patricia L.', phone: '(650) 555-0142',
          postedAt: '3 hours ago', duration: '3:12',
          summary: 'Booked a new consultation for Tuesday at 2:15pm and confirmed by text.',
          tags: ['Booked', 'New client'],
          action: { label: 'Tue 14:15 confirmed', kind: 'booked' }, verified: true },
        { id: 'c5', type: 'answered', caller: 'Marcus B.', phone: '(415) 555-0199',
          postedAt: '2 hours ago', duration: '1:35',
          summary: 'Wants a quote for a recurring monthly service. Left email and asked for a call back tomorrow morning.',
          tags: ['Quote', 'Sales'],
          action: { label: 'Callback requested', kind: 'transfer' }, verified: true },
        { id: 'c6', type: 'transferred', caller: 'Nina S.', phone: '(925) 555-0101',
          postedAt: '48 min ago', duration: '0:38',
          summary: 'Urgent — water heater leaking. Warm-transferred to your on-call line.',
          tags: ['Urgent', 'Transfer'],
          action: { label: 'Rang on-call', kind: 'transfer' }, verified: true },
    ];

    // TODO: aggregated rollup doc.
    const mockStats = { answered: 14, messages: 9, appointments: 6, duration: '2:11' };

    // TODO: 7-day aggregation query.
    const mockChart = [
        { day: 'Mon', answered: 9, missed: 1 },
        { day: 'Tue', answered: 12, missed: 2 },
        { day: 'Wed', answered: 15, missed: 0 },
        { day: 'Thu', answered: 11, missed: 3 },
        { day: 'Fri', answered: 18, missed: 1 },
        { day: 'Sat', answered: 14, missed: 2 },
        { day: 'Sun', answered: 16, missed: 1 },
    ];

    // TODO: Firestore onSnapshot on tenant activity.
    const mockActivity = [
        { time: 'Just now', text: 'Solana answered a call from Maya R.', kind: 'call' },
        { time: '3 min ago', text: 'New appointment booked for Tuesday.', kind: 'booking' },
        { time: '12 min ago', text: 'Text confirmation sent to Nina S.', kind: 'sms' },
        { time: '1 hr ago', text: 'Missed call logged from Daniel K.', kind: 'missed' },
        { time: '2 hr ago', text: 'Message captured from Marcus B.', kind: 'message' },
    ];

    // ============================================================
    // RENDER
    // ============================================================
    document.getElementById('today-date').textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'long', month: 'long', day: 'numeric'
    });
    document.getElementById('user-name').textContent = mockUser.displayName;
    document.getElementById('banner-calls').textContent = mockStats.answered;

    function countUp(el, target) {
        const start = performance.now(), duration = 700;
        function tick(t) {
            const p = Math.min((t - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased);
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }
    countUp(document.querySelector('[data-stat="answered"]'), mockStats.answered);
    countUp(document.querySelector('[data-stat="messages"]'), mockStats.messages);
    countUp(document.querySelector('[data-stat="appointments"]'), mockStats.appointments);
    document.querySelector('[data-stat="duration"]').textContent = mockStats.duration;

    (function renderChart() {
        const chart = document.getElementById('chart');
        const labels = document.getElementById('chart-labels');
        const max = Math.max(...mockChart.map(d => d.answered + d.missed));
        mockChart.forEach(d => {
            const total = d.answered + d.missed;
            const h = (total / max) * 100;
            const ap = total === 0 ? 0 : (d.answered / total) * 100;
            const col = document.createElement('div');
            col.className = 'flex-1 h-full flex flex-col justify-end gap-0.5';
            col.innerHTML = `
                <div class="spark-bar rounded-t-md bg-gray-300" style="height: ${h * (1 - ap/100)}%"></div>
                <div class="spark-bar rounded-b-md bg-black" style="height: ${h * (ap/100)}%"></div>
            `;
            chart.appendChild(col);
            const lbl = document.createElement('div');
            lbl.className = 'flex-1 text-center';
            lbl.textContent = d.day;
            labels.appendChild(lbl);
        });
    })();

    const callList = document.getElementById('call-list');
    let currentFilter = 'all';
    let currentSearch = '';

    function renderCalls() {
        callList.innerHTML = '';
        const filtered = mockCalls.filter(c => {
            const matchesTab = currentFilter === 'all' || c.type === currentFilter;
            const n = currentSearch.toLowerCase();
            const matchesSearch = !n
                || c.caller.toLowerCase().includes(n)
                || c.phone.toLowerCase().includes(n)
                || c.summary.toLowerCase().includes(n)
                || c.tags.some(t => t.toLowerCase().includes(n));
            return matchesTab && matchesSearch;
        });

        if (!filtered.length) {
            callList.innerHTML = `<div class="py-16 text-center"><p class="text-gray-400 text-[15px]">No calls match your filters.</p></div>`;
            return;
        }

        const tagClass = 'bg-[#f2f2f2] text-gray-600 text-[13px] px-3 py-1 rounded-full font-medium';
        filtered.forEach(c => {
            const actionHtml = c.action
                ? `<span class="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-gray-800 bg-gray-100 border border-gray-200 px-2.5 py-1 rounded-full">
                       <span class="w-1.5 h-1.5 rounded-full ${c.action.kind === 'booked' ? 'bg-green-500' : 'bg-orange-500'}"></span>
                       ${c.action.label}
                   </span>` : '';
            const row = document.createElement('div');
            row.className = 'bg-white p-6 pb-8 border-b border-gray-200 relative group';
            row.innerHTML = `
                <div class="absolute right-6 top-6 flex space-x-2">
                    <button class="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors border border-transparent hover:border-gray-200"><i data-lucide="thumbs-down" class="w-[18px] h-[18px]"></i></button>
                    <button class="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors border border-transparent hover:border-gray-200"><i data-lucide="heart" class="w-[18px] h-[18px]"></i></button>
                </div>
                <div class="text-[13px] text-gray-500 mb-2">${c.postedAt} <span class="mx-1">•</span> Duration: ${c.duration}</div>
                <h2 class="text-xl font-medium text-gray-900 mb-2 hover:text-black cursor-pointer w-4/5">${c.caller}<span class="text-[13px] font-normal text-gray-400 ml-2">${c.phone}</span></h2>
                <p class="text-[15px] text-gray-800 mb-4 leading-[1.6]">${c.summary}</p>
                <div class="flex flex-wrap gap-2 mb-4">${c.tags.map(t => `<span class="${tagClass}">${t}</span>`).join('')}</div>
                <div class="flex items-center justify-between gap-4 flex-wrap">
                    <div class="flex items-center text-[13px] text-gray-600 space-x-4">
                        ${c.verified
                            ? `<div class="flex items-center text-gray-800 font-medium"><svg class="w-4 h-4 mr-1 text-blue-600" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>Verified caller</div>`
                            : `<div class="flex items-center text-gray-500 font-medium"><svg class="w-4 h-4 mr-1 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>Unverified</div>`}
                    </div>
                    ${actionHtml}
                </div>
            `;
            callList.appendChild(row);
        });
        if (window.lucide) lucide.createIcons();
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('text-black', 'border-b-2', 'border-black');
                b.classList.add('text-gray-600');
            });
            btn.classList.remove('text-gray-600');
            btn.classList.add('text-black', 'border-b-2', 'border-black');
            currentFilter = btn.dataset.tab;
            renderCalls();
        });
    });
    document.getElementById('call-search').addEventListener('input', e => {
        currentSearch = e.target.value.trim();
        renderCalls();
    });
    renderCalls();

    (function renderActivity() {
        const feed = document.getElementById('activity-feed');
        const iconMap = {
            call:    { icon: 'phone',         bg: 'bg-black' },
            booking: { icon: 'calendar',      bg: 'bg-black' },
            sms:     { icon: 'message-circle', bg: 'bg-gray-700' },
            missed:  { icon: 'phone-missed',  bg: 'bg-gray-400' },
            message: { icon: 'mail',          bg: 'bg-gray-700' },
        };
        mockActivity.forEach(a => {
            const conf = iconMap[a.kind] || iconMap.call;
            const el = document.createElement('div');
            el.className = 'flex items-start gap-3';
            el.innerHTML = `
                <div class="w-8 h-8 rounded-full ${conf.bg} flex items-center justify-center flex-shrink-0 mt-0.5">
                    <i data-lucide="${conf.icon}" class="w-4 h-4 text-white"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-[14px] text-gray-800 leading-[1.5]">${a.text}</p>
                    <p class="text-[12px] text-gray-400 mt-0.5">${a.time}</p>
                </div>
            `;
            feed.appendChild(el);
        });
        if (window.lucide) lucide.createIcons();
    })();

    document.getElementById('signout-btn').addEventListener('click', () => {
        try { localStorage.removeItem('vocallus_user'); } catch (e) {}
        window.location.href = 'login.html';
    });

    // Sidebar tab switching — swap panels, no reload.
    (function () {
        var tabs = document.querySelectorAll('.dash-tab');
        var panels = document.querySelectorAll('.panel');

        function activate(name) {
            tabs.forEach(function (t) {
                var on = t.dataset.panel === name;
                t.classList.toggle('bg-gray-200/80', on);
                t.classList.toggle('text-gray-900', on);
                t.classList.toggle('text-gray-500', !on);
                var bar = t.querySelector('.dash-bar');
                if (bar) {
                    bar.classList.toggle('opacity-100', on);
                    bar.classList.toggle('opacity-0', !on);
                }
            });
            panels.forEach(function (p) {
                p.classList.toggle('hidden', p.id !== 'panel-' + name);
            });
        }

        tabs.forEach(function (t) {
            t.addEventListener('click', function (e) {
                var href = t.getAttribute('href') || '';
                // Real navigation links (solana.html, history.html) let the
                // browser handle it — only intercept in-page tab links.
                if (href.indexOf('#') === -1) return;
                e.preventDefault();
                activate(t.dataset.panel);
                if (history.replaceState) {
                    history.replaceState(null, '', '#' + t.dataset.panel);
                }
            });
        });

        // Activate the panel matching the URL hash on load.
        var initialHash = (window.location.hash || '').replace('#', '');
        if (initialHash && document.getElementById('panel-' + initialHash)) {
            activate(initialHash);
        }
    })();
  </script>
"""


def page_dashboard(_ctx: Ctx):
    """The dashboard uses a completely different shell — handled in render()."""
    return "Dashboard", "Your Vocallus dashboard.", DASHBOARD_BODY, ""


# ---------------------------------------------------------------------------
# Page registry
# ---------------------------------------------------------------------------

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
]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_page(path: str, builder) -> str:
    depth = len(Path(path).parts) - 1
    ctx = Ctx(depth)

    title, description, content, main_class = builder(ctx)

    head = HEAD.substitute(
        title=title,
        description=description,
        css=SHARED_CSS,
        favicon=ctx.img(FAVICON_IMAGE),
    )

    # Dashboard uses its own shell.
    if Path(path).name == "dashboard.html":
        return DASHBOARD_SHELL.substitute(
            head=head,
            content=content,
            scripts=SHARED_JS + DASHBOARD_JS,
        )

    return MARKETING_SHELL.substitute(
        head=head,
        header=render_header(ctx, path),
        footer=render_footer(ctx),
        main_class=main_class,
        content=content,
        scripts=SHARED_JS,
    )


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build() -> None:
    print(f"Building {SITE_NAME} …\n")

    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("Images:")
    ensure_images()

    print("\nPages:")
    for rel_path, builder in PAGES:
        out = ROOT / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        html = render_page(rel_path, builder)
        out.write_text(html, encoding="utf-8")
        print(f"  [write] {rel_path}  ({len(html):,} bytes)")

    # Clean up the old product.html from earlier builds.
    stale = PAGES_DIR / "product.html"
    if stale.exists():
        stale.unlink()
        print(f"\n  [del]  Pages/product.html (replaced by products.html)")

    print(f"\nDone. {len(PAGES)} pages written to {ROOT}")
    print("Open index.html in your browser to preview.")




# --- edit.py: Solana page + History page + sidebar nav ---

# ---- sidebar helper (used by solana.html and history.html) ----
SIDEBAR_TPL = '''    <nav class="w-[88px] bg-[#f2f2f2] border-r border-gray-200 flex flex-col justify-between items-center py-6 flex-shrink-0 z-10">
        <div class="flex flex-col items-center w-full space-y-4">
            <a href="../index.html" class="mb-2 select-none">
                <img src="../Images/logo.png" alt="Vocallus" class="w-9 h-9 rounded-xl" />
            </a>

            <div class="flex flex-col w-full items-center space-y-2">
                <a href="dashboard.html" data-nav="home" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __HOME_CLS__">
                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __HOME_BAR__"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5L12 3l9 7.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                    <span class="text-[11px] font-medium tracking-tight">Home</span>
                </a>

                <a href="solana.html" data-nav="solana" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __SOLANA_CLS__">
                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __SOLANA_BAR__"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Solana</span>
                </a>

                <a href="dashboard.html#number" data-nav="number" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __NUMBER_CLS__">
                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __NUMBER_BAR__"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.05 5A5 5 0 0 1 19 8.95"></path><path d="M15.05 1A9 9 0 0 1 23 8.94"></path><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Number</span>
                </a>

                <a href="history.html" data-nav="history" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __HISTORY_CLS__">
                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __HISTORY_BAR__"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    <span class="text-[11px] font-medium tracking-tight">History</span>
                </a>

                <a href="dashboard.html#finances" data-nav="finances" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __FINANCES_CLS__">
                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __FINANCES_BAR__"></div>
                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                    <span class="text-[11px] font-medium tracking-tight">Finances</span>
                </a>
            </div>
        </div>

        <div class="flex flex-col w-full items-center space-y-4">
            <a href="#" class="text-gray-500 hover:text-gray-800 relative p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ff5a00] rounded-full border-2 border-[#f2f2f2]"></span>
            </a>
            <button id="signout-btn" title="Sign out" class="text-gray-500 hover:text-gray-800 p-2 transition-colors">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
        </div>
    </nav>'''

def _render_sidebar(active):
    html = SIDEBAR_TPL
    for name in ("home", "solana", "number", "history", "finances"):
        if name == active:
            cls = "bg-gray-200/80 text-gray-900"
            bar = "opacity-100"
        else:
            cls = "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
            bar = "opacity-0"
        html = html.replace("__" + name.upper() + "_CLS__", cls)
        html = html.replace("__" + name.upper() + "_BAR__", bar)
    return html


# ---- solana.html ----
SOLANA_BODY_TPL = '''{sidebar}
    <aside class="w-[320px] bg-[#f9fafb] border-r border-gray-200 flex flex-col flex-shrink-0">
        <div class="p-5 border-b border-gray-200">
            <div class="flex items-center gap-3 mb-2">
                <img src="../Images/logo.png" alt="" class="w-11 h-11 rounded-2xl" />
                <div class="flex-1">
                    <div class="font-semibold text-[15px] text-gray-900" id="agent-name-display">Solana</div>
                    <div class="text-[12px] text-gray-500">AI receptionist</div>
                </div>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
            <div>
                <label class="block text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-2">Agent name</label>
                <input id="agent-name" type="text" value="Solana" placeholder="What should your Solana be called?"
                       class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] focus:outline-none focus:border-gray-400 bg-white">
            </div>

            <div>
                <label class="block text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-2">System prompt</label>
                <p class="text-[12px] text-gray-400 mb-2">How your agent should greet and respond.</p>
                <textarea id="system-prompt" rows="11" placeholder="You are Solana, the friendly AI receptionist for Acme Services. Greet callers warmly, ask how you can help, and book appointments when requested."
                          class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[13.5px] leading-[1.6] focus:outline-none focus:border-gray-400 bg-white resize-none">You are Solana, the friendly AI receptionist for Acme Services. Greet callers warmly, ask how you can help, and book appointments when requested. Keep answers short and confirm any booking by repeating the day and time back to the caller.</textarea>
            </div>

            <button id="save-prompt"
                    class="w-full btn-primary rounded-xl py-3 font-semibold text-[14px]">
                Save changes
            </button>

            <div>
                <div class="text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-3">Presets</div>
                <div class="space-y-2">
                    <button data-preset="voice" class="preset-btn w-full text-left rounded-xl border border-gray-200 bg-white px-3.5 py-3 hover:border-gray-400 transition">
                        <div class="text-[13.5px] font-semibold text-gray-900">Voice assistant</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Warm, friendly, conversational</div>
                    </button>
                    <button data-preset="booking" class="preset-btn w-full text-left rounded-xl border border-gray-200 bg-white px-3.5 py-3 hover:border-gray-400 transition">
                        <div class="text-[13.5px] font-semibold text-gray-900">Booking agent</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Focused on scheduling appointments</div>
                    </button>
                    <button data-preset="support" class="preset-btn w-full text-left rounded-xl border border-gray-200 bg-white px-3.5 py-3 hover:border-gray-400 transition">
                        <div class="text-[13.5px] font-semibold text-gray-900">Support agent</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Answers FAQs, escalates when needed</div>
                    </button>
                </div>
            </div>
        </div>
    </aside>

    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl shadow-[-5px_0_15px_-3px_rgba(0,0,0,0.1)]">
        <div class="max-w-[1100px] mx-auto px-8 py-8">

            <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
                <div>
                    <h1 class="text-[26px] font-semibold text-gray-900">Test your Solana</h1>
                    <p class="text-gray-500 text-[14px] mt-0.5">Try your agent before connecting a phone number.</p>
                </div>
                <div class="flex bg-gray-100 rounded-full p-1">
                    <button data-mode="call" class="mode-btn px-5 py-2 rounded-full text-[14px] font-semibold bg-white shadow-sm text-gray-900">Call</button>
                    <button data-mode="text" class="mode-btn px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">Text</button>
                </div>
            </div>

            <!-- Setup card: shown when no key is set -->
            <div id="api-setup" class="rounded-3xl border border-gray-100 p-7 mb-8 bg-[#f9fafb]">
                <div class="mb-6">
                    <h2 class="text-[18px] font-semibold text-gray-900">Connect an AI provider</h2>
                    <p class="text-[14px] text-gray-500 mt-1">Choose a provider and paste your API key.</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6" id="provider-grid">
                    <button data-provider="openai" class="provider-card relative rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/cha.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">OpenAI</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">GPT models</div>
                    </button>
                    <button data-provider="gemini" class="provider-card relative rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/gem.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">Gemini</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Google models</div>
                    </button>
                    <button data-provider="claude" class="provider-card relative rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/cla.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">Claude</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Anthropic models</div>
                    </button>
                </div>

                <div class="mb-5">
                    <label class="block text-[13px] font-semibold text-gray-700 mb-2">API key</label>
                    <input id="api-key" type="password" placeholder="Paste your API key"
                           class="w-full rounded-xl border border-gray-200 px-3.5 py-3 text-[14px] focus:outline-none focus:border-gray-400 bg-white">
                    <p id="key-hint" class="text-[12px] text-gray-400 mt-1.5">Pick a provider to see the expected key format.</p>
                </div>

                <div class="mb-5">
                    <label class="block text-[13px] font-semibold text-gray-700 mb-2">Model</label>

                </div>

                <div id="api-error" class="hidden rounded-xl bg-red-50 border border-red-200 p-4 mb-5">
                    <div class="flex items-start gap-3">
                        <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        <div>
                            <div id="api-error-title" class="text-[14px] font-semibold text-red-800">Invalid API key</div>
                            <div id="api-error-msg" class="text-[13px] text-red-700 mt-1">Check the key and try again.</div>
                        </div>
                    </div>
                </div>

                <button id="save-key" class="btn-primary px-6 py-3 rounded-xl font-semibold text-[14px]">
                    Save and continue
                </button>
            </div>

            <!-- Chat preview: shown after key is set -->
            <div id="chat-preview" class="hidden rounded-3xl border border-gray-100 bg-[#f9fafb] p-7">

                <div id="call-view">
                    <div class="text-center py-10">
                        <img src="../Images/logo.png" alt="" class="w-20 h-20 mx-auto rounded-3xl mb-4">
                        <div class="text-[22px] font-semibold text-gray-900">Test call</div>
                        <div class="text-[14px] text-gray-500 mt-1.5">Solana will answer as configured.</div>
                        <button id="start-call" class="mt-8 btn-primary inline-flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-[14px]">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                            Start test call
                        </button>
                    </div>
                </div>

                <div id="text-view" class="hidden">
                    <div class="space-y-4 mb-6" id="chat-log">
                        <div class="flex items-start gap-3">
                            <img src="../Images/logo.png" alt="" class="w-8 h-8 rounded-xl flex-shrink-0">
                            <div class="bg-white rounded-2xl rounded-tl-sm border border-gray-100 px-4 py-3 max-w-[70%]">
                                <p class="text-[14px] text-gray-800 leading-[1.5]">Hi, thanks for reaching out to Acme Services. How can I help today?</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-3 justify-end">
                            <div class="bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[70%]">
                                <p class="text-[14px] leading-[1.5]">Can I book a consultation for next Tuesday?</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-3">
                            <img src="../Images/logo.png" alt="" class="w-8 h-8 rounded-xl flex-shrink-0">
                            <div class="bg-white rounded-2xl rounded-tl-sm border border-gray-100 px-4 py-3 max-w-[70%]">
                                <p class="text-[14px] text-gray-800 leading-[1.5]">Of course. Next Tuesday at 10am or 2pm are both open. Which works best?</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <input type="text" placeholder="Type a message to test your Solana"
                               class="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-[14px] focus:outline-none focus:border-gray-400">
                        <button class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Send</button>
                    </div>
                </div>


        </div>
    </main>'''
SOLANA_JS = '''  <script>
    (function () {
      var PROVIDERS = {
        openai: {
          name: 'OpenAI', icon: '../Images/cha.png',
          keyPrefixes: ['sk-'], hint: 'OpenAI keys start with "sk-".',
          defaultModel: 'gpt-5-nano'
        },
        gemini: {
          name: 'Gemini', icon: '../Images/gem.png',
          keyPrefixes: ['AIza', 'AQ.'], hint: 'Gemini keys start with "AIza" or "AQ.".',
          defaultModel: 'gemini-3.5-flash-lite'
        },
        claude: {
          name: 'Claude', icon: '../Images/cla.png',
          keyPrefixes: ['sk-ant-'], hint: 'Claude keys start with "sk-ant-".',
          defaultModel: 'claude-haiku-4-5-20251001'
        }
      };

      var currentProvider = null;
      var chatHistory = [];

      var providerBtns = document.querySelectorAll('.provider-card');
      var keyInput  = document.getElementById('api-key');
      var keyHint   = document.getElementById('key-hint');
      var errorBox  = document.getElementById('api-error');
      var errorTitle= document.getElementById('api-error-title');
      var errorMsg  = document.getElementById('api-error-msg');
      var setupCard = document.getElementById('api-setup');
      var previewCard = document.getElementById('chat-preview');
      var saveBtn   = document.getElementById('save-key');

      function showError(t, m) {
        errorTitle.textContent = t; errorMsg.textContent = m;
        errorBox.classList.remove('hidden');
      }
      function hideError() { errorBox.classList.add('hidden'); }

      function selectProvider(id) {
        currentProvider = id;
        var p = PROVIDERS[id];
        providerBtns.forEach(function (b) {
          var on = b.dataset.provider === id;
          b.classList.toggle('border-black', on);
          b.classList.toggle('ring-2', on);
          b.classList.toggle('ring-black/10', on);
          b.classList.toggle('border-gray-200', !on);
          b.classList.toggle('ring-0', !on);
        });
        keyHint.textContent = p.hint;
        hideError();
      }

      providerBtns.forEach(function (b) {
        b.addEventListener('click', function () { selectProvider(b.dataset.provider); });
      });

      saveBtn.addEventListener('click', function () {
        hideError();
        var key = keyInput.value.trim();
        var provider = currentProvider;
        if (!provider) { showError('No provider selected', 'Pick OpenAI, Gemini, or Claude above.'); return; }
        var p = PROVIDERS[provider];
        if (!key) { showError('API key required', 'Paste a key from your ' + p.name + ' account.'); return; }
        var ok = p.keyPrefixes.some(function (pre) { return key.indexOf(pre) === 0; });
        if (key.length < 8 || !ok) { showError('Invalid API key', 'The key was rejected. ' + p.hint); return; }

        try {
          localStorage.setItem('vocallus_ai', JSON.stringify({
            provider: provider, model: p.defaultModel,
            key: key, configured: true
          }));
        } catch (e) {}

        setupCard.classList.add('hidden');
        previewCard.classList.remove('hidden');
      });

      document.getElementById('disconnect').addEventListener('click', function () {
        try { localStorage.removeItem('vocallus_ai'); } catch (e) {}
        setupCard.classList.remove('hidden');
        previewCard.classList.add('hidden');
        currentProvider = null;
        providerBtns.forEach(function (b) {
          b.classList.remove('border-black', 'ring-2', 'ring-black/10');
          b.classList.add('border-gray-200', 'ring-0');
        });
        keyInput.value = '';
      });

      /* Restore saved provider */
      try {
        var saved = JSON.parse(localStorage.getItem('vocallus_ai') || 'null');
        if (saved && saved.configured) {
          selectProvider(saved.provider);
          keyInput.value = saved.key || '';
          setupCard.classList.add('hidden');
          previewCard.classList.remove('hidden');
        }
      } catch (e) {}

      /* -------- Chat -------- */
      var chatLog = document.getElementById('chat-log');
      var chatInput = document.getElementById('chat-input');
      var chatSend = document.getElementById('chat-send');

      function getAgent() {
        try { return JSON.parse(localStorage.getItem('vocallus_agent') || 'null') || {}; }
        catch (e) { return {}; }
      }

      function pushBubble(role, text) {
        var wrap = document.createElement('div');
        wrap.className = role === 'user'
          ? 'flex items-start gap-3 justify-end'
          : 'flex items-start gap-3';
        wrap.innerHTML = role === 'user'
          ? '<div class="bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[70%]"><p class="text-[14px] leading-[1.5]"></p></div>'
          : '<img src="../Images/logo.png" alt="" class="w-8 h-8 rounded-xl flex-shrink-0"><div class="bg-white rounded-2xl rounded-tl-sm border border-gray-100 px-4 py-3 max-w-[70%]"><p class="text-[14px] text-gray-800 leading-[1.5]"></p></div>';
        wrap.querySelector('p').textContent = text;
        chatLog.appendChild(wrap);
        chatLog.scrollTop = chatLog.scrollHeight;
        return wrap;
      }

      function askAI(userText) {
        var cfg = null;
        try { cfg = JSON.parse(localStorage.getItem('vocallus_ai') || 'null'); } catch (e) {}
        if (!cfg) return Promise.reject(new Error('no config'));
        var agent = getAgent();
        var sys = agent.prompt || 'You are Solana, a friendly AI receptionist. Keep replies short and helpful.';
        var name = agent.name || 'Solana';

        chatHistory.push({ role: 'user', content: userText });

        // Try our Netlify function first — it handles CORS and hides nothing
        // it shouldn't. Falls back to a direct call for providers that allow
        // browser origins (Gemini and Claude both do).
        var tryFn = fetch('/.netlify/functions/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider: cfg.provider, model: cfg.model, key: cfg.key,
            system: sys, name: name, messages: chatHistory
          })
        }).then(function (r) {
          if (!r.ok) throw new Error('fn ' + r.status);
          return r.json();
        }).then(function (j) { return j.reply; });

        return tryFn.catch(function () {
          return directCall(cfg, sys, name);
        }).catch(function () {
          return '(Demo reply) I would normally answer via ' + cfg.provider +
                 ' using model ' + cfg.model + '. Once this is deployed to Netlify, ' +
                 'the real response will come through.';
        });
      }

      function directCall(cfg, sys, name) {
        if (cfg.provider === 'gemini') {
          var url = 'https://generativelanguage.googleapis.com/v1beta/models/' +
                    cfg.model + ':generateContent?key=' + encodeURIComponent(cfg.key);
          return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              systemInstruction: { parts: [{ text: sys }] },
              contents: chatHistory.map(function (m) {
                return { role: m.role === 'user' ? 'user' : 'model',
                         parts: [{ text: m.content }] };
              })
            })
          }).then(function (r) { return r.json(); })
            .then(function (j) {
              var t = j.candidates && j.candidates[0] &&
                      j.candidates[0].content &&
                      j.candidates[0].content.parts &&
                      j.candidates[0].content.parts[0].text;
              if (!t) throw new Error('no text');
              return t;
            });
        }
        if (cfg.provider === 'claude') {
          return fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-api-key': cfg.key,
              'anthropic-version': '2023-06-01',
              'anthropic-dangerous-direct-browser-access': 'true'
            },
            body: JSON.stringify({
              model: cfg.model, max_tokens: 512, system: sys,
              messages: chatHistory
            })
          }).then(function (r) { return r.json(); })
            .then(function (j) {
              var t = j.content && j.content[0] && j.content[0].text;
              if (!t) throw new Error('no text');
              return t;
            });
        }
        // OpenAI does not permit browser calls — the Netlify function handles it.
        return Promise.reject(new Error('openai requires function'));
      }

      function handleSend() {
        var text = (chatInput.value || '').trim();
        if (!text) return;
        chatInput.value = '';
        pushBubble('user', text);
        var thinking = pushBubble('assistant', '…');

        askAI(text).then(function (reply) {
          thinking.querySelector('p').textContent = reply;
          chatHistory.push({ role: 'assistant', content: reply });
        }).catch(function () {
          thinking.querySelector('p').textContent = 'Something went wrong.';
        });
      }

      chatSend.addEventListener('click', handleSend);
      chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') handleSend();
      });

      /* -------- Call / Text toggle -------- */
      var callView = document.getElementById('call-view');
      var textView = document.getElementById('text-view');
      document.querySelectorAll('.mode-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var mode = btn.dataset.mode;
          document.querySelectorAll('.mode-btn').forEach(function (b) {
            var on = b.dataset.mode === mode;
            b.classList.toggle('bg-white', on); b.classList.toggle('shadow-sm', on);
            b.classList.toggle('text-gray-900', on); b.classList.toggle('font-semibold', on);
            b.classList.toggle('text-gray-500', !on); b.classList.toggle('font-medium', !on);
          });
          callView.classList.toggle('hidden', mode !== 'call');
          textView.classList.toggle('hidden', mode !== 'text');
        });
      });

      /* -------- Sub-sidebar -------- */
      var nameInput = document.getElementById('agent-name');
      var promptArea = document.getElementById('system-prompt');
      var nameDisplay = document.getElementById('agent-name-display');

      try {
        var agent = JSON.parse(localStorage.getItem('vocallus_agent') || 'null');
        if (agent) {
          if (agent.name) { nameInput.value = agent.name; nameDisplay.textContent = agent.name; }
          if (agent.prompt) promptArea.value = agent.prompt;
        }
      } catch (e) {}

      nameInput.addEventListener('input', function () {
        nameDisplay.textContent = nameInput.value || 'Solana';
      });

      document.getElementById('save-prompt').addEventListener('click', function () {
        try {
          localStorage.setItem('vocallus_agent', JSON.stringify({
            name: nameInput.value.trim() || 'Solana',
            prompt: promptArea.value.trim()
          }));
        } catch (e) {}
        this.textContent = 'Saved';
        var self = this;
        setTimeout(function () { self.textContent = 'Save changes'; }, 1200);
      });

      var PRESETS = {
        voice: 'You are Solana, a warm and friendly AI receptionist. Greet callers by name when possible, use natural conversational language, and always confirm the reason for the call before wrapping up.',
        booking: 'You are Solana, a booking-focused AI receptionist. Capture the caller\\'s name, preferred date, preferred time, and reason for visit, then confirm the appointment slot back to them.',
        support: 'You are Solana, a helpful support agent. Answer common questions clearly and briefly. If something is outside your knowledge, offer to take a callback message.'
      };
      document.querySelectorAll('.preset-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          promptArea.value = PRESETS[btn.dataset.preset] || '';
          promptArea.focus();
        });
      });

      document.getElementById('signout-btn').addEventListener('click', function () {
        try {
          localStorage.removeItem('vocallus_user');
          localStorage.removeItem('vocallus_ai');
          localStorage.removeItem('vocallus_agent');
        } catch (e) {}
        window.location.href = 'login.html';
      });

      if (window.lucide) lucide.createIcons();
    })();
  </script>
'''

def page_solana(_ctx):
    body = SOLANA_BODY_TPL.replace("{sidebar}", _render_sidebar("solana"))
    return "Solana", "Configure and test your Solana agent.", body, ""


# ---- history.html ----
HISTORY_BODY_TPL = '''{sidebar}
    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl shadow-[-5px_0_15px_-3px_rgba(0,0,0,0.1)]">
        <div class="max-w-[1100px] mx-auto px-8 py-8">

            <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
                <div>
                    <h1 class="text-[28px] font-semibold text-gray-900">History</h1>
                    <p class="text-gray-500 text-[14px] mt-0.5">Every call and text Solana has handled.</p>
                </div>
                <div class="flex bg-gray-100 rounded-full p-1">
                    <button data-filter="all" class="hist-filter px-5 py-2 rounded-full text-[14px] font-semibold bg-white shadow-sm text-gray-900">All</button>
                    <button data-filter="call" class="hist-filter px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">Calls</button>
                    <button data-filter="text" class="hist-filter px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">Texts</button>
                </div>
            </div>

            <div id="history-list" class="space-y-3"></div>
        </div>
    </main>'''
HISTORY_JS = '''
  <script>
    (function () {
      var EVENTS = [
        { id: 1, kind: 'call', caller: 'Maya R.', phone: '(415) 555-0128',
          time: '6 hours ago', duration: '2:47',
          preview: 'Reschedule her Thursday appointment to Friday at 10am.',
          tags: ['Appointment'] },
        { id: 2, kind: 'text', caller: 'Nina S.', phone: '(925) 555-0101',
          time: '5 hours ago', duration: '—',
          preview: 'Sent confirmation: "You\'re all set for tomorrow at 10. Reply C to cancel."',
          tags: ['Confirmation'] },
        { id: 3, kind: 'call', caller: 'Daniel K.', phone: '(510) 555-0177',
          time: '4 hours ago', duration: '0:22',
          preview: 'Hung up before greeting finished. Marked as missed.',
          tags: ['Missed'] },
        { id: 4, kind: 'text', caller: 'Marcus B.', phone: '(415) 555-0199',
          time: '3 hours ago', duration: '—',
          preview: 'Quote follow-up sent with pricing for the recurring plan.',
          tags: ['Quote'] },
        { id: 5, kind: 'call', caller: 'Patricia L.', phone: '(650) 555-0142',
          time: '2 hours ago', duration: '3:12',
          preview: 'Booked new consultation for Tuesday at 2:15pm.',
          tags: ['Booked'] },
        { id: 6, kind: 'call', caller: 'Unknown', phone: '(628) 555-0114',
          time: '1 hour ago', duration: '0:52',
          preview: 'Asked about emergency after-hours service. Callback queued.',
          tags: ['FAQ'] }
      ];

      var list = document.getElementById('history-list');
      var currentFilter = 'all';

      function render() {
        list.innerHTML = '';
        var filtered = EVENTS.filter(function (e) {
          return currentFilter === 'all' || e.kind === currentFilter;
        });

        if (!filtered.length) {
          list.innerHTML = ''
            + '<div class="py-20 text-center">'
            + '  <div class="w-14 h-14 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4">'
            + '    <svg class="w-6 h-6 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
            + '  </div>'
            + '  <p class="text-[16px] font-medium text-gray-700">Call history will appear here</p>'
            + '  <p class="text-[13.5px] text-gray-400 mt-1">Once Solana starts handling calls and texts, they\'ll show up in this list.</p>'
            + '</div>';
          return;
        }

        filtered.forEach(function (e) {
          var isCall = e.kind === 'call';
          var iconSvg = isCall
            ? '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>'
            : '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>';
          var bg = isCall ? 'bg-black' : 'bg-gray-700';

          var row = document.createElement('div');
          row.className = 'rounded-2xl border border-gray-100 bg-white p-5 hover:shadow-sm transition';
          row.innerHTML = `
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl ${bg} flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${iconSvg}</svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <div class="font-semibold text-[15px] text-gray-900">${e.caller}</div>
                  <div class="text-[13px] text-gray-400">${e.phone}</div>
                  <div class="text-[12px] text-gray-400 ml-auto">${e.time}</div>
                </div>
                <p class="text-[14px] text-gray-700 mt-1.5 leading-[1.55]">${e.preview}</p>
                <div class="flex items-center gap-2 mt-3 flex-wrap">
                  ${e.tags.map(function (t) { return '<span class="bg-[#f2f2f2] text-gray-600 text-[12px] px-2.5 py-0.5 rounded-full font-medium">' + t + '</span>'; }).join('')}
                  ${isCall ? '<span class="text-[12px] text-gray-400 ml-1">' + e.duration + '</span>' : ''}
                </div>
              </div>
            </div>
          `;
          list.appendChild(row);
        });
      }

      document.querySelectorAll('.hist-filter').forEach(function (btn) {
        btn.addEventListener('click', function () {
          document.querySelectorAll('.hist-filter').forEach(function (b) {
            var on = b === btn;
            b.classList.toggle('bg-white', on);
            b.classList.toggle('shadow-sm', on);
            b.classList.toggle('text-gray-900', on);
            b.classList.toggle('font-semibold', on);
            b.classList.toggle('text-gray-500', !on);
            b.classList.toggle('font-medium', !on);
          });
          currentFilter = btn.dataset.filter;
          render();
        });
      });

      document.getElementById('signout-btn').addEventListener('click', function () {
        try { localStorage.removeItem('vocallus_user'); } catch (e) {}
        window.location.href = 'login.html';
      });

      render();
    })();
  </script>
'''

def page_history(_ctx):
    body = HISTORY_BODY_TPL.replace("{sidebar}", _render_sidebar("history"))
    return "History", "Every call and text Solana has handled.", body, ""


# ---- wrap render_page so solana / history use the dashboard shell ----
_prev_render_page_2__u3 = render_page

def render_page(path, builder):
    name = Path(path).name
    if name in ("solana.html", "history.html"):
        depth = len(Path(path).parts) - 1
        ctx = Ctx(depth)
        title, description, content, _main = builder(ctx)
        head = HEAD.substitute(
            title=title,
            description=description,
            css=SHARED_CSS,
            favicon=ctx.img(FAVICON_IMAGE),
        )
        extra = (SOLANA_JS + _PROVIDER_SELECT_JS) if name == "solana.html" else HISTORY_JS
        return DASHBOARD_SHELL.substitute(
            head=head,
            content=content,
            scripts=SHARED_JS + extra,
        )
    return _prev_render_page_2__u3(path, builder)


# ---- wrap ensure_images to also create the provider icons ----
_prev_ensure_images = ensure_images

def ensure_images():
    _prev_ensure_images()
    _generate_provider_icons()


def _generate_provider_icons():
    icons = [
        ("cha.png", (26, 26, 26),   (60, 60, 60),   "G", (255, 255, 255)),
        ("gem.png", (66, 133, 244), (155, 114, 203), "\u25c6", (255, 255, 255)),
        ("cla.png", (217, 119, 87), (191, 87, 62),   "C", (255, 255, 255)),
    ]
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  [warn] Pillow missing; skipping provider icons")
        return

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, top, bottom, letter, letter_color in icons:
        path = IMAGES_DIR / filename
        if path.exists() and path.stat().st_size > 0:
            print(f"  [ok]   Images/{filename} (cached)")
            continue

        size = 128
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        grad = Image.new("RGBA", (size, size))
        gd = ImageDraw.Draw(grad)
        for y in range(size):
            t = y / (size - 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
            gd.line([(0, y), (size, y)], fill=color)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size-1, size-1], radius=int(size*0.24), fill=255)
        img.paste(grad, (0, 0), mask)
        d = ImageDraw.Draw(img)

        font = None
        for p in ("arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            try:
                font = ImageFont.truetype(p, int(size * 0.5))
                break
            except (OSError, IOError):
                pass
        if font is None:
            font = ImageFont.load_default()

        try:
            bbox = d.textbbox((0, 0), letter, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text(((size-w)/2 - bbox[0], (size-h)/2 - bbox[1]), letter,
                   font=font, fill=letter_color)
        except Exception:
            r = size // 6
            d.ellipse([size//2 - r, size//2 - r, size//2 + r, size//2 + r],
                      fill=letter_color)
        img.save(path, "PNG", optimize=True)
        print(f"  [new]  Images/{filename}")


# ---- register the new pages ----
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
]

# --- end edit.py: Solana page + History page + sidebar nav ---


# --- edit.py: bulletproof provider selection ---

_PROVIDER_SELECT_JS = '''
  <script>
    (function () {
      if (window.__vocallusProviderSelect) return;
      window.__vocallusProviderSelect = true;

      // Inject the CSS once. .selected is a plain class, so Tailwind
      // doesn't need to know about it — the browser applies it directly.
      var style = document.createElement('style');
      style.textContent =
        '.provider-card{position:relative;transition:border-color .15s ease,box-shadow .15s ease;}' +
        '.provider-card.selected{border-color:#111111 !important;box-shadow:0 0 0 3px rgba(17,17,17,.10) !important;}' +
        '.provider-card .selected-badge{display:none !important;}' +
        '.provider-card.selected .selected-badge{display:inline-flex !important;}';
      document.head.appendChild(style);

      // Event delegation in the capture phase, so nothing else can stop
      // the click before we see it.
      document.addEventListener('click', function (e) {
        var card = e.target && e.target.closest ? e.target.closest('.provider-card') : null;
        if (!card) return;
        var cards = document.querySelectorAll('.provider-card');
        for (var i = 0; i < cards.length; i++) {
          cards[i].classList.toggle('selected', cards[i] === card);
        }
      }, true);

      // If a provider was already saved, mark it selected on load.
      try {
        var saved = JSON.parse(localStorage.getItem('vocallus_ai') || 'null');
        if (saved && saved.provider) {
          var match = document.querySelector('.provider-card[data-provider="' + saved.provider + '"]');
          if (match) match.classList.add('selected');
        }
      } catch (e) {}
    })();
  </script>
'''


import re

# --- edit.py: Firebase v10 + Calendar + Pricing ---

FIREBASE_SCRIPT = '''
  <!-- Firebase v10 modular SDK + helpers -->
  <script type="module">
    import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
    import {
      getAuth, onAuthStateChanged, signInWithPopup, GoogleAuthProvider,
      signInWithEmailAndPassword, createUserWithEmailAndPassword,
      signOut, updateProfile, sendPasswordResetEmail
    } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';
    import {
      getFirestore, doc, getDoc, setDoc, updateDoc, deleteDoc,
      collection, onSnapshot, addDoc, query, where, orderBy, serverTimestamp
    } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';

    const firebaseConfig = {
      apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
      authDomain: "vocallus-aa81e.firebaseapp.com",
      projectId: "vocallus-aa81e",
      storageBucket: "vocallus-aa81e.firebasestorage.app",
      messagingSenderId: "997486177218",
      appId: "1:997486177218:web:7c4741dbd450549140845b",
      measurementId: "G-XXWMQ90D50"
    };

    const app  = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db   = getFirestore(app);

    window.__fb = {
      app, auth, db,
      onAuthStateChanged, signInWithPopup, GoogleAuthProvider,
      signInWithEmailAndPassword, createUserWithEmailAndPassword,
      signOut, updateProfile, sendPasswordResetEmail,
      doc, getDoc, setDoc, updateDoc, deleteDoc,
      collection, onSnapshot, addDoc, query, where, orderBy, serverTimestamp
    };

    window.dispatchEvent(new Event('firebase-ready'));
  </script>
  <script>
    // Tiny helper every page script uses to wait for the module above.
    window.whenFirebase = function (cb) {
      if (window.__fb) return cb(window.__fb);
      window.addEventListener('firebase-ready', function () { cb(window.__fb); }, { once: true });
    };
    // Auth guards
    window.requireAuth = function () {
      window.whenFirebase(function (fb) {
        fb.onAuthStateChanged(fb.auth, function (user) {
          if (!user) { window.location.replace('login.html'); }
        });
      });
    };
    window.redirectIfAuthed = function (dest) {
      window.whenFirebase(function (fb) {
        fb.onAuthStateChanged(fb.auth, function (user) {
          if (user) { window.location.replace(dest || 'dashboard.html'); }
        });
      });
    };
  </script>
'''

# ---------- render_page: inject Firebase into every page ----------
_prev_render_page_1__u2 = render_page

def render_page(path, builder):
    html = _prev_render_page_1__u2(path, builder)
    if "<!-- Firebase v10 modular SDK" not in html and "</head>" in html:
        html = html.replace("</head>", FIREBASE_SCRIPT + "\n</head>", 1)
    return html


# ---------- header: signed-in Dashboard button ----------
_prev_render_header_2__u4 = render_header

def render_header(ctx, current_page=""):
    html = _prev_render_header_2__u4(ctx, current_page)
    # Add a script that flips "Sign in"/"Try for free" to "Dashboard" when authed.
    swap = '''
    <script>
      window.whenFirebase && window.whenFirebase(function (fb) {
        fb.onAuthStateChanged(fb.auth, function (user) {
          var login  = document.querySelector('a[href$="login.html"].px-2');
          var signup = document.querySelector('a[href$="signup.html"].btn-primary, a[href$="signup.html"][class*="btn-primary"]');
          if (user) {
            if (login)  login.style.display = 'none';
            if (signup) {
              signup.textContent = 'Dashboard';
              signup.setAttribute('href', 'Pages/dashboard.html');
            }
          }
        });
      });
    </script>'''
    if "</header>" in html and "whenFirebase && window.whenFirebase" not in html:
        html = html.replace("</header>", swap + "\n</header>", 1)
    return html


# ---------- shared default system prompt ----------
DEFAULT_PROMPT = (
    "You are Solana, a friendly AI receptionist. Keep replies short and "
    "helpful. Greet the caller warmly, capture their name and reason for "
    "calling, and confirm any appointment back to them."
)


# ---------- login page ----------
LOGIN_BODY = '''
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-16 lg:py-24 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div class="lg:col-span-6 flex flex-col justify-center">
            <span class="inline-flex self-start items-center rounded-full bg-[#111111] border border-[#111111] px-3.5 py-1.5 text-[13px] font-semibold text-white">Welcome back</span>
            <h1 class="mt-5 text-4xl sm:text-5xl lg:text-[52px] font-bold leading-[1.08] tracking-[-0.035em] text-[#111111]">Sign in to Vocallus</h1>
            <p class="mt-6 text-[17px] sm:text-[18px] leading-[1.58] text-[#55565B] max-w-[520px]">Pick up right where you left off.</p>
          </div>
          <div class="lg:col-span-6 flex justify-center lg:justify-end">
            <div class="w-full max-w-[460px] rounded-3xl border border-neutral-100 bg-white p-8 sm:p-10 shadow-sm">
              <button type="button" id="google-signin" class="w-full inline-flex items-center justify-center gap-2.5 rounded-xl border border-neutral-200 bg-white px-6 py-3.5 font-bold text-[16px] text-neutral-800 shadow-xs hover:bg-neutral-50 transition mb-5">
                <img src="../Images/gicon.png" alt="" class="h-5 w-5">
                Sign in with Google
              </button>
              <div class="flex items-center gap-3 mb-5">
                <div class="flex-1 h-px bg-neutral-200"></div>
                <span class="text-[12px] font-semibold text-neutral-400 uppercase tracking-wider">or</span>
                <div class="flex-1 h-px bg-neutral-200"></div>
              </div>
              <form id="login-form" class="space-y-5" novalidate>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Email</span>
                  <input type="email" name="email" placeholder="you@company.com" required autocomplete="email" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Password</span>
                  <input type="password" name="password" placeholder="********" required autocomplete="current-password" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <div id="login-error" class="hidden rounded-xl bg-red-50 border border-red-200 p-3.5 text-[13.5px] text-red-700"></div>
                <button type="submit" class="btn-primary w-full inline-flex items-center justify-center px-6 py-3.5 rounded-xl font-bold text-[16px] shadow-sm">Sign in</button>
              </form>
              <p class="mt-6 text-center text-[13.5px] text-neutral-500">
                New to Vocallus? <a href="signup.html" class="font-semibold text-[#111111] hover:underline">Try for free</a>
              </p>
            </div>
          </div>
        </div>
      </div>
'''

LOGIN_JS = '''
  <script>
    window.redirectIfAuthed && window.redirectIfAuthed('dashboard.html');
    window.whenFirebase && window.whenFirebase(function (fb) {
      var errEl = document.getElementById('login-error');
      function showErr(msg) { errEl.textContent = msg; errEl.classList.remove('hidden'); }
      function hideErr() { errEl.classList.add('hidden'); }

      document.getElementById('google-signin').addEventListener('click', function () {
        hideErr();
        var provider = new fb.GoogleAuthProvider();
        fb.signInWithPopup(fb.auth, provider)
          .then(function () { window.location.href = 'dashboard.html'; })
          .catch(function (e) { showErr(e.message || String(e)); });
      });

      document.getElementById('login-form').addEventListener('submit', function (e) {
        e.preventDefault();
        hideErr();
        var email = this.email.value.trim();
        var pw = this.password.value;
        fb.signInWithEmailAndPassword(fb.auth, email, pw)
          .then(function () { window.location.href = 'dashboard.html'; })
          .catch(function (e) { showErr(e.message || String(e)); });
      });
    });
  </script>
'''

def page_login(ctx):
    return "Sign in", "Sign in to your Vocallus inbox.", LOGIN_BODY, ""


# ---------- signup page ----------
SIGNUP_BODY = '''
      <div class="max-w-[1400px] mx-auto px-6 lg:px-12 py-16 lg:py-24 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div class="lg:col-span-6 flex flex-col justify-center">
            <span class="inline-flex self-start items-center rounded-full bg-[#111111] border border-[#111111] px-3.5 py-1.5 text-[13px] font-semibold text-white">Free demo</span>
            <h1 class="mt-5 text-4xl sm:text-5xl lg:text-[52px] font-bold leading-[1.08] tracking-[-0.035em] text-[#111111]">Try Vocallus free</h1>
            <p class="mt-6 text-[17px] sm:text-[18px] leading-[1.58] text-[#55565B] max-w-[520px]">Set up Solana in minutes.</p>
          </div>
          <div class="lg:col-span-6 flex justify-center lg:justify-end">
            <div class="w-full max-w-[460px] rounded-3xl border border-neutral-100 bg-white p-8 sm:p-10 shadow-sm">
              <button type="button" id="google-signup" class="w-full inline-flex items-center justify-center gap-2.5 rounded-xl border border-neutral-200 bg-white px-6 py-3.5 font-bold text-[16px] text-neutral-800 shadow-xs hover:bg-neutral-50 transition mb-5">
                <img src="../Images/gicon.png" alt="" class="h-5 w-5">
                Sign up with Google
              </button>
              <div class="flex items-center gap-3 mb-5">
                <div class="flex-1 h-px bg-neutral-200"></div>
                <span class="text-[12px] font-semibold text-neutral-400 uppercase tracking-wider">or</span>
                <div class="flex-1 h-px bg-neutral-200"></div>
              </div>
              <form id="signup-form" class="space-y-5" novalidate>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Full name</span>
                  <input type="text" name="name" placeholder="Jordan Rivera" required autocomplete="name" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Email</span>
                  <input type="email" name="email" placeholder="you@company.com" required autocomplete="email" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Company</span>
                  <input type="text" name="company" placeholder="Acme Services" required autocomplete="organization" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <label class="block">
                  <span class="block text-[13.5px] font-semibold text-[#111111] mb-1.5">Password</span>
                  <input type="password" name="password" placeholder="At least 6 characters" required minlength="6" autocomplete="new-password" class="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-[15px] outline-none focus:border-neutral-500 focus:ring-4 focus:ring-neutral-100">
                </label>
                <div id="signup-error" class="hidden rounded-xl bg-red-50 border border-red-200 p-3.5 text-[13.5px] text-red-700"></div>
                <button type="submit" class="btn-primary w-full inline-flex items-center justify-center px-6 py-3.5 rounded-xl font-bold text-[16px] shadow-sm">Create my account</button>
              </form>
              <p class="mt-6 text-center text-[13.5px] text-neutral-500">
                Already have an account? <a href="login.html" class="font-semibold text-[#111111] hover:underline">Sign in</a>
              </p>
            </div>
          </div>
        </div>
      </div>
'''

SIGNUP_JS = '''
  <script>
    window.redirectIfAuthed && window.redirectIfAuthed('dashboard.html');
    window.whenFirebase && window.whenFirebase(function (fb) {
      var errEl = document.getElementById('signup-error');
      function showErr(m) { errEl.textContent = m; errEl.classList.remove('hidden'); }
      function hideErr() { errEl.classList.add('hidden'); }

      function ensureUserDoc(user, extra) {
        var ref = fb.doc(fb.db, 'users', user.uid);
        return fb.getDoc(ref).then(function (snap) {
          if (!snap.exists()) {
            var data = Object.assign({
              name: (extra && extra.name) || user.displayName || '',
              email: user.email || '',
              company: (extra && extra.company) || '',
              plan: 'none',
              agentName: 'Solana',
              systemPrompt: 'You are Solana, a friendly AI receptionist. Keep replies short and helpful. Greet the caller warmly, capture their name and reason for calling, and confirm any appointment back to them.',
              createdAt: fb.serverTimestamp()
            }, {});
            return fb.setDoc(ref, data);
          }
          return Promise.resolve();
        });
      }

      document.getElementById('google-signup').addEventListener('click', function () {
        hideErr();
        var provider = new fb.GoogleAuthProvider();
        fb.signInWithPopup(fb.auth, provider)
          .then(function (res) { return ensureUserDoc(res.user); })
          .then(function () { window.location.href = 'dashboard.html'; })
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
          .then(function () { window.location.href = 'dashboard.html'; })
          .catch(function (e) { showErr(e.message || String(e)); });
      });
    });
  </script>
'''

def page_signup(ctx):
    return "Sign up", "Try Vocallus free.", SIGNUP_BODY, ""


# ---------- Solana page (working chat, Firestore) ----------
SOLANA_BODY_TPL_NEW = '''{sidebar}
    <aside class="w-[320px] bg-[#f9fafb] border-r border-gray-200 flex flex-col flex-shrink-0">
        <div class="p-5 border-b border-gray-200">
            <div class="flex items-center gap-3 mb-2">
                <img src="../Images/logo.png" alt="" class="w-11 h-11 rounded-2xl">
                <div class="flex-1">
                    <div class="font-semibold text-[15px] text-gray-900" id="agent-name-display">Solana</div>
                    <div class="text-[12px] text-gray-500">AI receptionist</div>
                </div>
            </div>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
            <div>
                <label class="block text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-2">Agent name</label>
                <input id="agent-name" type="text" placeholder="Solana" class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[14px] focus:outline-none focus:border-gray-400 bg-white">
            </div>
            <div>
                <label class="block text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-2">System prompt</label>
                <p class="text-[12px] text-gray-400 mb-2">How your agent should greet and respond.</p>
                <textarea id="system-prompt" rows="11" placeholder="You are Solana..." class="w-full rounded-xl border border-gray-200 px-3.5 py-2.5 text-[13.5px] leading-[1.6] focus:outline-none focus:border-gray-400 bg-white resize-none"></textarea>
            </div>
            <button id="save-prompt" class="w-full btn-primary rounded-xl py-3 font-semibold text-[14px]">Save changes</button>
        </div>
    </aside>

    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl border-l border-gray-200">
        <div class="max-w-[1100px] mx-auto px-8 py-8">
            <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
                <div>
                    <h1 class="text-[26px] font-semibold text-gray-900">Test your Solana</h1>
                    <p class="text-gray-500 text-[14px] mt-0.5">Try your agent before connecting a phone number.</p>
                </div>
                <div class="flex bg-gray-100 rounded-full p-1">
                    <button data-mode="call" class="mode-btn px-5 py-2 rounded-full text-[14px] font-semibold bg-white shadow-sm text-gray-900">Call</button>
                    <button data-mode="text" class="mode-btn px-5 py-2 rounded-full text-[14px] font-medium text-gray-500">Text</button>
                </div>
            </div>

            <div id="api-setup" class="rounded-3xl border border-gray-100 p-7 mb-8 bg-[#f9fafb]">
                <div class="mb-6">
                    <h2 class="text-[18px] font-semibold text-gray-900">Connect an AI provider</h2>
                    <p class="text-[14px] text-gray-500 mt-1">Gemini is required for phone calls.</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6" id="provider-grid">
                    <button data-provider="openai" class="provider-card rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/cha.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">OpenAI</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">GPT models</div>
                    </button>
                    <button data-provider="gemini" class="provider-card rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/gem.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">Gemini <span class="ml-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">Required for phone calls</span></div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Google models</div>
                    </button>
                    <button data-provider="claude" class="provider-card rounded-2xl border-2 border-gray-200 bg-white p-4 hover:border-gray-300 transition text-left">
                        <img src="../Images/cla.png" alt="" class="w-8 h-8 rounded-lg mb-3">
                        <div class="text-[14px] font-semibold text-gray-900">Claude</div>
                        <div class="text-[12px] text-gray-500 mt-0.5">Anthropic models</div>
                    </button>
                </div>

                <div class="mb-5">
                    <label class="block text-[13px] font-semibold text-gray-700 mb-2">API key</label>
                    <input id="api-key" type="password" placeholder="Paste your API key" class="w-full rounded-xl border border-gray-200 px-3.5 py-3 text-[14px] focus:outline-none focus:border-gray-400 bg-white">
                    <p id="key-hint" class="text-[12px] text-gray-400 mt-1.5">Pick a provider to see the expected key format.</p>
                    <div id="key-saved" class="hidden mt-3 flex items-center justify-between rounded-xl bg-white border border-gray-200 px-4 py-3">
                        <div>
                            <div class="text-[12px] font-semibold text-gray-500 uppercase tracking-wide">Saved key</div>
                            <div id="key-masked" class="text-[14px] font-mono text-gray-900 mt-0.5">----</div>
                        </div>
                        <button id="key-replace" class="text-[13px] font-semibold text-gray-700 underline hover:text-black">Replace key</button>
                    </div>
                </div>

                <div id="api-error" class="hidden rounded-xl bg-red-50 border border-red-200 p-4 mb-5">
                    <div class="flex items-start gap-3">
                        <svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                        <div>
                            <div id="api-error-title" class="text-[14px] font-semibold text-red-800">Error</div>
                            <div id="api-error-msg" class="text-[13px] text-red-700 mt-1"></div>
                        </div>
                    </div>
                </div>

                <button id="save-key" class="btn-primary px-6 py-3 rounded-xl font-semibold text-[14px]">Save and continue</button>
            </div>

            <div class="rounded-2xl border border-gray-100 bg-[#f9fafb] p-5 mb-8">
                <div class="text-[12px] font-semibold uppercase tracking-wide text-gray-500 mb-1">Your Solana number</div>
                <div id="solana-number" class="text-[16px] font-semibold text-gray-900">Loading&hellip;</div>
            </div>

            <div id="chat-preview" class="rounded-3xl border border-gray-100 bg-[#f9fafb] p-7">
                <div id="call-view">
                    <div class="text-center py-10">
                        <img src="../Images/logo.png" alt="" class="w-20 h-20 mx-auto rounded-3xl mb-4">
                        <div class="text-[22px] font-semibold text-gray-900">Test call</div>
                        <div class="text-[14px] text-gray-500 mt-1.5">Phone calls launch after you subscribe.</div>
                        <button id="start-call" class="mt-8 btn-primary inline-flex items-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-[14px]">
                            Start test call
                        </button>
                    </div>
                </div>
                <div id="text-view" class="hidden">
                    <div class="space-y-4 mb-6" id="chat-log"></div>
                    <div class="flex items-center gap-3">
                        <input id="chat-input" type="text" placeholder="Type a message to test your Solana" class="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-[14px] focus:outline-none focus:border-gray-400">
                        <button id="chat-send" class="btn-primary px-5 py-3 rounded-xl font-semibold text-[14px]">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </main>'''


SOLANA_JS = '''
  <script>
    window.requireAuth && window.requireAuth();
    window.whenFirebase && window.whenFirebase(function (fb) {
      var PROVIDERS = {
        openai: { name:'OpenAI', keyPrefixes:['sk-'], hint:'OpenAI keys start with "sk-".' },
        gemini: { name:'Gemini', keyPrefixes:['AIza','AQ.'], hint:'Gemini keys start with "AIza" or "AQ.".' },
        claude: { name:'Claude', keyPrefixes:['sk-ant-'], hint:'Claude keys start with "sk-ant-".' }
      };
      var uid = null, currentProvider = null;
      var $ = function (id) { return document.getElementById(id); };

      var providerBtns = document.querySelectorAll('.provider-card');
      var keyInput = $('api-key'), keyHint = $('key-hint');
      var errBox = $('api-error'), errTitle = $('api-error-title'), errMsg = $('api-error-msg');
      var setupCard = $('api-setup'), preview = $('chat-preview');
      var savedBox = $('key-saved'), masked = $('key-masked'), replaceBtn = $('key-replace');

      function showErr(t, m) { errTitle.textContent = t; errMsg.textContent = m; errBox.classList.remove('hidden'); }
      function hideErr() { errBox.classList.add('hidden'); }
      function maskKey(k) { return k.slice(0,4) + '••••••' + k.slice(-4); }

      function selectProvider(id) {
        currentProvider = id;
        var p = PROVIDERS[id];
        providerBtns.forEach(function (b) {
          var on = b.dataset.provider === id;
          b.classList.toggle('border-black', on);
          b.classList.toggle('ring-2', on);
          b.classList.toggle('ring-black/10', on);
          b.classList.toggle('border-gray-200', !on);
        });
        keyHint.textContent = p.hint;
        hideErr();
      }

      providerBtns.forEach(function (b) {
        b.addEventListener('click', function () { selectProvider(b.dataset.provider); });
      });

      function loadUser() {
        return fb.getDoc(fb.doc(fb.db, 'users', uid)).then(function (snap) {
          if (!snap.exists()) return;
          var d = snap.data();
          if (d.agentName) { $('agent-name').value = d.agentName; $('agent-name-display').textContent = d.agentName; }
          if (d.systemPrompt) $('system-prompt').value = d.systemPrompt;
          $('solana-number').textContent = d.phoneNumber || 'No number yet — one is assigned after you subscribe.';
        });
      }
      function loadKey() {
        return fb.getDoc(fb.doc(fb.db, 'users', uid, 'private', 'ai')).then(function (snap) {
          if (!snap.exists()) return;
          var d = snap.data();
          if (d && d.provider) {
            selectProvider(d.provider);
            keyInput.value = '';
            masked.textContent = maskKey(d.apiKey || '');
            savedBox.classList.remove('hidden');
            keyInput.style.display = 'none';
          }
        });
      }

      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) return;
        uid = user.uid;
        loadUser();
        loadKey();
      });

      $('save-prompt').addEventListener('click', function () {
        if (!uid) return;
        var btn = this; btn.textContent = 'Saving…';
        fb.updateDoc(fb.doc(fb.db, 'users', uid), {
          agentName: $('agent-name').value.trim() || 'Solana',
          systemPrompt: $('system-prompt').value.trim()
        }).then(function () {
          btn.textContent = 'Saved';
          setTimeout(function () { btn.textContent = 'Save changes'; }, 1200);
        }).catch(function (e) { btn.textContent = 'Save changes'; showErr('Save failed', e.message); });
      });

      $('agent-name').addEventListener('input', function () {
        $('agent-name-display').textContent = this.value || 'Solana';
      });

      $('save-key').addEventListener('click', function () {
        hideErr();
        if (!uid) { showErr('Not signed in', 'Please sign in again.'); return; }
        var key = keyInput.value.trim();
        if (!currentProvider) { showErr('No provider selected', 'Pick a provider above.'); return; }
        var p = PROVIDERS[currentProvider];
        var ok = p.keyPrefixes.some(function (pre) { return key.indexOf(pre) === 0; });
        if (key.length < 8 || !ok) { showErr('Invalid API key', p.hint); return; }
        var model = currentProvider === 'gemini' ? 'gemini-2.5-flash'
                  : currentProvider === 'openai' ? 'gpt-4o-mini'
                  : 'claude-3-5-haiku-20241022';
        fb.setDoc(fb.doc(fb.db, 'users', uid, 'private', 'ai'), {
          provider: currentProvider, apiKey: key, model: model
        }).then(function () {
          masked.textContent = maskKey(key);
          savedBox.classList.remove('hidden');
          keyInput.value = '';
          keyInput.style.display = 'none';
        }).catch(function (e) { showErr('Could not save key', e.message); });
      });

      replaceBtn.addEventListener('click', function () {
        savedBox.classList.add('hidden');
        keyInput.style.display = '';
        keyInput.focus();
      });

      /* ---- Text chat ---- */
      var chatLog = $('chat-log'), chatInput = $('chat-input'), chatSend = $('chat-send');
      var history = [];

      function bubble(role, text) {
        var el = document.createElement('div');
        el.className = role === 'user' ? 'flex justify-end' : 'flex items-start gap-3';
        el.innerHTML = role === 'user'
          ? '<div class="bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[70%]"><p class="text-[14px] leading-[1.5]"></p></div>'
          : '<img src="../Images/logo.png" alt="" class="w-8 h-8 rounded-xl flex-shrink-0"><div class="bg-white rounded-2xl rounded-tl-sm border border-gray-100 px-4 py-3 max-w-[70%]"><p class="text-[14px] text-gray-800 leading-[1.5]"></p></div>';
        el.querySelector('p').textContent = text;
        chatLog.appendChild(el);
        chatLog.scrollTop = chatLog.scrollHeight;
        return el;
      }

      function send() {
        var text = (chatInput.value || '').trim();
        if (!text || !uid) return;
        chatInput.value = '';
        bubble('user', text);
        var thinking = bubble('assistant', '…');
        history.push({ role: 'user', content: text });

        var keySnap, promptVal, agentName;
        Promise.all([
          fb.getDoc(fb.doc(fb.db, 'users', uid, 'private', 'ai')),
          fb.getDoc(fb.doc(fb.db, 'users', uid))
        ]).then(function (arr) {
          var keyDoc = arr[0], userDoc = arr[1];
          if (!keyDoc.exists()) throw new Error('No API key saved. Add one above.');
          var kd = keyDoc.data();
          if (kd.provider !== 'gemini') throw new Error('Text test only works with Gemini. Save a Gemini key.');
          var ud = userDoc.exists() ? userDoc.data() : {};
          promptVal = ud.systemPrompt || 'You are Solana, a friendly AI receptionist.';
          agentName = ud.agentName || 'Solana';

          var url = 'https://generativelanguage.googleapis.com/v1beta/models/' +
                    (kd.model || 'gemini-2.5-flash') + ':generateContent?key=' +
                    encodeURIComponent(kd.apiKey);

          var body = {
            systemInstruction: { parts: [{ text: promptVal }] },
            contents: history.map(function (m) {
              return { role: m.role === 'user' ? 'user' : 'model', parts: [{ text: m.content }] };
            })
          };
          return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
          }).then(function (r) { return r.json(); });
        }).then(function (j) {
          var t = j.candidates && j.candidates[0] && j.candidates[0].content
               && j.candidates[0].content.parts && j.candidates[0].content.parts[0].text;
          if (!t) throw new Error((j.error && j.error.message) || 'No reply from Gemini.');
          thinking.querySelector('p').textContent = t;
          history.push({ role: 'assistant', content: t });
        }).catch(function (e) {
          thinking.querySelector('p').textContent = 'Error: ' + (e.message || e);
        });
      }
      chatSend.addEventListener('click', send);
      chatInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') send(); });

      /* ---- Call / Text toggle ---- */
      document.querySelectorAll('.mode-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var mode = btn.dataset.mode;
          document.querySelectorAll('.mode-btn').forEach(function (b) {
            var on = b.dataset.mode === mode;
            b.classList.toggle('bg-white', on); b.classList.toggle('shadow-sm', on);
            b.classList.toggle('text-gray-900', on); b.classList.toggle('font-semibold', on);
            b.classList.toggle('text-gray-500', !on); b.classList.toggle('font-medium', !on);
          });
          $('call-view').classList.toggle('hidden', mode !== 'call');
          $('text-view').classList.toggle('hidden', mode !== 'text');
        });
      });

      /* ---- Sign out ---- */
      var so = document.getElementById('signout-btn');
      if (so) so.addEventListener('click', function () {
        fb.signOut(fb.auth).then(function () { window.location.href = 'login.html'; });
      });
    });
  </script>
'''

def page_solana(_ctx):
    body = SOLANA_BODY_TPL_NEW.replace("{sidebar}", _render_sidebar("solana"))
    return "Solana", "Configure and test your Solana agent.", body, ""


# ---------- Calendar page ----------
CALENDAR_BODY = '''{sidebar}
    <main class="flex-1 overflow-y-auto custom-scrollbar bg-white relative rounded-tl-3xl border-l border-gray-200">
        <div class="max-w-[1200px] mx-auto px-8 py-8">
            <div class="flex items-center justify-between mb-6 flex-wrap gap-4">
                <div>
                    <h1 class="text-[26px] font-semibold text-gray-900">Calendar</h1>
                    <p class="text-gray-500 text-[14px] mt-0.5">Bookings from Solana and manual appointments.</p>
                </div>
                <div class="flex items-center gap-2">
                    <button id="prev-week" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13.5px] font-medium hover:bg-gray-50">Prev</button>
                    <button id="today-btn" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13.5px] font-medium hover:bg-gray-50">Today</button>
                    <button id="next-week" class="px-3.5 py-2 rounded-lg border border-gray-200 text-[13.5px] font-medium hover:bg-gray-50">Next</button>
                </div>
            </div>

            <div class="flex items-center gap-2 mb-6">
                <button data-view="week" class="view-btn px-4 py-2 rounded-lg text-[13.5px] font-semibold bg-black text-white">Week</button>
                <button data-view="list" class="view-btn px-4 py-2 rounded-lg text-[13.5px] font-medium border border-gray-200">Upcoming</button>
                <div id="week-label" class="ml-auto text-[14px] font-medium text-gray-700"></div>
            </div>

            <div id="week-view">
                <div class="overflow-x-auto rounded-2xl border border-gray-100">
                    <table class="w-full min-w-[900px] table-fixed border-collapse">
                        <thead><tr id="cal-head" class="bg-[#f9fafb]"></tr></thead>
                        <tbody id="cal-body"></tbody>
                    </table>
                </div>
            </div>

            <div id="list-view" class="hidden">
                <div id="upcoming-list" class="space-y-3"></div>
            </div>

            <div class="mt-8 rounded-2xl border border-gray-100 bg-[#f9fafb] p-6">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-[16px] font-semibold text-gray-900">Business hours</h2>
                    <div class="text-[13px] text-gray-500">Slot length: <span id="slot-length">30</span> min</div>
                </div>
                <div id="hours-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"></div>
                <button id="save-hours" class="mt-4 btn-primary px-5 py-2.5 rounded-xl font-semibold text-[13.5px]">Save hours</button>
            </div>
        </div>
    </main>

    <div id="modal" class="hidden fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl">
            <div class="flex items-center justify-between mb-4">
                <h3 id="modal-title" class="text-[18px] font-semibold text-gray-900">New appointment</h3>
                <button id="modal-close" class="text-gray-400 hover:text-gray-700 text-xl leading-none">×</button>
            </div>
            <form id="appt-form" class="space-y-4">
                <label class="block">
                    <span class="block text-[13px] font-semibold text-gray-700 mb-1">Title</span>
                    <input name="title" required class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]">
                </label>
                <label class="block">
                    <span class="block text-[13px] font-semibold text-gray-700 mb-1">Customer name</span>
                    <input name="customerName" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]">
                </label>
                <label class="block">
                    <span class="block text-[13px] font-semibold text-gray-700 mb-1">Customer phone</span>
                    <input name="customerPhone" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]">
                </label>
                <div class="grid grid-cols-2 gap-3">
                    <label class="block">
                        <span class="block text-[13px] font-semibold text-gray-700 mb-1">Start</span>
                        <input type="datetime-local" name="start" required class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]">
                    </label>
                    <label class="block">
                        <span class="block text-[13px] font-semibold text-gray-700 mb-1">End</span>
                        <input type="datetime-local" name="end" required class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]">
                    </label>
                </div>
                <label class="block">
                    <span class="block text-[13px] font-semibold text-gray-700 mb-1">Notes</span>
                    <textarea name="notes" rows="2" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-[14px]"></textarea>
                </label>
                <div class="flex items-center justify-between gap-3 pt-2">
                    <button type="button" id="appt-delete" class="hidden text-[13.5px] font-semibold text-red-600 hover:underline">Delete</button>
                    <div class="flex items-center gap-2 ml-auto">
                        <button type="button" id="modal-cancel" class="px-4 py-2 rounded-lg border border-gray-200 text-[13.5px] font-medium">Cancel</button>
                        <button type="submit" class="btn-primary px-5 py-2 rounded-lg font-semibold text-[13.5px]">Save</button>
                    </div>
                </div>
            </form>
        </div>
    </div>'''

CALENDAR_JS = '''
  <script>
    window.requireAuth && window.requireAuth();
    window.whenFirebase && window.whenFirebase(function (fb) {
      var uid = null;
      var currentWeekStart = startOfWeek(new Date());
      var appts = [];
      var hours = defaultHours();
      var slotMin = 30;
      var editingId = null;
      var $ = function (id) { return document.getElementById(id); };

      function startOfWeek(d) {
        var x = new Date(d); x.setHours(0,0,0,0);
        var day = x.getDay();
        var diff = day === 0 ? -6 : 1 - day;
        x.setDate(x.getDate() + diff);
        return x;
      }
      function addDays(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }
      function fmtDay(d) { return d.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' }); }
      function pad(n) { return (n < 10 ? '0' : '') + n; }
      function toLocalInput(d) { return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+'T'+pad(d.getHours())+':'+pad(d.getMinutes()); }
      function defaultHours() {
        var w = { closed:false, open:'09:00', close:'17:00' };
        var c = { closed:true,  open:'09:00', close:'17:00' };
        return { mon:w, tue:w, wed:w, thu:w, fri:w, sat:c, sun:c };
      }

      var DAYS = ['mon','tue','wed','thu','fri','sat','sun'];

      function renderHead() {
        var head = $('cal-head');
        head.innerHTML = '<th class="w-[80px] py-3 text-[12px] font-semibold text-gray-500 border-b border-gray-200"></th>';
        for (var i = 0; i < 7; i++) {
          var d = addDays(currentWeekStart, i);
          var th = document.createElement('th');
          th.className = 'py-3 text-[12px] font-semibold text-gray-700 border-b border-l border-gray-200';
          th.textContent = fmtDay(d);
          head.appendChild(th);
        }
        var end = addDays(currentWeekStart, 6);
        $('week-label').textContent = currentWeekStart.toLocaleDateString('en-US', { month:'short', day:'numeric' }) + ' – ' + end.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
      }

      function renderBody() {
        var body = $('cal-body');
        body.innerHTML = '';
        for (var h = 7; h < 20; h++) {
          for (var m = 0; m < 60; m += slotMin) {
            var tr = document.createElement('tr');
            var timeCell = document.createElement('td');
            timeCell.className = 'text-[11px] text-gray-400 align-top py-2 pl-2 border-b border-gray-100 w-[80px]';
            timeCell.textContent = (m === 0) ? (h + ':00') : '';
            tr.appendChild(timeCell);

            for (var d = 0; d < 7; d++) {
              var day = addDays(currentWeekStart, d);
              var slotStart = new Date(day); slotStart.setHours(h, m, 0, 0);
              var slotEnd = new Date(slotStart); slotEnd.setMinutes(slotEnd.getMinutes() + slotMin);

              var key = DAYS[d];
              var isClosed = hours[key] && hours[key].closed;
              var td = document.createElement('td');
              td.className = 'align-top border-b border-l border-gray-100 relative h-[38px] cursor-pointer hover:bg-gray-50 ' + (isClosed ? 'bg-gray-50' : '');
              td.dataset.start = slotStart.toISOString();
              td.dataset.end = slotEnd.toISOString();

              var match = appts.find(function (a) {
                return a.start && a.end && new Date(a.start) < slotEnd && new Date(a.end) > slotStart;
              });
              if (match) {
                td.classList.remove('cursor-pointer', 'hover:bg-gray-50');
                var chip = document.createElement('div');
                chip.className = 'absolute inset-x-1 top-0.5 rounded-md bg-black text-white text-[11px] px-2 py-1 truncate cursor-pointer';
                chip.textContent = match.title || 'Appointment';
                chip.title = match.title || '';
                chip.addEventListener('click', function (e) { e.stopPropagation(); openEdit(match.id); });
                td.appendChild(chip);
                if (match.source === 'ai') {
                  var badge = document.createElement('span');
                  badge.className = 'absolute right-1 bottom-0.5 text-[9px] font-semibold uppercase tracking-wider text-white bg-green-600 rounded px-1';
                  badge.textContent = 'AI';
                  td.appendChild(badge);
                }
              }
              tr.appendChild(td);
            }
            body.appendChild(tr);
          }
        }
      }

      function renderList() {
        var wrap = $('upcoming-list');
        wrap.innerHTML = '';
        var now = new Date();
        var upcoming = appts.filter(function (a) { return new Date(a.start) >= now; })
                            .sort(function (a, b) { return new Date(a.start) - new Date(b.start); });
        if (!upcoming.length) {
          wrap.innerHTML = '<div class="py-16 text-center text-gray-400 text-[15px]">No upcoming appointments.</div>';
          return;
        }
        upcoming.forEach(function (a) {
          var row = document.createElement('div');
          row.className = 'rounded-2xl border border-gray-100 bg-white p-5 hover:shadow-sm transition cursor-pointer flex items-start gap-4';
          row.innerHTML =
            '<div class="w-10 h-10 rounded-xl bg-black flex items-center justify-center flex-shrink-0">' +
              '<svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' +
            '</div>' +
            '<div class="flex-1">' +
              '<div class="flex items-center gap-2 flex-wrap">' +
                '<div class="font-semibold text-[15px] text-gray-900"></div>' +
                (a.source === 'ai' ? '<span class="text-[10px] font-bold uppercase tracking-wider text-white bg-green-600 rounded px-1.5 py-0.5">Booked by Solana</span>' : '') +
                '<div class="text-[12px] text-gray-400 ml-auto">' + new Date(a.start).toLocaleString() + '</div>' +
              '</div>' +
              '<p class="text-[13.5px] text-gray-600 mt-1"></p>' +
            '</div>';
          row.querySelector('div.font-semibold').textContent = a.title || 'Appointment';
          row.querySelector('p').textContent = (a.customerName || '') + (a.customerPhone ? ' · ' + a.customerPhone : '');
          row.addEventListener('click', function () { openEdit(a.id); });
          wrap.appendChild(row);
        });
      }

      function renderHours() {
        var grid = $('hours-grid');
        grid.innerHTML = '';
        DAYS.forEach(function (k) {
          var h = hours[k] || { closed:true, open:'09:00', close:'17:00' };
          var cell = document.createElement('div');
          cell.className = 'rounded-xl border border-gray-200 bg-white p-3';
          cell.innerHTML =
            '<div class="flex items-center justify-between mb-2">' +
              '<span class="text-[12.5px] font-semibold uppercase tracking-wide text-gray-600">' + k + '</span>' +
              '<label class="inline-flex items-center gap-1.5 text-[12px] text-gray-500">' +
                '<input type="checkbox" data-day="'+k+'" data-field="closed" ' + (h.closed ? 'checked' : '') + ' class="rounded">' +
                'Closed' +
              '</label>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-2">' +
              '<input type="time" data-day="'+k+'" data-field="open" value="'+h.open+'" ' + (h.closed ? 'disabled' : '') + ' class="rounded-lg border border-gray-200 px-2 py-1.5 text-[12.5px]">' +
              '<input type="time" data-day="'+k+'" data-field="close" value="'+h.close+'" ' + (h.closed ? 'disabled' : '') + ' class="rounded-lg border border-gray-200 px-2 py-1.5 text-[12.5px]">' +
            '</div>';
          grid.appendChild(cell);
        });
        grid.querySelectorAll('input').forEach(function (inp) {
          inp.addEventListener('change', function () {
            var d = inp.dataset.day, f = inp.dataset.field;
            if (!hours[d]) hours[d] = { open:'09:00', close:'17:00', closed:false };
            hours[d][f] = (inp.type === 'checkbox') ? inp.checked : inp.value;
            renderHours();
          });
        });
      }

      function openNew(startISO, endISO) {
        editingId = null;
        $('modal-title').textContent = 'New appointment';
        $('appt-delete').classList.add('hidden');
        var f = $('appt-form'); f.reset();
        if (startISO) f.start.value = toLocalInput(new Date(startISO));
        if (endISO)   f.end.value   = toLocalInput(new Date(endISO));
        $('modal').classList.remove('hidden');
      }
      function openEdit(id) {
        var a = appts.find(function (x) { return x.id === id; });
        if (!a) return;
        editingId = id;
        $('modal-title').textContent = 'Edit appointment';
        $('appt-delete').classList.remove('hidden');
        var f = $('appt-form');
        f.title.value = a.title || '';
        f.customerName.value = a.customerName || '';
        f.customerPhone.value = a.customerPhone || '';
        f.start.value = toLocalInput(new Date(a.start));
        f.end.value = toLocalInput(new Date(a.end));
        f.notes.value = a.notes || '';
        $('modal').classList.remove('hidden');
      }
      function closeModal() { $('modal').classList.add('hidden'); editingId = null; }

      $('modal-close').addEventListener('click', closeModal);
      $('modal-cancel').addEventListener('click', closeModal);
      $('modal').addEventListener('click', function (e) { if (e.target === $('modal')) closeModal(); });

      $('appt-form').addEventListener('submit', function (e) {
        e.preventDefault();
        if (!uid) return;
        var f = e.target;
        var data = {
          title: f.title.value.trim(),
          customerName: f.customerName.value.trim(),
          customerPhone: f.customerPhone.value.trim(),
          start: new Date(f.start.value),
          end: new Date(f.end.value),
          notes: f.notes.value.trim()
        };
        if (editingId) {
          fb.updateDoc(fb.doc(fb.db, 'users', uid, 'appointments', editingId), data)
            .then(closeModal);
        } else {
          data.source = 'manual';
          data.createdAt = fb.serverTimestamp();
          fb.addDoc(fb.collection(fb.db, 'users', uid, 'appointments'), data)
            .then(closeModal);
        }
      });

      $('appt-delete').addEventListener('click', function () {
        if (!uid || !editingId) return;
        fb.deleteDoc(fb.doc(fb.db, 'users', uid, 'appointments', editingId))
          .then(closeModal);
      });

      $('prev-week').addEventListener('click', function () { currentWeekStart = addDays(currentWeekStart, -7); renderHead(); renderBody(); });
      $('next-week').addEventListener('click', function () { currentWeekStart = addDays(currentWeekStart, 7); renderHead(); renderBody(); });
      $('today-btn').addEventListener('click', function () { currentWeekStart = startOfWeek(new Date()); renderHead(); renderBody(); });

      document.querySelectorAll('.view-btn').forEach(function (b) {
        b.addEventListener('click', function () {
          var v = b.dataset.view;
          document.querySelectorAll('.view-btn').forEach(function (x) {
            var on = x.dataset.view === v;
            x.classList.toggle('bg-black', on); x.classList.toggle('text-white', on);
            x.classList.toggle('font-semibold', on);
            x.classList.toggle('border', !on); x.classList.toggle('border-gray-200', !on);
            x.classList.toggle('font-medium', !on);
          });
          $('week-view').classList.toggle('hidden', v !== 'week');
          $('list-view').classList.toggle('hidden', v !== 'list');
          if (v === 'list') renderList();
        });
      });

      $('cal-body').addEventListener('click', function (e) {
        var td = e.target.closest('td');
        if (!td || !td.dataset.start) return;
        openNew(td.dataset.start, td.dataset.end);
      });

      $('save-hours').addEventListener('click', function () {
        if (!uid) return;
        fb.updateDoc(fb.doc(fb.db, 'users', uid), { hours: hours, appointmentLength: slotMin });
      });

      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) return;
        uid = user.uid;
        fb.getDoc(fb.doc(fb.db, 'users', uid)).then(function (snap) {
          if (snap.exists()) {
            var d = snap.data();
            if (d.hours) hours = Object.assign(hours, d.hours);
            if (d.appointmentLength) slotMin = d.appointmentLength;
          }
          renderHours();
          renderHead(); renderBody();
          fb.onSnapshot(fb.collection(fb.db, 'users', uid, 'appointments'), function (s) {
            appts = [];
            s.forEach(function (doc) {
              var x = doc.data(); x.id = doc.id;
              x.start = x.start && x.start.toDate ? x.start.toDate() : x.start;
              x.end   = x.end   && x.end.toDate   ? x.end.toDate()   : x.end;
              appts.push(x);
            });
            renderBody();
            if (!$('list-view').classList.contains('hidden')) renderList();
          });
        });
      });
    });
  </script>
'''

def page_calendar(_ctx):
    body = CALENDAR_BODY.replace("{sidebar}", _render_sidebar("calendar"))
    return "Calendar", "Your Vocallus appointment calendar.", body, ""


# ---------- extend the sidebar to include Calendar ----------
_SIDEBAR_TPL = SIDEBAR_TPL
def _render_sidebar(active):
    html = _SIDEBAR_TPL
    # Insert Calendar between Solana and Number if missing
    if 'data-nav="calendar"' not in html:
        solana_block = re.search(r'(\s*<a href="solana\.html".*?</a>\s*)', html, re.DOTALL)
        if solana_block:
            cal = (
                '\n                <a href="calendar.html" data-nav="calendar" class="app-tab relative flex flex-col items-center justify-center w-full py-2.5 rounded-xl transition-colors __CALENDAR_CLS__">\n'
                '                    <div class="app-bar absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gray-900 rounded-r-full transition-opacity __CALENDAR_BAR__"></div>\n'
                '                    <svg class="w-5 h-5 mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>\n'
                '                    <span class="text-[11px] font-medium tracking-tight">Calendar</span>\n'
                '                </a>\n'
            )
            html = html[:solana_block.end()] + cal + html[solana_block.end():]
    for name in ("home","solana","calendar","number","history","finances"):
        if name == active:
            cls, bar = "bg-gray-200/80 text-gray-900", "opacity-100"
        else:
            cls, bar = "text-gray-500 hover:text-gray-900 hover:bg-gray-100", "opacity-0"
        html = html.replace("__" + name.upper() + "_CLS__", cls)
        html = html.replace("__" + name.upper() + "_BAR__", bar)
    return html


# ---------- Pricing ----------
NEW_PRICING = '''
        <div class="text-center max-w-[720px] mx-auto">
          <span class="inline-flex items-center rounded-full bg-[#111111] border border-[#111111] px-3.5 py-1.5 text-[13px] font-semibold text-white">Pricing</span>
          <h2 class="mt-5 text-3xl sm:text-4xl lg:text-[44px] font-bold leading-[1.12] tracking-[-0.03em] text-[#111111]">Simple pricing that scales</h2>
          <p class="mt-5 text-[17px] leading-[1.6] text-[#55565B]">Two plans. Cancel anytime.</p>
        </div>
        <div class="mt-20 grid grid-cols-1 lg:grid-cols-2 gap-6 items-start max-w-[900px] mx-auto" id="pricing-cards">
          <div class="rounded-3xl border border-gray-300 ring-2 ring-black/5 bg-white p-8 shadow-xs flex flex-col">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Pro</h3>
              <span class="inline-flex items-center rounded-full bg-[#111111] border border-[#111111] px-3 py-1 text-[12px] font-semibold text-white">Most popular</span>
            </div>
            <p class="mt-2.5 text-[15.5px] leading-[1.6] text-[#55565B]">Bring your own Gemini API key.</p>
            <div class="mt-6 flex items-end gap-1.5">
              <span class="text-[40px] font-extrabold leading-none tracking-[-0.04em] text-[#111111]">$15</span>
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
              <button data-plan="pro" class="plan-btn btn-primary inline-flex w-full items-center justify-center px-6 py-3 rounded-xl font-bold text-[15.5px] tracking-[-0.01em] shadow-xs">Choose Pro</button>
            </div>
          </div>
          <div class="rounded-3xl border border-neutral-100 bg-white p-8 shadow-xs flex flex-col">
            <h3 class="text-[19px] font-bold tracking-tight text-[#111111]">Max</h3>
            <p class="mt-2.5 text-[15.5px] leading-[1.6] text-[#55565B]">AI included — no API key needed.</p>
            <div class="mt-6 flex items-end gap-1.5">
              <span class="text-[40px] font-extrabold leading-none tracking-[-0.04em] text-[#111111]">$99</span>
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
              <button data-plan="max" class="plan-btn inline-flex w-full items-center justify-center px-6 py-3 rounded-xl font-bold text-[15.5px] border border-neutral-200 text-neutral-800 hover:bg-neutral-50 transition shadow-xs">Choose Max</button>
            </div>
          </div>
        </div>
        <script>
          window.STRIPE_PRO_LINK = "";
          window.STRIPE_MAX_LINK = "";
          window.whenFirebase && window.whenFirebase(function (fb) {
            document.querySelectorAll('.plan-btn').forEach(function (btn) {
              btn.addEventListener('click', function () {
                var plan = btn.dataset.plan;
                var user = fb.auth.currentUser;
                if (!user) { window.location.href = 'signup.html?plan=' + plan; return; }
                var link = plan === 'pro' ? window.STRIPE_PRO_LINK : window.STRIPE_MAX_LINK;
                if (!link) { alert('Checkout coming soon'); return; }
                var u = encodeURIComponent(user.uid);
                var e = encodeURIComponent(user.email || '');
                window.location.href = link + '?client_reference_id=' + u + '&prefilled_email=' + e;
              });
            });
          });
        </script>
'''

def page_pricing(_ctx):
    return ("Pricing", "Simple pricing for Vocallus.",
            section_wrap("pricing", NEW_PRICING), "")


# ---------- Dashboard: real data ----------
DASH_JS_PATCH = '''
  <script>
    window.requireAuth && window.requireAuth();
    window.whenFirebase && window.whenFirebase(function (fb) {
      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) return;
        var nameEl = document.getElementById('user-name');
        if (nameEl) nameEl.textContent = user.displayName || (user.email || '').split('@')[0] || 'there';
        fb.getDoc(fb.doc(fb.db, 'users', user.uid)).then(function (snap) {
          if (!snap.exists()) return;
          var d = snap.data();
          // Update any element that shows plan or current number.
          document.querySelectorAll('[data-bind="plan"]').forEach(function (el) {
            el.textContent = (d.plan && d.plan !== 'none') ? d.plan[0].toUpperCase() + d.plan.slice(1) : 'None';
          });
          document.querySelectorAll('[data-bind="number"]').forEach(function (el) {
            el.textContent = d.phoneNumber || 'None';
          });
          document.querySelectorAll('[data-bind="agentName"]').forEach(function (el) {
            el.textContent = d.agentName || 'Solana';
          });
        });
        var so = document.getElementById('signout-btn');
        if (so) so.addEventListener('click', function () {
          fb.signOut(fb.auth).then(function () { window.location.href = 'login.html'; });
        });
      });
    });
  </script>
'''


# ---------- Final PAGES rebind ----------
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

# ---------- render_page picks the right extra JS ----------
_prev_render_page2__u1 = render_page

def render_page(path, builder):
    html = _prev_render_page2__u1(path, builder)
    name = Path(path).name
    extra = ""
    if name == "login.html":     extra = LOGIN_JS
    elif name == "signup.html":  extra = SIGNUP_JS
    elif name == "solana.html":  extra = SOLANA_JS
    elif name == "calendar.html":extra = CALENDAR_JS
    elif name == "dashboard.html": extra = DASH_JS_PATCH
    if extra and "</body>" in html and extra.strip()[:30] not in html:
        html = html.replace("</body>", extra + "\n</body>", 1)
    # Tag dashboard elements with data-bind
    if name == "dashboard.html":
        html = html.replace('id="user-name"', 'id="user-name" data-bind="agentName"', 1)
        # "Growth" plan chip
        html = html.replace('>Growth<', ' data-bind="plan">None<')
    return html

# --- end edit.py: Firebase v10 + Calendar + Pricing ---




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
          data = data.numbers || [];
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




# --- edit.py: smooth header auth swap ---

# Strip any previous header-swap script, then inject a new one that:
#   • fades "Sign in" out over ~220ms
#   • fades the primary button out, swaps its text + href, fades it back in
#   • uses "Go to Dashboard" with an arrow instead of just "Dashboard"
#   • does nothing for signed-out visitors (default buttons stay)
#   • honors prefers-reduced-motion (instant swap, no fade)

_HEADER_SWAP_RE = re.compile(
    r'\s*<script>\s*window\.whenFirebase && window\.whenFirebase.*?</script>',
    re.DOTALL,
)

_NEW_HEADER_SWAP = '''
  <script>
    /* header-auth-swap */
    (function () {
      function run() {
        var fb = window.__fb;
        if (!fb) return;
        var header = document.querySelector('header');
        if (!header) return;

        var login   = header.querySelector('a[href$="login.html"]');
        var primary = header.querySelector(
          'a[href$="signup.html"].btn-primary, ' +
          'a[href$="signup.html"][class*="btn-primary"]'
        );
        if (!primary) return;

        var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!reduce) {
          [login, primary].forEach(function (el) {
            if (el) el.style.transition = 'opacity .22s ease';
          });
        }

        fb.onAuthStateChanged(fb.auth, function (user) {
          if (!user) return; // signed out: leave defaults alone

          // Hide "Sign in"
          if (login && !login.dataset.authSwapped) {
            login.dataset.authSwapped = '1';
            if (reduce) {
              login.style.display = 'none';
            } else {
              login.style.opacity = '0';
              setTimeout(function () { login.style.display = 'none'; }, 220);
            }
          }

          // Swap primary button
          if (!primary.dataset.authSwapped) {
            primary.dataset.authSwapped = '1';

            var swap = function () {
              primary.setAttribute('href', 'Pages/dashboard.html');
              primary.innerHTML =
                'Go to Dashboard' +
                '<svg class="w-4 h-4 ml-2" viewBox="0 0 24 24" fill="none" ' +
                'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" ' +
                'stroke-linejoin="round">' +
                '<path d="M5 12h14"></path><path d="M12 5l7 7-7 7"></path>' +
                '</svg>';
            };

            if (reduce) {
              swap();
            } else {
              primary.style.opacity = '0';
              setTimeout(function () {
                swap();
                primary.style.opacity = '1';
              }, 180);
            }
          }
        });
      }

      if (window.__fb) run();
      else window.addEventListener('firebase-ready', run, { once: true });
    })();
  </script>
'''

_prev_render_header_1__u3 = render_header

def render_header(ctx, current_page=""):
    html = _prev_render_header_1__u3(ctx, current_page)
    html = _HEADER_SWAP_RE.sub('', html)
    if "</header>" in html:
        html = html.replace("</header>", _NEW_HEADER_SWAP + "\n</header>", 1)
    return html

# --- end edit.py: smooth header auth swap ---




# --- edit.py: header auth swap (Talk to Sales / Dashboard) ---

# Strip any earlier header-swap scripts so only ours runs.
_HEADER_SWAP_RE = re.compile(
    r'\s*<script>\s*(?:/\* header-auth-swap \*/|\s*window\.whenFirebase && window\.whenFirebase).*?</script>',
    re.DOTALL,
)

_NEW_HEADER_SWAP = '''
  <script>
    /* header-auth-swap */
    (function () {
      function run() {
        var fb = window.__fb;
        if (!fb) return;
        var header = document.querySelector('header');
        if (!header) return;

        // The bordered "Talk to Sales" — same one on every marketing page.
        var secondary = header.querySelector(
          'a[href$="talk-to-sales.html"]:not(.btn-primary)'
        );
        // The primary "Try for free" button.
        var primary = header.querySelector(
          'a[href$="signup.html"].btn-primary, ' +
          'a[href$="signup.html"][class*="btn-primary"]'
        );
        var login = header.querySelector('a[href$="login.html"]');
        if (!primary) return;

        var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!reduce) {
          [login, primary, secondary].forEach(function (el) {
            if (el) el.style.transition = 'opacity .2s ease';
          });
        }

        function hide(el, ms) {
          if (!el || el.dataset.authHidden) return;
          el.dataset.authHidden = '1';
          if (reduce) { el.style.display = 'none'; return; }
          el.style.opacity = '0';
          setTimeout(function () { el.style.display = 'none'; }, ms || 200);
        }

        function swapPrimary(text, href) {
          if (!primary || primary.dataset.authSwapped) return;
          primary.dataset.authSwapped = '1';
          var apply = function () {
            primary.textContent = text;
            primary.setAttribute('href', href);
            // Keep it looking like the current primary button.
            primary.classList.add('btn-primary');
            primary.classList.remove('border', 'border-neutral-200', 'text-neutral-800');
          };
          if (reduce) { apply(); return; }
          primary.style.opacity = '0';
          setTimeout(function () { apply(); primary.style.opacity = '1'; }, 180);
        }

        // -------- Default (signed out): relabel primary to Talk to Sales ----
        // Do this immediately, before auth resolves, so the button is never
        // "Try for free" for signed-out visitors.
        swapPrimary('Talk to Sales', 'Pages/talk-to-sales.html');
        // Now there are two Talk to Sales; keep the bordered one visible.

        fb.onAuthStateChanged(fb.auth, function (user) {
          if (!user) return;

          // Signed in: hide Sign in, hide the bordered duplicate, and
          // relabel the primary to Dashboard.
          hide(login, 200);
          hide(secondary, 200);

          // Undo the swap flag so we can change the label again.
          if (primary) primary.dataset.authSwapped = '';
          swapPrimary('Dashboard', 'Pages/dashboard.html');
        });
      }

      if (window.__fb) run();
      else window.addEventListener('firebase-ready', run, { once: true });
    })();
  </script>
'''

_prev_render_header_swap__u2 = render_header

def render_header(ctx, current_page=""):
    html = _prev_render_header_swap__u2(ctx, current_page)
    html = _HEADER_SWAP_RE.sub('', html)
    if "</header>" in html:
        html = html.replace("</header>", _NEW_HEADER_SWAP + "\n</header>", 1)
    return html

# --- end edit.py: header auth swap (Talk to Sales / Dashboard) ---




# --- edit.py: hero Talk to Sales + auth swap ---

# 1. Hero: "See the dashboard" -> "Talk to Sales", pointing at talk-to-sales.html

_HERO_BTN_OLD = (
    '                <a href="{ctx.u(\'Pages/dashboard.html\')}" '
    'class="inline-flex items-center justify-center px-7 py-3.5 rounded-xl '
    'font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 '
    'text-neutral-800 hover:bg-neutral-50 transition">\n'
    "                  See the dashboard\n"
    "                </a>\n"
)
_HERO_BTN_NEW = (
    '                <a href="{ctx.u(\'Pages/talk-to-sales.html\')}" '
    'class="inline-flex items-center justify-center px-7 py-3.5 rounded-xl '
    'font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 '
    'text-neutral-800 hover:bg-neutral-50 transition">\n'
    "                  Talk to Sales\n"
    "                </a>\n"
)

# Also catch the alternative hero form (in case a prior edit changed it)
_HERO_BTN_ALT = (
    'href="{ctx.u(\'Pages/dashboard.html\')}" class="inline-flex items-center '
    'justify-center px-7 py-3.5 rounded-xl font-bold text-[16px] '
    'tracking-[-0.01em] border border-neutral-200 text-neutral-800 '
    'hover:bg-neutral-50 transition">\n'
    "                  See the dashboard\n"
)

_prev_page_index = page_index

def page_index(ctx):
    title, desc, content, main = _prev_page_index(ctx)
    if "See the dashboard" in content:
        if _HERO_BTN_OLD in content:
            content = content.replace(_HERO_BTN_OLD, _HERO_BTN_NEW, 1)
        else:
            # Fallback: swap just the label + target string if exact markup drifted
            content = content.replace(
                "Pages/dashboard.html')}\" class=\"inline-flex items-center justify-center px-7 py-3.5 rounded-xl font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 text-neutral-800 hover:bg-neutral-50 transition\">\n                  See the dashboard",
                "Pages/talk-to-sales.html')}\" class=\"inline-flex items-center justify-center px-7 py-3.5 rounded-xl font-bold text-[16px] tracking-[-0.01em] border border-neutral-200 text-neutral-800 hover:bg-neutral-50 transition\">\n                  Talk to Sales",
                1,
            )
            # Last-resort: just relabel
            content = content.replace("See the dashboard", "Talk to Sales")
    return title, desc, content, main


# 2. Header: remove any previous swap script that relabeled the primary button

_HEADER_SWAP_RE = re.compile(
    r'\s*<script>\s*(?:/\* header-auth-swap \*/|\s*window\.whenFirebase && window\.whenFirebase).*?</script>',
    re.DOTALL,
)

# 3. New script: leaves "Try for free" alone; swaps every "Talk to Sales"
#    link to "Dashboard" when the user is signed in.

_NEW_SWAP_SCRIPT = '''
  <script>
    /* talk-to-sales-auth-swap */
    (function () {
      function run() {
        var fb = window.__fb;
        if (!fb) return;
        var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Every "Talk to Sales" link on the page (header + hero).
        function talkButtons() {
          return Array.prototype.slice.call(
            document.querySelectorAll('a[href$="talk-to-sales.html"]')
          );
        }

        // Also the small bordered header button is an <a>; both get swapped.
        var targets = talkButtons();
        if (!targets.length) return;

        if (!reduce) {
          targets.forEach(function (el) { el.style.transition = 'opacity .2s ease'; });
        }

        function applySwap() {
          targets.forEach(function (el) {
            if (el.dataset.authSwapped) return;
            el.dataset.authSwapped = '1';
            var doIt = function () {
              el.textContent = 'Dashboard';
              el.setAttribute('href', 'Pages/dashboard.html');
            };
            if (reduce) { doIt(); return; }
            el.style.opacity = '0';
            setTimeout(function () { doIt(); el.style.opacity = '1'; }, 180);
          });
        }

        // Also hide the small "Sign in" link when signed in (unchanged behavior).
        var login = document.querySelector('header a[href$="login.html"]');
        function hideLogin() {
          if (!login || login.dataset.authHidden) return;
          login.dataset.authHidden = '1';
          if (reduce) { login.style.display = 'none'; return; }
          login.style.opacity = '0';
          setTimeout(function () { login.style.display = 'none'; }, 200);
        }

        fb.onAuthStateChanged(fb.auth, function (user) {
          if (!user) return;
          applySwap();
          hideLogin();
        });
      }

      if (window.__fb) run();
      else window.addEventListener('firebase-ready', run, { once: true });
    })();
  </script>
'''

_prev_render_header_swap__u1 = render_header

def render_header(ctx, current_page=""):
    html = _prev_render_header_swap__u1(ctx, current_page)
    html = _HEADER_SWAP_RE.sub('', html)
    if "</header>" in html:
        html = html.replace("</header>", _NEW_SWAP_SCRIPT + "\n</header>", 1)
    # Also handle Talk to Sales buttons in the body (the hero one). Inject
    # the same script near the end of <body> so it can find them after render.
    return html


# Body-level copy of the same swap (for the hero button)
_BODY_SWAP_SCRIPT = '''
  <script>
    /* talk-to-sales-auth-swap-body */
    window.whenFirebase && window.whenFirebase(function (fb) {
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      fb.onAuthStateChanged(fb.auth, function (user) {
        if (!user) return;
        var btns = document.querySelectorAll('main a[href$="talk-to-sales.html"]');
        btns.forEach(function (el) {
          if (el.dataset.authSwapped) return;
          el.dataset.authSwapped = '1';
          var doIt = function () {
            el.textContent = 'Dashboard';
            el.setAttribute('href', 'Pages/dashboard.html');
          };
          if (reduce) { doIt(); return; }
          el.style.transition = 'opacity .2s ease';
          el.style.opacity = '0';
          setTimeout(function () { doIt(); el.style.opacity = '1'; }, 180);
        });
      });
    });
  </script>
'''

_prev_rp_hero = render_page

def render_page(path, builder):
    html = _prev_rp_hero(path, builder)
    name = Path(path).name
    # Only marketing pages that contain a hero "Talk to Sales" need this.
    if name in ("index.html",) and "talk-to-sales-auth-swap-body" not in html:
        if "</body>" in html:
            html = html.replace("</body>", _BODY_SWAP_SCRIPT + "\n</body>", 1)
    return html

# --- end edit.py: hero Talk to Sales + auth swap ---




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


if __name__ == "__main__":
    build()