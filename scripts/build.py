#!/usr/bin/env python3
"""AI Brief static site generator. Reads data/articles.json, writes HTML + sitemap + robots."""
import json, os, html, shutil
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

CATS = [
    ("ai-news", "AI News", "📰", "Breaking stories and developments from the AI world."),
    ("ai-tools", "AI Tools", "🛠️", "Hand-picked AI tools, comparisons, and roundups."),
    ("tutorials", "Tutorials", "🎯", "Step-by-step guides to get more from AI."),
    ("explainers", "Explainers", "📖", "Big AI ideas explained in plain English."),
]
CATMAP = {slug: (name, emoji, desc) for slug, name, emoji, desc in CATS}

CSS = "css/style.css"
JS = "js/app.js"
GA4 = SITE.get("ga4", "G-XXXXXXXXXX")
URL = SITE["url"].rstrip("/")

def esc(t): return html.escape(t or "")

def head(title, desc, canonical, schema_json="", og_type="website", image_emoji="🤖"):
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
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{CSS}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>{image_emoji}</text></svg>">
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

def header(active="home"):
    def nav(href, label, key):
        cls = ' class="active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    return f"""<body>
<header class="site-header">
<div class="wrap header-inner">
<a class="logo" href="index.html">🤖 <span>AI</span> Brief</a>
<nav class="main-nav">
{nav("index.html","Home","home")}
{nav("ai-news.html","AI News","ai-news")}
{nav("ai-tools.html","AI Tools","ai-tools")}
{nav("tutorials.html","Tutorials","tutorials")}
{nav("explainers.html","Explainers","explainers")}
{nav("about.html","About","about")}
</nav>
<button class="theme-toggle" id="themeToggle" aria-label="Toggle dark mode">🌙</button>
</div>
</header>"""

FOOTER = f"""<footer class="site-footer">
<div class="wrap footer-grid">
<div>
<h4>🤖 AI Brief</h4>
<p>{esc(SITE['tagline'])}. Original briefs, honest takes, and practical guides — published daily.</p>
</div>
<div>
<h4>Sections</h4>
<p><a href="ai-news.html">AI News</a><br><a href="ai-tools.html">AI Tools</a><br><a href="tutorials.html">Tutorials</a><br><a href="explainers.html">Explainers</a></p>
</div>
<div>
<h4>Site</h4>
<p><a href="about.html">About</a><br><a href="contact.html">Contact</a><br><a href="privacy.html">Privacy Policy</a></p>
</div>
</div>
<div class="wrap footer-bottom">
<p>© {date.today().year} AI Brief. Summaries are original commentary with source links; all trademarks belong to their owners.</p>
</div>
</footer>
<script src="{JS}"></script>
</body>
</html>"""

def card(a):
    cat_name, cat_emoji, _ = CATMAP[a["category"]] if False else ("", "", "")
    return f"""<a class="card" href="articles/{a['slug']}.html">
<div class="card-emoji">{a['emoji']}</div>
<div class="card-body">
<span class="badge">{esc(a['category'])}</span>
<h3>{esc(a['title'])}</h3>
<p>{esc(a['excerpt'])}</p>
<div class="meta"><span>{a['date']}</span> · <span>{a['read_minutes']} min read</span></div>
</div>
</a>"""

def article_schema(a, canonical):
    body_text = esc(" ".join(a["body"].replace("<p>"," ").replace("</p>"," ").replace("<strong>","").replace("</strong>","").replace("<em>","").replace("</em>","").split())[:60])
    s = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": a["title"],
        "description": a["excerpt"],
        "datePublished": a["date"],
        "dateModified": a["date"],
        "author": {"@type": "Organization", "name": "AI Brief"},
        "publisher": {"@type": "Organization", "name": "AI Brief", "url": URL},
        "mainEntityOfPage": canonical,
    }
    return '<script type="application/ld+json">' + json.dumps(s) + "</script>"

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
rest = ARTICLES[1:]
cat_sections = ""
for slug, name, emoji, desc in CATS:
    items = [a for a in ARTICLES if a["category"] == name][:3]
    if not items: continue
    cat_sections += f"""<section class="cat-section"><div class="section-head"><h2>{emoji} {name}</h2><a href="{slug}.html">View all →</a></div><div class="grid">{''.join(card(a) for a in items)}</div></section>"""

home_schema = '<script type="application/ld+json">' + json.dumps({
    "@context": "https://schema.org", "@type": "WebSite",
    "name": SITE["name"], "url": URL + "/",
    "description": SITE["description"],
}) + "</script>"

write("index.html", head(f"{SITE['name']} — {SITE['tagline']}", SITE["description"], URL + "/", home_schema, image_emoji="🤖") + header("home") + f"""
<main class="wrap">
<section class="hero">
<span class="badge">Featured</span>
<a class="hero-link" href="articles/{featured['slug']}.html">
<div class="hero-emoji">{featured['emoji']}</div>
<h1>{esc(featured['title'])}</h1>
<p>{esc(featured['excerpt'])}</p>
<div class="meta"><span>{featured['date']}</span> · <span>{featured['read_minutes']} min read</span></div>
</a>
</section>
<section><div class="section-head"><h2>🕐 Latest</h2></div><div class="grid">{''.join(card(a) for a in rest)}</div></section>
{cat_sections}
<section class="newsletter"><h2>📬 Get the AI Brief in your inbox</h2><p>One short email per week. The most important AI stories, zero spam.</p><form id="nlForm"><input type="email" id="nlEmail" placeholder="you@example.com" required><button type="submit">Subscribe</button></form><p class="nl-note" id="nlNote"></p></section>
</main>
""" + FOOTER)

# ---------- category pages ----------
for slug, name, emoji, desc in CATS:
    items = [a for a in ARTICLES if a["category"] == name]
    write(f"{slug}.html",
        head(f"{name} — {SITE['name']}", desc, f"{URL}/{slug}.html", image_emoji=emoji) + header(slug) + f"""
