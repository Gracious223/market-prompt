#!/usr/bin/env python3
"""
The Signal — site builder.

  python3 build.py

Does two things:
  1. Regenerates index.html (the landing page) from the newsletters/ folder.
  2. Re-renders each newsletter into a modern, interactive article page,
     reusing the same navy/gold brand. Content is parsed out of each file and
     re-emitted, so the step is idempotent (safe to run repeatedly).

Real cover/hero images live in assets/img/ (downloaded once). No other deps.
"""

import re
import html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
NEWSLETTERS = ROOT / "newsletters"
IMG_DIR = ROOT / "assets" / "img"
OUTPUT = ROOT / "index.html"

SKIP_SUFFIXES = ("-preview.html",)
SKIP_NAMES = {"index.html"}

SECTION_LABELS = {"markets": "Markets", "tools": "Tools", "labs": "Labs", "pm": "Product", "risk": "Risk"}

# Tiny line icons (24-viewbox stroke paths) for chips / pills.
ICON_PATHS = {
    "markets": '<polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/>',
    "tools": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    "labs": '<path d="M9 3h6M10 3v5L5 17a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/>',
    "pm": '<polygon points="12 3 21 8 12 13 3 8 12 3"/><polyline points="3 14 12 19 21 14"/>',
    "risk": '<path d="M12 4 2 20h20L12 4z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
}

# Real images available (downloaded into assets/img). Sorted for stable mapping.
_IMAGES = sorted(p.name for p in IMG_DIR.glob("img*.jpg")) if IMG_DIR.exists() else []

# Thematic image per section type (used as section banners inside articles).
SECTION_IMG_FILE = {
    "markets": "img7.jpg",  # financial-district towers
    "tools": "img4.jpg",    # analytics dashboard
    "labs": "img3.jpg",     # AI robot
    "pm": "img8.jpg",       # abstract data network
    "risk": "img1.jpg",     # falling candlesticks
}


def issue_image(num, idx=0, prefix=""):
    if not _IMAGES:
        return None
    key = int(num) if str(num).isdigit() else idx + 1
    return prefix + "assets/img/" + _IMAGES[(key - 1) % len(_IMAGES)]


def section_image(dot, prefix="../"):
    if not _IMAGES:
        return None
    name = SECTION_IMG_FILE.get(dot)
    if name not in _IMAGES:
        name = _IMAGES[0]
    return prefix + "assets/img/" + name


def icon_svg(key, cls="ic"):
    if key not in ICON_PATHS:
        return ""
    return (
        f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{ICON_PATHS[key]}</svg>'
    )


def chip_html(key):
    return f'<span class="chip {key}">{icon_svg(key)}{SECTION_LABELS[key]}</span>'


# ──────────────────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────────────────

STORY_RE = re.compile(
    r'<span class="tag (\w+)">(?:<svg.*?</svg>)?(.*?)</span>'
    r'.*?<h3[^>]*>(.*?)</h3>'
    r'.*?<p[^>]*>(.*?)</p>'
    r'.*?<div class="why-it-matters">\s*<p[^>]*>(.*?)</p>'
    r'.*?<a[^>]*href="(.*?)"[^>]*>(.*?)</a>',
    re.S,
)


def _search(pattern, text, default=""):
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else default


def parse_issue(path: Path):
    text = path.read_text(encoding="utf-8")

    title = _search(r"<title>(.*?)</title>", text)
    eyebrow = _search(r'class="eyebrow">(.*?)<', text) or "Your Intelligence Brief"
    issue = _search(r'class="issue">\s*(.*?)\s*<', text) or "Issue"
    num = _search(r"(\d+)", issue, default="")
    date_label = _search(r'class="date-bar">\s*<span>\s*(.*?)\s*</span>', text)

    intro_html = _search(r'class="intro"[^>]*>\s*<p[^>]*>(.*?)</p>', text)
    summary = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", intro_html))).strip()

    stat_cards = re.findall(r'<div class="number">(.*?)</div>\s*<div class="label">(.*?)</div>', text, re.S)
    stat_cards = [(n.strip(), l.strip()) for n, l in stat_cards]

    sectionlist = []
    for block in re.split(r'<(?:div|section) class="section[ "]', text)[1:]:
        name = _search(r'<h2[^>]*>(.*?)</h2>', block)
        dot = _search(r'class="dot (\w+)"', block)
        if not name or not dot:
            continue
        stories = []
        for m in STORY_RE.finditer(block):
            stories.append({
                "tagcls": m.group(1),
                "tag": m.group(2).strip(),
                "title": m.group(3).strip(),
                "body": m.group(4).strip(),
                "why": m.group(5).strip(),
                "href": m.group(6).strip(),
                "link": m.group(7).strip(),
            })
        sectionlist.append({"name": name, "dot": dot, "stories": stories})

    # Files we can't parse into our template (e.g. the scheduled agent's richer
    # bespoke layout) are kept as-is and only indexed — never overwritten.
    external = len(sectionlist) == 0
    if not num:
        num = _search(r"Issue No\.\s*(\d+)", text, default="")
    if external:
        lead = _search(r'class="pill[^"]*">(.*?)<', text) or "Daily Edition"
        dek = _search(r"<h2[^>]*>.*?</h2>\s*<p[^>]*>(.*?)</p>", text)
        if not dek:
            dek = _search(r'class="story-body"[^>]*>.*?<p[^>]*>(.*?)</p>', text)
        summary = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", dek))).strip()
        if not summary:
            summary = _search(r'class="subtitle">(.*?)<', text) or "Daily edition of The Signal."
    else:
        lead = sectionlist[0]["name"]

    dots = []
    for s in sectionlist:
        if s["dot"] not in dots:
            dots.append(s["dot"])

    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", path.stem)
    sort_dt = datetime(*map(int, m.groups())) if m else datetime.fromtimestamp(path.stat().st_mtime)

    return {
        "file": path.name, "title": title, "eyebrow": eyebrow, "issue": issue, "num": num,
        "date_label": date_label or sort_dt.strftime("%d %B %Y"), "intro_html": intro_html,
        "summary": summary, "stat_cards": stat_cards, "sectionlist": sectionlist,
        "sections": dots, "sort_dt": sort_dt, "external": external, "lead": lead,
    }


