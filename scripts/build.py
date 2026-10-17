#!/usr/bin/env python3
"""AI Brief static site generator. Reads data/articles.json, writes HTML + sitemap + robots."""
import json, os, html, shutil, re, hashlib
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "articles.json")
STATIC = os.path.join(ROOT, "static")
OUT = ROOT  # generate into repo root for Vercel static serving

with open(DATA) as f:
    site_data = json.load(f)
SITE = site_data["site"]
ARTICLES = sorted(
    [a for a in site_data["articles"] if not a.get("draft")],
    key=lambda a: a["date"], reverse=True,
)

# slug, name, emoji, desc, badge class, base hue
CATS = [
    ("ai-news",    "AI News",    "📰", "Breaking stories and developments from the AI world.", "news",       250),
    ("ai-tools",   "AI Tools",   "🛠️", "Hand-picked AI tools, comparisons, and roundups.",        "tools",      160),
    ("tutorials",  "Tutorials",  "🎯", "Step-by-step guides to get more from AI.",                "tutorials",    35),
    ("explainers", "Explainers", "📖", "Big AI ideas explained in plain English.",               "explainers",   330),
]
CATMAP = {slug: (name, emoji, desc, badge, hue) for slug, name, emoji, desc, badge, hue in CATS}
CAT_BY_NAME = {name: slug for slug, name, _, _, _, _ in CATS}

CSS = "css/style.css"
JS = "js/app.js"
GA4 = SITE.get("ga4", "G-XXXXXXXXXX")
URL = SITE["url"].rstrip("/")

def esc(t): return html.escape(t or "")

def art_grad(slug, category):
    """Deterministic premium gradient for an article."""
    _, _, _, _, base = CATMAP.get(CAT_BY_NAME.get(category, "ai-news"), ("", "", "", "", 250))
    h = int(hashlib.md5(slug.encode()).hexdigest()[:4], 16)
    h1 = (base + (h % 44) - 22) % 360
    h2 = (h1 + 55) % 360
    return f"linear-gradient(135deg,hsl({h1},62%,42%),hsl({h2},68%,30%))"

def art_div(a, letter_size="4.2rem", cls=""):
    letter = esc(a["title"].lstrip()[0].upper()) if a["title"] else "A"
    return (f'<div class="art {cls}" style="background:{art_grad(a["slug"], a["category"])}">'
            f'<span class="art-letter" style="font-size:{letter_size}">{letter}</span></div>')

def badge(a):
    _, _, _, b, _ = CATMAP.get(CAT_BY_NAME.get(a["category"], "ai-news"), ("", "", "", "news", 0))
    return f'<span class="badge {b}">{esc(a["category"])}</span>'

def fmt_date(d):
    try:
        y, m, dd = d.split("-")
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        return f"{months[int(m)-1]} {int(dd)}, {y}"
    except Exception:
        return d