<main class="wrap">
<section class="page-head"><h1>{emoji} {name}</h1><p>{desc}</p></section>
<div class="grid">{''.join(card(a) for a in items) if items else '<p>No articles yet.</p>'}</div>
</main>
""" + FOOTER)

# ---------- article pages ----------
for a in ARTICLES:
    canonical = f"{URL}/articles/{a['slug']}.html"
    related = [x for x in ARTICLES if x["category"] == a["category"] and x["slug"] != a["slug"]][:3]
    write(f"articles/{a['slug']}.html",
        head(a["title"] + f" — {SITE['name']}", a["excerpt"], canonical, article_schema(a, canonical), og_type="article", image_emoji=a["emoji"]) + header("") + f"""
<main class="wrap article-page">
<nav class="crumbs"><a href="../index.html">Home</a> / <a href="../{a['category'].lower().replace(' ','-')}.html">{esc(a['category'])}</a></nav>
<article>
<div class="article-emoji">{a['emoji']}</div>
<span class="badge">{esc(a['category'])}</span>
<h1>{esc(a['title'])}</h1>
<div class="meta"><span>By AI Brief</span> · <span>{a['date']}</span> · <span>{a['read_minutes']} min read</span></div>
<p class="lede">{esc(a['excerpt'])}</p>
<div class="article-body">{a['body']}</div>
<div class="source-box">🔗 <strong>Source:</strong> <a href="{a['source_url']}" rel="nofollow noopener" target="_blank">{esc(a['source_name'])}</a><p class="fine">This is an original summary with commentary. Read the full story at the source.</p></div>
<div class="tags">{' '.join(f'<span class="tag">#{esc(t)}</span>' for t in a.get('tags', []))}</div>
</article>
{f'<section><div class="section-head"><h2>Related</h2></div><div class="grid">{"".join(card(x) for x in related)}</div></section>' if related else ''}
</main>
""" + FOOTER)

# ---------- static pages ----------
ABOUT_BODY = """<p><strong>AI Brief</strong> covers artificial intelligence news, tools, and tutorials in plain English — no hype, no jargon.</p><p>Every brief is an <strong>original summary with commentary</strong>, written to help you understand what happened and why it matters. We always link to the original source so you can read more and so publishers get the credit they deserve.</p><h2>How we're made</h2><p>AI Brief is an AI-assisted publication. Stories are drafted with AI help from public sources, then shaped into original briefs with our own analysis. We never reproduce articles — we summarize, contextualize, and link out.</p><h2>Corrections & takedowns</h2><p>Found an error or own content you'd like removed? <a href="contact.html">Contact us</a> and we'll respond within 48 hours.</p>"""
CONTACT_BODY = """<p>Questions, corrections, takedown requests, or partnership ideas — reach out:</p><p>📧 <strong>Email:</strong> <a href="mailto:hello@ainews.vercel.app">hello@ainews.vercel.app</a></p><p>We aim to respond within 48 hours. For content takedown requests, please include the article URL and proof of ownership.</p>"""
PRIVACY_BODY = """<p>AI Brief respects your privacy.</p><h2>What we collect</h2><p>We use Google Analytics (GA4) to understand aggregate traffic patterns — pages visited, approximate location, device type. We do not collect names, emails, or personal identifiers unless you voluntarily subscribe to the newsletter.</p><h2>Cookies</h2><p>Analytics cookies help us improve the site. You can disable cookies in your browser settings.</p><h2>Third parties</h2><p>We do not sell your data. Analytics data is processed by Google under their privacy policy.</p><h2>Contact</h2><p>Privacy questions: <a href="mailto:hello@ainews.vercel.app">hello@ainews.vercel.app</a></p>"""

for fname, title, desc_text, body_html, emoji in [
    ("about.html", "About — AI Brief", "What AI Brief is and how it works.", ABOUT_BODY, "ℹ️"),
    ("contact.html", "Contact — AI Brief", "Contact AI Brief for corrections, takedowns, or partnerships.", CONTACT_BODY, "✉️"),
    ("privacy.html", "Privacy Policy — AI Brief", "AI Brief privacy policy: what we collect and why.", PRIVACY_BODY, "🔒"),
]:
    write(fname, head(title, desc_text, f"{URL}/{fname}", image_emoji=emoji) + header(fname.replace(".html","")) + f"""
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