def collect():
    issues = []
    for path in sorted(NEWSLETTERS.glob("*.html")):
        if path.name in SKIP_NAMES or path.name.endswith(SKIP_SUFFIXES):
            continue
        issues.append(parse_issue(path))
    issues.sort(key=lambda i: i["sort_dt"], reverse=True)
    return issues


# ──────────────────────────────────────────────────────────────────────────
# Landing page (index.html)
# ──────────────────────────────────────────────────────────────────────────

INDEX_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#14142b;--ink-2:#1d1d3a;--paper:#f6f3ec;--gold:#c9a96e;--gold-soft:#e3cfa6;--muted:#8a8fa8;--muted-d:#5b5f78;--line:#e8e3d8;--card:#fff;--r:14px}
html{scroll-behavior:smooth}
body{background:var(--paper);font-family:'Inter',sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.mono{font-family:'Space Mono',monospace}
.nav{position:sticky;top:0;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:14px 28px;background:rgba(20,20,43,.72);backdrop-filter:saturate(160%) blur(14px);-webkit-backdrop-filter:saturate(160%) blur(14px);border-bottom:1px solid rgba(201,169,110,.18)}
.nav .brand{font-family:'Playfair Display',serif;font-weight:800;font-size:19px;color:var(--paper)}
.nav .brand span{color:var(--gold)}
.nav .links{display:flex;align-items:center;gap:26px}
.nav .links a{font-size:12px;font-weight:500;letter-spacing:.3px;color:#b9bcd0;transition:color .15s}
.nav .links a:hover{color:var(--gold)}
.nav .cta{border:none;cursor:pointer;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink);background:var(--gold);padding:8px 15px;border-radius:999px;transition:transform .15s,box-shadow .15s}
.nav .cta:hover{transform:translateY(-1px);box-shadow:0 6px 18px rgba(201,169,110,.4)}
@media (max-width:640px){.nav .links a:not(.cta){display:none}}
.hero{position:relative;overflow:hidden;background:var(--ink);color:var(--paper);padding:96px 24px 104px;text-align:center;isolation:isolate}
.hero::before,.hero::after{content:"";position:absolute;z-index:-2;border-radius:50%;filter:blur(70px);opacity:.55}
.hero::before{width:560px;height:560px;top:-220px;left:50%;transform:translateX(-60%);background:radial-gradient(circle,rgba(201,169,110,.55),transparent 65%);animation:float1 14s ease-in-out infinite}
.hero::after{width:520px;height:520px;bottom:-260px;right:50%;transform:translateX(60%);background:radial-gradient(circle,rgba(90,110,200,.42),transparent 65%);animation:float2 18s ease-in-out infinite}
.hero .grid-bg{position:absolute;inset:0;z-index:-1;opacity:.5;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:52px 52px;mask-image:radial-gradient(ellipse 75% 70% at 50% 35%,#000 40%,transparent 100%);-webkit-mask-image:radial-gradient(ellipse 75% 70% at 50% 35%,#000 40%,transparent 100%)}
@keyframes float1{0%,100%{transform:translateX(-60%) translateY(0)}50%{transform:translateX(-55%) translateY(26px)}}
@keyframes float2{0%,100%{transform:translateX(60%) translateY(0)}50%{transform:translateX(54%) translateY(-30px)}}
.hero .kicker{display:inline-flex;align-items:center;gap:9px;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--gold);border:1px solid rgba(201,169,110,.35);border-radius:999px;padding:7px 16px;margin-bottom:30px;background:rgba(201,169,110,.06)}
.hero .dot{width:7px;height:7px;border-radius:50%;background:#5ad17a;box-shadow:0 0 0 0 rgba(90,209,122,.7);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(90,209,122,.6)}70%{box-shadow:0 0 0 8px rgba(90,209,122,0)}100%{box-shadow:0 0 0 0 rgba(90,209,122,0)}}
.hero h1{font-family:'Playfair Display',serif;font-weight:900;font-size:clamp(54px,11vw,104px);line-height:.94;letter-spacing:-2px}
.hero h1 span{background:linear-gradient(120deg,var(--gold),var(--gold-soft));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .tagline{margin-top:22px;font-size:clamp(14px,2.3vw,17px);font-weight:300;letter-spacing:.4px;color:#c2c5d8}
.hero .sub{margin:14px auto 0;max-width:520px;font-size:14px;line-height:1.7;color:var(--muted)}
.hero .actions{margin-top:38px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.btn{font-size:13px;font-weight:600;letter-spacing:.3px;padding:13px 26px;border-radius:999px;transition:transform .15s,box-shadow .15s,background .15s}
.btn-gold{background:var(--gold);color:var(--ink)}
.btn-gold:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(201,169,110,.42)}
.btn-ghost{border:1px solid rgba(255,255,255,.22);color:var(--paper)}
.btn-ghost:hover{border-color:var(--gold);color:var(--gold)}
.hero-wave{display:block;width:100%;height:40px;margin-top:-1px}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
.featured{margin:-48px auto 0;position:relative;z-index:5}
.feat-card{display:grid;grid-template-columns:230px 1fr auto;align-items:stretch;gap:30px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 24px 20px 20px;box-shadow:0 30px 60px -28px rgba(20,20,43,.4);transition:transform .2s,box-shadow .2s}
.feat-card:hover{transform:translateY(-3px);box-shadow:0 38px 70px -28px rgba(20,20,43,.5)}
.feat-cover{position:relative;border-radius:13px;overflow:hidden;min-height:184px}
.feat-cover img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.feat-cover .ov{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;background:linear-gradient(180deg,rgba(19,19,42,.35),rgba(19,19,42,.72))}
.feat-cover .ov .lbl{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--gold)}
.feat-cover .ov .big{font-family:'Playfair Display',serif;font-weight:800;font-size:60px;color:var(--paper);line-height:1;margin:4px 0}
.feat-cover .ov .lbl-date{font-family:'Space Mono',monospace;font-size:11px;color:#dfe1ee;letter-spacing:.5px}
.feat-body{align-self:center}
.feat-body .ey{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--gold);margin-bottom:10px}
.feat-body p{font-size:15.5px;line-height:1.65;color:#44475e}
.feat-body .chips{margin-top:14px}
.feat-cta{align-self:center;font-family:'Space Mono',monospace;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink);border:1.5px solid var(--ink);border-radius:999px;padding:12px 20px;white-space:nowrap;transition:background .15s,color .15s}
.feat-card:hover .feat-cta{background:var(--ink);color:var(--gold)}
@media (max-width:820px){.feat-card{grid-template-columns:1fr;text-align:left}.feat-cover{min-height:150px}.feat-cta{justify-self:start;align-self:start}}
.toolbar{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;flex-wrap:wrap;margin:72px 0 22px}
.toolbar .h-wrap .lbl{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--gold)}
.toolbar h2{font-family:'Playfair Display',serif;font-size:36px;font-weight:800;margin-top:4px;letter-spacing:-.5px}
.toolbar .count{color:var(--muted-d);font-size:14px;font-weight:400;margin-left:10px}
.search input{font-family:'Inter',sans-serif;font-size:14px;padding:13px 18px 13px 42px;width:300px;max-width:78vw;border:1px solid var(--line);border-radius:999px;background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='%238a8fa8' stroke-width='2' viewBox='0 0 24 24'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E") no-repeat 16px center;color:var(--ink);outline:none;transition:border-color .15s,box-shadow .15s}
.search input:focus{border-color:var(--gold);box-shadow:0 0 0 4px rgba(201,169,110,.14)}
.filters{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 28px}
.pill{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;padding:9px 15px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--muted-d);cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:7px}
.pill:hover{border-color:var(--gold);color:var(--ink)}
.pill.active{background:var(--ink);color:var(--gold);border-color:var(--ink)}
.pill .ic{width:13px;height:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:24px;padding-bottom:90px}
.card{position:relative;overflow:hidden;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:0;display:flex;flex-direction:column;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
.card-rule{position:absolute;top:0;left:0;right:0;height:3px;z-index:4;background:linear-gradient(90deg,var(--gold),var(--gold-soft));transform:scaleX(0);transform-origin:left;transition:transform .25s ease}
.card:hover{transform:translateY(-5px);box-shadow:0 22px 44px -22px rgba(20,20,43,.45);border-color:transparent}
.card:hover .card-rule{transform:scaleX(1)}
.cover{position:relative;height:172px;overflow:hidden}
.cover img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s ease}
.card:hover .cover img{transform:scale(1.07)}
.cover::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,20,43,.05) 40%,rgba(20,20,43,.62))}
.cover-num{position:absolute;left:16px;bottom:12px;z-index:2;font-family:'Space Mono',monospace;font-size:12px;letter-spacing:1px;color:#fff;text-transform:uppercase}
.cover-num b{color:var(--gold);margin-left:4px}
.card-body{padding:20px 26px 24px;display:flex;flex-direction:column;flex:1}
.card-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}
.card-date{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:.5px}
.card-tag{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--gold)}
.card-title{font-family:'Playfair Display',serif;font-size:25px;font-weight:700;line-height:1.12;letter-spacing:-.3px}
.card-summary{font-size:13.5px;line-height:1.66;color:#56566a;margin-top:13px;flex:1;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.card-foot{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:18px;padding-top:16px;border-top:1px solid #f0ede6}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font-family:'Space Mono',monospace;font-size:9px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;padding:4px 8px;border-radius:999px;display:inline-flex;align-items:center;gap:4px}
.chip .ic{width:11px;height:11px}
.chip.markets{background:#e8f4f8;color:#2a7fa8}.chip.tools{background:#eef8e6;color:#4a8a2a}.chip.labs{background:#f8e8f4;color:#8a2a7a}.chip.pm{background:#f8f0e8;color:#8a5a2a}.chip.risk{background:#f8e8e8;color:#8a2a2a}
.read{font-size:12px;font-weight:700;color:var(--gold);white-space:nowrap;display:inline-flex;gap:6px}
.read .arr{transition:transform .2s}
.card:hover .read .arr{transform:translateX(4px)}
.empty{grid-column:1/-1;text-align:center;color:var(--muted);padding:70px 0;font-size:14px}
.js .reveal{opacity:0;transform:translateY(20px);transition:opacity .55s ease,transform .55s ease;transition-delay:calc(var(--i,0) * 55ms)}
.js .reveal.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.js .reveal{opacity:1;transform:none;transition:none}.hero::before,.hero::after,.cover img{animation:none;transition:none}}
.site-footer{background:var(--ink);color:var(--muted);text-align:center;padding:56px 24px;font-size:12px;line-height:1.9}
.site-footer .ft{font-family:'Playfair Display',serif;color:var(--paper);font-size:26px;font-weight:800;margin-bottom:6px}
.site-footer .ft span{color:var(--gold)}
.site-footer .meta{font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.5px;margin-top:14px;color:var(--muted-d)}
.foot-sub{background:none;border:none;cursor:pointer;color:var(--gold);font-family:'Space Mono',monospace;font-size:12px;letter-spacing:.5px;margin-top:12px;transition:opacity .15s}
.foot-sub:hover{opacity:.75}
.modal{position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;padding:24px}
.modal[hidden]{display:none}
.modal .backdrop{position:absolute;inset:0;background:rgba(12,12,26,.62);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);animation:fade .2s ease}
.modal .dialog{position:relative;z-index:1;width:100%;max-width:440px;background:var(--card);border-radius:18px;overflow:hidden;box-shadow:0 40px 90px -30px rgba(0,0,0,.6);animation:pop .25s ease}
@keyframes fade{from{opacity:0}}
@keyframes pop{from{opacity:0;transform:translateY(14px) scale(.97)}}
.modal .top{background:var(--ink);color:var(--paper);padding:32px 30px 26px;text-align:center;position:relative;overflow:hidden}
.modal .top::after{content:"";position:absolute;width:260px;height:260px;top:-160px;left:50%;transform:translateX(-50%);background:radial-gradient(circle,rgba(201,169,110,.5),transparent 65%);filter:blur(40px)}
.modal .top .ey{position:relative;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2.5px;text-transform:uppercase;color:var(--gold)}
.modal .top h3{position:relative;font-family:'Playfair Display',serif;font-size:28px;font-weight:800;margin-top:8px}
.modal .top p{position:relative;font-size:13px;color:#c2c5d8;margin-top:8px;line-height:1.6}
.modal .body{padding:26px 30px 30px}
.modal form{display:flex;flex-direction:column;gap:12px}
.modal input{font-family:'Inter',sans-serif;font-size:14px;padding:14px 16px;border:1px solid var(--line);border-radius:10px;outline:none;transition:border-color .15s,box-shadow .15s}
.modal input:focus{border-color:var(--gold);box-shadow:0 0 0 4px rgba(201,169,110,.14)}
.modal button.sub{font-family:'Space Mono',monospace;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;background:var(--gold);color:var(--ink);border:none;border-radius:10px;padding:14px;cursor:pointer;transition:transform .15s,box-shadow .15s}
.modal button.sub:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(201,169,110,.4)}
.modal .fine{font-size:11px;color:var(--muted);text-align:center;margin-top:2px}
.modal .x{position:absolute;top:14px;right:16px;z-index:2;background:rgba(255,255,255,.12);color:var(--paper);border:none;width:30px;height:30px;border-radius:50%;cursor:pointer;font-size:18px;line-height:1;transition:background .15s}
.modal .x:hover{background:rgba(255,255,255,.25)}
.modal .done{text-align:center;padding:10px 0}
.modal .done .tick{display:inline-flex;align-items:center;justify-content:center;width:52px;height:52px;border-radius:50%;background:#eaf7ee;color:#2e9e57;font-size:26px}
.modal .done p{font-size:14px;color:#44475e;margin-top:12px;line-height:1.6}
@media (max-width:560px){.search input{width:100%}.search{width:100%}.toolbar{align-items:flex-start}}
"""

INDEX_JS = """
const q=document.getElementById('q');
const cards=[...document.querySelectorAll('.card')];
const empty=document.getElementById('empty');
const pills=[...document.querySelectorAll('.pill')];
let activeSection='all';
function apply(){
  const term=(q?q.value:'').trim().toLowerCase();
  let shown=0;
  cards.forEach(c=>{
    const matchText=!term||c.dataset.text.toLowerCase().includes(term);
    const matchSec=activeSection==='all'||(c.dataset.sections||'').split(' ').includes(activeSection);
    const ok=matchText&&matchSec;
    c.style.display=ok?'':'none';
    if(ok)shown++;
  });
  empty.hidden=shown!==0;
}
q&&q.addEventListener('input',apply);
pills.forEach(p=>p.addEventListener('click',()=>{pills.forEach(x=>x.classList.remove('active'));p.classList.add('active');activeSection=p.dataset.section;apply();}));
const io=new IntersectionObserver((entries)=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
const SUBSCRIBE_TO='EfiaAmankwa@outlook.com';
const modal=document.getElementById('subModal');
const subForm=document.getElementById('subForm');
const subDone=document.getElementById('subDone');
function openModal(){modal.hidden=false;document.body.style.overflow='hidden';setTimeout(()=>{const i=document.getElementById('subEmail');i&&i.focus();},60);}
function closeModal(){modal.hidden=true;document.body.style.overflow='';subForm.hidden=false;subDone.hidden=true;subForm.reset();}
document.querySelectorAll('[data-subscribe]').forEach(b=>b.addEventListener('click',openModal));
modal.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',closeModal));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!modal.hidden)closeModal();});
subForm&&subForm.addEventListener('submit',e=>{
  e.preventDefault();
  const email=document.getElementById('subEmail').value.trim();
  const subject=encodeURIComponent('Subscribe me to The Signal');
  const body=encodeURIComponent('Please add this address to The Signal daily brief:\\n\\n'+email);
  window.location.href='mailto:'+SUBSCRIBE_TO+'?subject='+subject+'&body='+body;
  subForm.hidden=true;subDone.hidden=false;
});
"""


def render_card(issue, index=0):
    chips = "".join(chip_html(s) for s in issue["sections"])
    href = f'newsletters/{issue["file"]}'
    num = html.escape(issue["num"] or "—")
    img = issue_image(issue["num"], index, "") or ""
    lead = issue["lead"]
    secs_attr = " ".join(issue["sections"])
    haystack = html.escape(
        f'{issue["title"]} {issue["issue"]} {issue["summary"]} '
        + " ".join(SECTION_LABELS[s] for s in issue["sections"]),
        quote=True,
    )
    return f"""        <a class="card reveal" href="{href}" data-text="{haystack}" data-sections="{secs_attr}" style="--i:{index}">
          <span class="card-rule"></span>
          <div class="cover">
            <img src="{img}" alt="" loading="lazy" />
            <span class="cover-num">Issue No.<b>{num}</b></span>
          </div>
          <div class="card-body">
            <div class="card-top">
              <span class="card-tag">{html.escape(lead)}</span>
              <span class="card-date">{html.escape(issue["date_label"])}</span>
            </div>
            <h3 class="card-title">The&nbsp;Signal</h3>
            <p class="card-summary">{html.escape(issue["summary"])}</p>
            <div class="card-foot">
              <div class="chips">{chips}</div>
              <span class="read">Read<span class="arr">→</span></span>
            </div>
          </div>
        </a>"""


def render(issues):
    latest = issues[0] if issues else None
    cards = "\n".join(render_card(i, n) for n, i in enumerate(issues))
    count = len(issues)
    built = datetime.now().strftime("%d %B %Y")

    latest_summary = html.escape(latest["summary"]) if latest else "No issues yet."
    latest_date = html.escape(latest["date_label"]) if latest else ""
    latest_num = html.escape(latest["num"]) if latest and latest["num"] else "—"
    latest_href = f'newsletters/{latest["file"]}' if latest else "#"
    latest_chips = "".join(chip_html(s) for s in latest["sections"]) if latest else ""
    latest_img = issue_image(latest["num"], 0, "") if latest else ""

    present = [k for k in SECTION_LABELS if any(k in i["sections"] for i in issues)]
    pills = '<button class="pill active" data-section="all">All Issues</button>' + "".join(
        f'<button class="pill" data-section="{k}">{icon_svg(k)}{SECTION_LABELS[k]}</button>' for k in present
    )

    return f"""<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>The Signal — AI · Public Markets · Product</title>
  <meta name="description" content="The Signal — a daily intelligence brief on AI, public markets, and product management." />
  <script>document.documentElement.className = 'js';</script>
  <style>{INDEX_CSS}</style>
</head>
<body>
  <nav class="nav">
    <a class="brand" href="#top">The <span>Signal</span></a>
    <div class="links">
      <a href="#issues">Issues</a>
      <a href="{latest_href}">Latest</a>
      <button class="cta" type="button" data-subscribe>Subscribe</button>
    </div>
  </nav>

  <header class="hero" id="top">
    <div class="grid-bg"></div>
    <div class="kicker"><span class="dot"></span> Updated Daily · {built}</div>
    <h1>The <span>Signal</span></h1>
    <p class="tagline">AI · Public Markets · Product Management</p>
    <p class="sub">A daily intelligence brief decoding the AI market for analysts and product leaders — five stories, one read, every morning.</p>
    <div class="actions">
      <a class="btn btn-gold" href="{latest_href}">Read the latest issue</a>
      <a class="btn btn-ghost" href="#issues">Browse the archive</a>
    </div>
  </header>
  <svg class="hero-wave" viewBox="0 0 1440 40" preserveAspectRatio="none" aria-hidden="true">
    <path d="M0,40 L0,18 C240,40 480,40 720,24 C960,8 1200,8 1440,22 L1440,40 Z" fill="#14142b"/>
  </svg>

  <div class="wrap">
    <section class="featured" aria-label="Latest issue">
      <a class="feat-card" href="{latest_href}">
        <div class="feat-cover">
          <img src="{latest_img}" alt="" loading="lazy" />
          <div class="ov">
            <span class="lbl">Issue</span>
            <span class="big">{latest_num}</span>
            <span class="lbl-date">{latest_date}</span>
          </div>
        </div>
        <div class="feat-body">
          <div class="ey">★ Latest Dispatch</div>
          <p>{latest_summary}</p>
          <div class="chips">{latest_chips}</div>
        </div>
        <span class="feat-cta">Read now →</span>
      </a>
    </section>

    <div class="toolbar" id="issues">
      <div class="h-wrap">
        <div class="lbl mono">// The Archive</div>
        <h2>All Issues<span class="count">{count} published</span></h2>
      </div>
      <div class="search">
        <input id="q" type="search" placeholder="Search issues…" autocomplete="off" aria-label="Search issues" />
      </div>
    </div>

    <div class="filters" id="filters">{pills}</div>

    <section class="grid" id="grid">
{cards}
      <div class="empty" id="empty" hidden>No issues match your filters.</div>
    </section>
  </div>

  <footer class="site-footer">
    <div class="ft">The <span>Signal</span></div>
    <p>Curated by Efia Amankwa · AI Product Manager, Public Markets</p>
    <div><button class="foot-sub" type="button" data-subscribe>Subscribe for the daily brief →</button></div>
    <div class="meta">{count} ISSUES · SITE REBUILT {built.upper()}</div>
  </footer>

  <div class="modal" id="subModal" hidden role="dialog" aria-modal="true" aria-label="Subscribe to The Signal">
    <div class="backdrop" data-close></div>
    <div class="dialog">
      <div class="top">
        <button class="x" type="button" data-close aria-label="Close">×</button>
        <div class="ey">The Signal · Daily Brief</div>
        <h3>Never miss the signal.</h3>
        <p>One sharp read each morning — AI, public markets, and product — straight to your inbox.</p>
      </div>
      <div class="body">
        <form id="subForm">
          <input id="subEmail" type="email" required placeholder="you@company.com" aria-label="Email address" />
          <button class="sub" type="submit">Subscribe</button>
          <div class="fine">Free · No spam · Unsubscribe anytime</div>
        </form>
        <div class="done" id="subDone" hidden>
          <div class="tick">✓</div>
          <p>Almost there — your email app will open to send the confirmation. Hit send and you're on the list.</p>
        </div>
      </div>
    </div>
  </div>

  <script>{INDEX_JS}</script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────────
# Article pages (modern redesign)
# ──────────────────────────────────────────────────────────────────────────

ARTICLE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700;800;900&family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#14142b;--ink-2:#1d1d3a;--paper:#f6f3ec;--gold:#c9a96e;--gold-soft:#e3cfa6;--muted:#8a8fa8;--muted-d:#5b5f78;--line:#e8e3d8;--card:#fff}
html{scroll-behavior:smooth}
body{background:var(--paper);font-family:'Inter',sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:90;background:linear-gradient(90deg,var(--gold),var(--gold-soft))}
.anav{position:sticky;top:0;z-index:60;display:flex;align-items:center;justify-content:space-between;padding:13px 24px;background:rgba(20,20,43,.78);backdrop-filter:saturate(160%) blur(14px);-webkit-backdrop-filter:saturate(160%) blur(14px);border-bottom:1px solid rgba(201,169,110,.18)}
.anav .back{font-family:'Playfair Display',serif;font-weight:800;font-size:17px;color:var(--paper)}
.anav .back span{color:var(--gold)}
.anav .back:hover{opacity:.85}
.anav .meta{font-family:'Space Mono',monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#b9bcd0;display:none}
@media (min-width:680px){.anav .meta{display:block}}
.anav .sub{border:none;cursor:pointer;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink);background:var(--gold);padding:8px 14px;border-radius:999px}
.anav .sub:hover{transform:translateY(-1px)}
.ahero{position:relative;min-height:64vh;display:flex;align-items:flex-end;color:var(--paper);overflow:hidden;isolation:isolate}
.ahero .bg{position:absolute;inset:0;z-index:-2;background-size:cover;background-position:center;transform:scale(1.05)}
.ahero .scrim{position:absolute;inset:0;z-index:-1;background:linear-gradient(180deg,rgba(20,20,43,.45) 0%,rgba(20,20,43,.6) 45%,rgba(20,20,43,.92) 100%)}
.ahero .inner{max-width:820px;margin:0 auto;width:100%;padding:48px 24px 56px;text-align:center}
.ahero .eyebrow{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--gold);margin-bottom:18px}
.ahero h1{font-family:'Playfair Display',serif;font-weight:900;font-size:clamp(46px,9vw,88px);line-height:.95;letter-spacing:-1.5px}
.ahero h1 span{background:linear-gradient(120deg,var(--gold),var(--gold-soft));-webkit-background-clip:text;background-clip:text;color:transparent}
.ahero .tag{margin-top:18px;font-size:14px;font-weight:300;letter-spacing:.5px;color:#d4d6e4}
.date-bar{margin:26px auto 0;max-width:520px;display:flex;justify-content:center;gap:18px;flex-wrap:wrap;align-items:center;padding-top:18px;border-top:1px solid rgba(255,255,255,.16)}
.date-bar span{font-family:'Space Mono',monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#c2c5d8}
.date-bar .issue{background:var(--gold);color:var(--ink);padding:3px 11px;border-radius:999px;font-weight:700}
.intro{background:var(--gold);color:var(--ink)}
.intro p{max-width:760px;margin:0 auto;padding:26px 24px;font-size:15.5px;line-height:1.75;font-weight:400}
.intro p strong{font-weight:700}
.acontent{max-width:820px;margin:0 auto;padding:8px 24px 40px;position:relative}
.stat-row{display:flex;gap:14px;margin:40px 0 8px;flex-wrap:wrap}
.stat-card{flex:1;min-width:150px;background:var(--ink);border-radius:12px;padding:24px 18px;text-align:center;transition:transform .2s,box-shadow .2s}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 18px 36px -20px rgba(20,20,43,.6)}
.stat-card .number{font-family:'Playfair Display',serif;font-size:36px;font-weight:800;color:var(--gold);line-height:1}
.stat-card .label{font-size:10px;font-weight:500;color:#a7abc4;letter-spacing:.8px;text-transform:uppercase;margin-top:10px;line-height:1.5}
.toc{position:fixed;top:50%;right:max(16px,calc((100vw - 820px)/2 - 150px));transform:translateY(-50%);z-index:40;display:none;flex-direction:column;gap:10px}
@media (min-width:1180px){.toc{display:flex}}
.toc a{display:flex;align-items:center;gap:9px;font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted-d);opacity:.6;transition:opacity .15s,color .15s}
.toc a .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.toc a.active{opacity:1;color:var(--ink);font-weight:700}
.section{padding-top:52px}
.sec-banner{position:relative;height:128px;border-radius:14px;overflow:hidden;background-size:cover;background-position:center;display:flex;align-items:flex-end}
.sec-banner .sec-scrim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,20,43,.3),rgba(20,20,43,.8))}
.sec-banner .sec-head{position:relative;z-index:2;display:flex;align-items:center;gap:12px;padding:20px 24px}
.sec-banner .dot{width:10px;height:10px;border-radius:50%}
.sec-banner h2{font-family:'Inter',sans-serif;font-size:13px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#fff}
.dot.markets{background:#3a9bcf}.dot.tools{background:#5aa83a}.dot.labs{background:#b54a9e}.dot.pm{background:#cf9a3a}.dot.risk{background:#cf524a}
.stories{margin-top:22px;display:flex;flex-direction:column;gap:22px}
.story{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:30px 32px;transition:transform .2s,box-shadow .2s,border-color .2s}
.story:hover{transform:translateY(-3px);box-shadow:0 22px 44px -26px rgba(20,20,43,.4);border-color:transparent}
.story .tag{display:inline-flex;align-items:center;gap:6px;font-family:'Space Mono',monospace;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:5px 10px;border-radius:999px;margin-bottom:14px}
.story .tag .ic{width:12px;height:12px}
.tag.markets{background:#e8f4f8;color:#2a7fa8}.tag.tools{background:#eef8e6;color:#4a8a2a}.tag.labs{background:#f8e8f4;color:#8a2a7a}.tag.pm{background:#f8f0e8;color:#8a5a2a}.tag.risk{background:#f8e8e8;color:#8a2a2a}
.story h3{font-family:'Playfair Display',serif;font-size:24px;font-weight:700;line-height:1.25;letter-spacing:-.3px;margin-bottom:12px}
.story > p{font-size:15px;line-height:1.8;color:#42445a}
.story > p strong{color:var(--ink);font-weight:600}
.why-it-matters{margin-top:16px;padding:16px 20px;background:#faf7f0;border-left:3px solid var(--gold);border-radius:0 8px 8px 0}
.why-it-matters p{font-size:13px;line-height:1.7;color:#5a5a6e;font-style:italic}
.why-it-matters strong{color:var(--ink);font-style:normal;font-weight:700}
.source{display:inline-flex;align-items:center;gap:7px;margin-top:18px;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--ink);border:1.5px solid var(--ink);border-radius:999px;padding:9px 16px;transition:background .15s,color .15s}
.source:hover{background:var(--ink);color:var(--gold)}
.js .reveal{opacity:0;transform:translateY(24px);transition:opacity .6s ease,transform .6s ease}
.js .reveal.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.js .reveal{opacity:1;transform:none;transition:none}.ahero .bg{transform:none}}
.afooter{background:var(--ink);color:var(--muted);text-align:center;padding:54px 24px}
.afooter .ft{font-family:'Playfair Display',serif;color:var(--paper);font-size:24px;font-weight:800;margin-bottom:6px}
.afooter .ft span{color:var(--gold)}
.afooter p{font-size:12px;line-height:1.9}
.afooter .actions{margin-top:20px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.afooter .b{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:11px 20px;border-radius:999px;cursor:pointer;border:1px solid rgba(255,255,255,.2);color:var(--paper);background:none}
.afooter .b.gold{background:var(--gold);color:var(--ink);border-color:var(--gold)}
.afooter .b:hover{transform:translateY(-1px)}
@media (max-width:560px){.story{padding:24px 22px}.ahero{min-height:56vh}}
"""

ARTICLE_JS = """
(function(){
  const prog=document.getElementById('progress');
  function onScroll(){var h=document.documentElement;var sc=h.scrollTop||document.body.scrollTop;var max=h.scrollHeight-h.clientHeight;prog.style.width=(max>0?(sc/max*100):0)+'%';}
  document.addEventListener('scroll',onScroll,{passive:true});onScroll();
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
  var toc=document.getElementById('toc');
  if(toc){
    var links=[].slice.call(toc.querySelectorAll('a'));
    var map={};links.forEach(function(l){map[l.dataset.target]=l;});
    var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(x){x.classList.remove('active');});var a=map[e.target.id];if(a)a.classList.add('active');}});},{rootMargin:'-40% 0px -55% 0px'});
    document.querySelectorAll('.section').forEach(function(s){so.observe(s);});
  }
  document.querySelectorAll('[data-subscribe]').forEach(function(b){b.addEventListener('click',function(){window.location.href='../index.html#top';});});
})();
"""


def render_article(d, idx=0):
    num = html.escape(d["num"] or str(idx + 1))
    hero = issue_image(d["num"], idx, "../") or ""
    title = d["title"] or "The Signal"

    toc_links = ""
    secs_html = ""
    for si, s in enumerate(d["sectionlist"]):
        secimg = section_image(s["dot"]) or ""
        stories_html = ""
        for st in s["stories"]:
            ic = icon_svg(st["tagcls"])
            stories_html += f"""
            <article class="story reveal">
              <span class="tag {st['tagcls']}">{ic}{st['tag']}</span>
              <h3>{st['title']}</h3>
              <p>{st['body']}</p>
              <div class="why-it-matters"><p>{st['why']}</p></div>
              <a class="source" href="{st['href']}" target="_blank" rel="noopener">{st['link']}</a>
            </article>"""
        toc_links += f"""<a href="#sec-{si}" data-target="sec-{si}"><span class="dot {s['dot']}"></span>{s['name']}</a>"""
        secs_html += f"""
        <section class="section sec reveal" id="sec-{si}">
          <div class="sec-banner" style="background-image:url('{secimg}')">
            <div class="sec-scrim"></div>
            <div class="sec-head"><span class="dot {s['dot']}"></span><h2>{s['name']}</h2></div>
          </div>
          <div class="stories">{stories_html}</div>
        </section>"""

    stats_html = "".join(
        f'<div class="stat-card"><div class="number">{n}</div><div class="label">{l}</div></div>'
        for n, l in d["stat_cards"]
    )
    stat_row = f'<div class="stat-row">{stats_html}</div>' if stats_html else ""

    return f"""<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
  <script>document.documentElement.className = 'js';</script>
  <style>{ARTICLE_CSS}</style>