def head(title, desc, canonical, schema_json="", og_type="website"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{CSS}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%234f46e5'/><text x='50' y='68' font-size='52' text-anchor='middle' fill='white' font-family='Georgia'>A</text></svg>">
<!-- Google tag (gtag.js) — replace G-XXXXXXXXXX with your GA4 Measurement ID -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag("js", new Date());
gtag("config", "{GA4}");
</script>
{schema_json}
</head>"""

def header(active="home", ticker_items=None):
    def nav(href, label, key):
        cls = ' class="active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    ticker = ""
    if ticker_items:
        links = "".join(f'<a href="articles/{a["slug"]}.html">{esc(a["title"])}</a>' for a in ticker_items[:8])
        ticker = f'<div class="ticker" aria-hidden="true"><div class="ticker-inner"><span class="tick-label">Latest</span>{links}{links}</div></div>'
    return f"""<body>
{ticker}
<header class="site-header">
<div class="wrap header-inner">
<a class="logo" href="index.html"><span class="logo-mark">🤖</span><span><em>AI</em> Brief</span></a>
<button class="icon-btn hamburger" id="hamburger" aria-label="Menu">☰</button>
<nav class="main-nav" id="mainNav">
{nav("index.html","Home","home")}
{nav("ai-news.html","AI News","ai-news")}
{nav("ai-tools.html","AI Tools","ai-tools")}
{nav("tutorials.html","Tutorials","tutorials")}
{nav("explainers.html","Explainers","explainers")}
{nav("about.html","About","about")}
</nav>
<div class="header-actions">
<button class="icon-btn" data-search-open aria-label="Search (Ctrl+K)" title="Search (Ctrl+K)">🔍</button>
<button class="icon-btn theme-toggle" aria-label="Toggle dark mode">🌙</button>
<button class="btn-subscribe" data-subscribe>Subscribe</button>
</div>
</div>
</header>
<div class="search-overlay" id="searchOverlay">
<div class="search-box">
<input type="text" id="searchInput" placeholder="Search AI news, tools, guides…" autocomplete="off">
<div class="search-results" id="searchResults"></div>
</div>
</div>"""

FOOTER = f"""<footer class="site-footer">
<div class="wrap footer-top">
<div class="footer-brand">
<a class="logo" href="index.html"><span class="logo-mark">🤖</span><span><em>AI</em> Brief</span></a>
<p style="margin-top:12px">AI news &amp; tools, explained simply. Original briefs, honest takes, and practical guides — published daily for a worldwide audience.</p>
</div>
<div>
<h4>Sections</h4>
<ul>
<li><a href="ai-news.html">AI News</a></li>
<li><a href="ai-tools.html">AI Tools</a></li>
<li><a href="tutorials.html">Tutorials</a></li>
<li><a href="explainers.html">Explainers</a></li>
</ul>
</div>
<div>
<h4>Site</h4>
<ul>
<li><a href="about.html">About</a></li>
<li><a href="contact.html">Contact</a></li>
<li><a href="privacy.html">Privacy Policy</a></li>
</ul>
</div>
<div class="footer-nl">
<h4>Newsletter</h4>
<p>One short email per week. The most important AI stories, zero spam.</p>
<form id="nlFormFooter"><input type="email" placeholder="you@example.com" required aria-label="Email"><button type="submit">Join</button></form>
<p class="nl-note" id="nlNoteFooter" style="font-size:.82rem"></p>
</div>
</div>
<div class="wrap footer-bottom">
<p>© {date.today().year} AI Brief. Original summaries with source links; all trademarks belong to their owners.</p>
<p>Made with 🤖 for the AI-curious.</p>
</div>
</footer>
<script src="{JS}"></script>
</body>
</html>"""

NEWSLETTER = """<section class="newsletter reveal">
<h2>Get the AI Brief in your inbox</h2>
<p>One short email per week. The most important AI stories, zero spam. Join thousands of AI-curious readers.</p>
<div class="stats">
<div><strong>12+</strong>Original briefs</div>
<div><strong>4</strong>Sections</div>
<div><strong>0</strong>Spam, ever</div>
</div>
<form id="nlForm"><input type="email" id="nlEmail" placeholder="you@example.com" required aria-label="Email"><button type="submit">Subscribe free</button></form>
<p class="nl-note" id="nlNote"></p>
</section>"""

def card(a):
    return f"""<a class="card reveal" href="articles/{a['slug']}.html">
{art_div(a)}
<div class="card-body">
{badge(a)}
<h3>{esc(a['title'])}</h3>
<p>{esc(a['excerpt'])}</p>
<div class="meta"><span>{fmt_date(a['date'])}</span><span class="dot">•</span><span>{a['read_minutes']} min read</span></div>
</div>
</a>"""

def why_boxify(body):
    """Wrap the 'Why it matters' paragraph in a styled callout."""
    def repl(m):
        inner = m.group(1)
        inner = re.sub(r"^<strong>Why it matters:</strong>\s*", "", inner)
        return ('<div class="why-box"><h4>💡 Why it matters</h4><p>' + inner + "</p></div>")
    return re.sub(r"<p><strong>Why it matters:</strong>(.*?)</p>", repl, body, flags=re.S)

def article_schema(a, canonical, cat_slug):
    s = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": a["title"],
        "description": a["excerpt"],
        "datePublished": a["date"],
        "dateModified": a["date"],
        "author": {"@type": "Organization", "name": "AI Brief", "url": URL},
        "publisher": {"@type": "Organization", "name": "AI Brief", "url": URL},
        "mainEntityOfPage": canonical,
    }
    bc = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": URL + "/"},
            {"@type": "ListItem", "position": 2, "name": a["category"], "item": f"{URL}/{cat_slug}.html"},
            {"@type": "ListItem", "position": 3, "name": a["title"]},
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(s) + "</script>\n" + \
           '<script type="application/ld+json">' + json.dumps(bc) + "</script>"

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ---------- static assets ----------
shutil.copytree(os.path.join(STATIC, "css"), os.path.join(OUT, "css"), dirs_exist_ok=True)
shutil.copytree(os.path.join(STATIC, "js"), os.path.join(OUT, "js"), dirs_exist_ok=True)

# ---------- homepage ----------
featured = ARTICLES[0]
side = ARTICLES[1:4]
latest = ARTICLES[1:9]
cat_sections = ""
for slug, name, emoji, desc, _, _ in CATS:
    items = [a for a in ARTICLES if a["category"] == name][:3]
    if not items: continue
    cat_sections += (f'<section class="cat-section"><div class="section-head reveal">'
                     f'<h2><span class="sec-emoji">{emoji}</span>{name}</h2>'
                     f'<a href="{slug}.html">View all →</a></div>'
                     f'<div class="grid">{"".join(card(a) for a in items)}</div></section>')

latest_html = "".join(
    f"""<a class="latest-item reveal" href="articles/{a['slug']}.html">
<span class="latest-num">{i:02d}</span>
<div><h3>{esc(a['title'])}</h3><p>{esc(a['excerpt'])}</p>
<div class="meta">{badge(a)}<span>{fmt_date(a['date'])}</span><span class="dot">•</span><span>{a['read_minutes']} min read</span></div></div>
</a>""" for i, a in enumerate(latest, 1))

side_html = "".join(
    f"""<a class="hero-side-card reveal" href="articles/{a['slug']}.html">
{art_div(a, letter_size="2.6rem")}
<div><h3>{esc(a['title'])}</h3><div class="meta"><span>{fmt_date(a['date'])}</span><span class="dot">•</span><span>{a['read_minutes']} min</span></div></div>
</a>""" for a in side)

home_schema = '<script type="application/ld+json">' + json.dumps({
    "@context": "https://schema.org", "@type": "WebSite",
    "name": SITE["name"], "url": URL + "/",
    "description": SITE["description"],
    "potentialAction": {"@type": "SearchAction",
        "target": URL + "/?q={search_term_string}",
        "query-input": "required name=search_term_string"},
}) + "</script>"

write("index.html", head(f"{SITE['name']} — {SITE['tagline']}", SITE["description"], URL + "/", home_schema) + header("home", ARTICLES) + f"""
<main class="wrap">
<section class="hero-grid">
<a class="hero-main reveal" href="articles/{featured['slug']}.html">
{art_div(featured, letter_size="11rem")}
<div class="hero-content">
<span class="kicker">✨ Featured story</span>
<h1>{esc(featured['title'])}</h1>
<p>{esc(featured['excerpt'])}</p>
<div class="hero-meta"><span>{badge(featured)}</span><span>{fmt_date(featured['date'])}</span><span>·</span><span>{featured['read_minutes']} min read</span></div>
</div>
</a>
<div class="hero-side">{side_html}</div>
</section>

<section><div class="section-head reveal"><h2><span class="sec-emoji">🕐</span>Latest briefs</h2><a href="ai-news.html">More news →</a></div>
<div class="latest-list">{latest_html}</div></section>

{cat_sections}
{NEWSLETTER}
</main>
""" + FOOTER)

# ---------- category pages ----------
for slug, name, emoji, desc, _, _ in CATS:
    items = [a for a in ARTICLES if a["category"] == name]
    h1 = (int(hashlib.md5(slug.encode()).hexdigest()[:4], 16) % 44) - 22
    hero_bg = f"linear-gradient(135deg,hsl({250+h1},60%,45%),hsl({295+h1},65%,32%))"
    cards = "".join(card(a) for a in items) if items else "<p>No articles yet.</p>"
    write(f"{slug}.html",
        head(f"{name} — {SITE['name']}", desc, f"{URL}/{slug}.html") + header(slug, ARTICLES) + f"""
<main class="wrap">
<section class="page-hero reveal" style="background:{hero_bg}">
<h1>{emoji} {name}</h1>
<p>{desc}</p>
</section>
<section style="margin-top:28px"><div class="grid">{cards}</div></section>
{NEWSLETTER}
</main>
""" + FOOTER)

# ---------- article pages ----------
for idx, a in enumerate(ARTICLES):
    canonical = f"{URL}/articles/{a['slug']}.html"
    cat_slug = CAT_BY_NAME.get(a["category"], "ai-news")
    related = [x for x in ARTICLES if x["category"] == a["category"] and x["slug"] != a["slug"]][:3]
    if len(related) < 3:
        related += [x for x in ARTICLES if x["slug"] != a["slug"] and x not in related][:3-len(related)]
    prev_a = ARTICLES[idx - 1] if idx > 0 else None
    next_a = ARTICLES[idx + 1] if idx + 1 < len(ARTICLES) else None
    trending = [x for x in ARTICLES if x["slug"] != a["slug"]][:5]
    body = why_boxify(a["body"])
    pn = ""
    if prev_a or next_a:
        pn = '<nav class="pn-nav">'
        pn += (f'<a class="pn-card prev reveal" href="{prev_a["slug"]}.html"><span>← Newer</span><h4>{esc(prev_a["title"])}</h4></a>' if prev_a else '<span></span>')
        pn += (f'<a class="pn-card next reveal" href="{next_a["slug"]}.html"><span>Older →</span><h4>{esc(next_a["title"])}</h4></a>' if next_a else '<span></span>')
        pn += "</nav>"
    write(f"articles/{a['slug']}.html",
        head(a["title"] + f" — {SITE['name']}", a["excerpt"], canonical, article_schema(a, canonical, cat_slug), og_type="article") + header("", ARTICLES) + f"""
<div class="progress-bar" id="progressBar"></div>
<main class="wrap">
<nav class="crumbs"><a href="../index.html">Home</a> &nbsp;/&nbsp; <a href="../{cat_slug}.html">{esc(a['category'])}</a> &nbsp;/&nbsp; <span>{esc(a['title'][:42])}…</span></nav>
<div class="article-layout">
<div class="article-main">
<article>
{badge(a)}
<h1>{esc(a['title'])}</h1>
<p class="lede">{esc(a['excerpt'])}</p>
<div class="byline">
<div class="avatar">A</div>
<div class="who"><strong>AI Brief</strong><span>{fmt_date(a['date'])} · {a['read_minutes']} min read</span></div>
<div class="share-row">
<button class="share-btn" data-share="x" aria-label="Share on X" title="Share on X">𝕏</button>
<button class="share-btn" data-share="linkedin" aria-label="Share on LinkedIn" title="Share on LinkedIn">in</button>
<button class="share-btn" data-share="copy" aria-label="Copy link" title="Copy link">🔗</button>
</div>
</div>
<div class="article-cover"><div class="art" style="background:{art_grad(a['slug'], a['category'])}"><span class="art-letter" style="font-size:8rem">{esc(a['title'].lstrip()[0].upper())}</span></div></div>
<div class="article-body">{body}</div>
<div class="source-box">🔗 <strong>Source:</strong> <a href="{a['source_url']}" rel="nofollow noopener" target="_blank">{esc(a['source_name'])}</a><p class="fine">This is an original summary with commentary. Read the full story at the source.</p></div>
<div class="tags">{' '.join(f'<span class="tag">#{esc(t)}</span>' for t in a.get('tags', []))}</div>
<div class="author-box">
<div class="avatar">A</div>
<div><h4>AI Brief</h4><p>AI news &amp; tools, explained simply. Original briefs with honest takes, published daily for readers worldwide.</p></div>
</div>
</article>
{pn}
</div>
<aside class="sidebar">
<div class="side-card reveal">
<h4>🔥 Trending</h4>
<ol>{"".join(f'<li><a href="{x["slug"]}.html">{esc(x["title"])}</a></li>' for x in trending)}</ol>
</div>
<div class="side-card side-nl reveal">
<h4>📬 Weekly AI Brief</h4>
<p>The most important AI stories, once a week. Zero spam.</p>
<form id="nlFormSide"><input type="email" placeholder="you@example.com" required aria-label="Email"><button type="submit">Subscribe</button></form>
<p class="nl-note" id="nlNoteSide" style="font-size:.82rem"></p>
</div>
</aside>
</div>
{f'<section><div class="section-head reveal"><h2>Related briefs</h2></div><div class="grid">{"".join(card(x) for x in related)}</div></section>' if related else ''}
</main>
""" + FOOTER)

# ---------- search.json ----------
search_index = [{
    "title": a["title"], "excerpt": a["excerpt"], "category": a["category"],
    "date": fmt_date(a["date"]), "tags": a.get("tags", []),
    "url": f"articles/{a['slug']}.html",
    "grad": art_grad(a["slug"], a["category"]),
    "letter": a["title"].lstrip()[0].upper(),
} for a in ARTICLES]
write("search.json", json.dumps(search_index))

# ---------- static pages ----------
ABOUT_BODY = """<p><strong>AI Brief</strong> covers artificial intelligence news, tools, and tutorials in plain English — no hype, no jargon — for readers worldwide.</p><p>Every brief is an <strong>original summary with commentary</strong>, written to help you understand what happened and why it matters. We always link to the original source so you can read more and so publishers get the credit they deserve.</p><h2>How we're made</h2><p>AI Brief is an AI-assisted publication. Stories are drafted with AI help from public sources, then shaped into original briefs with our own analysis. We never reproduce articles — we summarize, contextualize, and link out.</p><h2>Corrections & takedowns</h2><p>Found an error or own content you'd like removed? <a href="contact.html">Contact us</a> and we'll respond within 48 hours.</p>"""
CONTACT_BODY = """<p>Questions, corrections, takedown requests, or partnership ideas — reach out:</p><p>📧 <strong>Email:</strong> <a href="mailto:hello@ainews.vercel.app">hello@ainews.vercel.app</a></p><p>We aim to respond within 48 hours. For content takedown requests, please include the article URL and proof of ownership.</p>"""
PRIVACY_BODY = """<p>AI Brief respects your privacy.</p><h2>What we collect</h2><p>We use Google Analytics (GA4) to understand aggregate traffic patterns — pages visited, approximate location, device type. We do not collect names, emails, or personal identifiers unless you voluntarily subscribe to the newsletter.</p><h2>Cookies</h2><p>Analytics cookies help us improve the site. You can disable cookies in your browser settings.</p><h2>Third parties</h2><p>We do not sell your data. Analytics data is processed by Google under their privacy policy.</p><h2>Contact</h2><p>Privacy questions: <a href="mailto:hello@ainews.vercel.app">hello@ainews.vercel.app</a></p>"""

for fname, title, desc_text, body_html, emoji in [
    ("about.html", "About — AI Brief", "What AI Brief is and how it works.", ABOUT_BODY, "ℹ️"),
    ("contact.html", "Contact — AI Brief", "Contact AI Brief for corrections, takedowns, or partnerships.", CONTACT_BODY, "✉️"),
    ("privacy.html", "Privacy Policy — AI Brief", "AI Brief privacy policy: what we collect and why.", PRIVACY_BODY, "🔒"),
]:
    key = fname.replace(".html", "")
    write(fname, head(title, desc_text, f"{URL}/{fname}") + header(key, ARTICLES) + f"""
<main class="wrap static-page"><h1>{emoji} {esc(title.split(' — ')[0])}</h1><div class="article-body">{body_html}</div></main>
""" + FOOTER)

# ---------- sitemap.xml ----------
urls = ["", "ai-news.html", "ai-tools.html", "tutorials.html", "explainers.html",
        "about.html", "contact.html", "privacy.html"] + [f"articles/{a['slug']}.html" for a in ARTICLES]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append(f"  <url><loc>{URL}/{u}</loc><changefreq>daily</changefreq></url>")
sm.append("</urlset>")
write("sitemap.xml", "\n".join(sm))

# ---------- news sitemap ----------
ns = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
for a in ARTICLES:
    ns.append(f"""  <url><loc>{URL}/articles/{a['slug']}.html</loc>
    <news:news><news:publication><news:name>AI Brief</news:name><news:language>en</news:language></news:publication>
    <news:publication_date>{a['date']}</news:publication_date><news:title>{esc(a['title'])}</news:title></news:news></url>""")
ns.append("</urlset>")
write("news-sitemap.xml", "\n".join(ns))

# ---------- robots.txt ----------
write("robots.txt", f"""User-agent: *
Allow: /
Sitemap: {URL}/sitemap.xml
Sitemap: {URL}/news-sitemap.xml
""")

print(f"Built {len(ARTICLES)} articles, {len(urls)} URLs → {OUT}")