</head>
<body>
  <div class="progress" id="progress"></div>

  <nav class="anav">
    <a class="back" href="../index.html">← The <span>Signal</span></a>
    <span class="meta">{d['issue']} · {d['date_label']}</span>
    <button class="sub" type="button" data-subscribe>Subscribe</button>
  </nav>

  <header class="ahero">
    <div class="bg" style="background-image:url('{hero}')"></div>
    <div class="scrim"></div>
    <div class="inner">
      <div class="eyebrow">{d['eyebrow']}</div>
      <h1>The <span>Signal</span></h1>
      <p class="tag">AI · Public Markets · Product Management</p>
      <div class="date-bar">
        <span>{d['date_label']}</span>
        <span class="issue">{d['issue']}</span>
        <span>Curated for Efia</span>
      </div>
    </div>
  </header>

  <div class="intro"><p>{d['intro_html']}</p></div>

  <nav class="toc" id="toc">{toc_links}</nav>

  <main class="acontent">
    {stat_row}
    {secs_html}
  </main>

  <footer class="afooter">
    <div class="ft">The <span>Signal</span></div>
    <p>Curated for Efia Amankwa · AI Product Manager, Public Markets<br/>{d['issue']} · {d['date_label']}</p>
    <div class="actions">
      <a class="b gold" href="../index.html">← Back to all issues</a>
      <button class="b" type="button" data-subscribe>Subscribe</button>
    </div>
  </footer>

  <script>{ARTICLE_JS}</script>
</body>
</html>
"""


def main():
    issues = collect()
    OUTPUT.write_text(render(issues), encoding="utf-8")
    for idx, d in enumerate(issues):
        if not d.get("external"):
            (NEWSLETTERS / d["file"]).write_text(render_article(d, idx), encoding="utf-8")
    print(f"Built index.html + {len(issues)} article page(s) from {len(_IMAGES)} image(s):")
    for i in issues:
        n_stories = sum(len(s["stories"]) for s in i["sectionlist"])
        print(f"  · {i['issue']:<14} {i['date_label']:<16} {i['file']:<22} {len(i['sectionlist'])} sections / {n_stories} stories")


if __name__ == "__main__":
    main()
