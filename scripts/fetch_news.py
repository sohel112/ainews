#!/usr/bin/env python3
"""
Ady news pipeline — fetches AI news RSS feeds, dedupes against existing
articles, and generates draft briefs.

Summarization: if GEMINI_API_KEY env var is set, calls Gemini API for original
100-150 word briefs with commentary. Otherwise writes source-based stubs marked
draft=true for human review.

Usage: python3 scripts/fetch_news.py
"""
import json, os, re, sys, html as htmlmod
from datetime import date, datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "articles.json")
SEEN_FILE = os.path.join(ROOT, "data", "seen.json")

# Curated RSS sources — official blogs + reputable tech press (no paywalled content)
FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("MIT Tech Review AI", "https://www.technologyreview.com/feed/"),
    ("Google DeepMind", "https://deepmind.google/discover/blog/rss.xml"),
]

MAX_NEW = 5  # max new drafts per run


def fetch(url, timeout=25):
    req = Request(url, headers={"User-Agent": "AIBriefBot/1.0 (+https://ainews-psi-teal.vercel.app)"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_rss(xml_text):
    """Minimal RSS/Atom parser (no deps). Returns [(title, link, published)]."""
    items = []
    for m in re.finditer(r"<item>(.*?)</item>", xml_text, re.S):
        chunk = m.group(1)
        title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", chunk, re.S)
        link = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", chunk, re.S)
        if title and link:
            items.append((htmlmod.unescape(title.group(1).strip()),
                          htmlmod.unescape(link.group(1).strip())))
    if not items:  # try Atom
        for m in re.finditer(r"<entry>(.*?)</entry>", xml_text, re.S):
            chunk = m.group(1)
            title = re.search(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", chunk, re.S)
            link = re.search(r'<link[^>]*href="([^"]+)"', chunk)
            if title and link:
                items.append((htmlmod.unescape(title.group(1).strip()), link.group(1).strip()))
    return items


def ai_keywords(title):
    t = title.lower()
    return any(k in t for k in ["ai ", "artificial intelligence", "chatgpt", "gpt",
            "gemini", "claude", "llm", "machine learning", "openai", "anthropic",
            "deepmind", "copilot", "midjourney", "stable diffusion", "robot"])


def summarize_with_gemini(title, link, source):
    """Original 100-150 word brief + 'why it matters' via Gemini. Returns body HTML or None."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    import urllib.request
    prompt = (
        "Write an ORIGINAL 100-150 word news brief about this AI story for a general audience. "
        "Do NOT copy or closely paraphrase any article text — write fresh commentary in plain English. "
        "Structure: 2 short paragraphs summarizing what happened, then a final paragraph starting with "
        "'Why it matters:' giving your honest take. Use <p> tags and <strong> for the 'Why it matters:' label. "
        f"Story headline: {title}. Source: {source} ({link})."
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"maxOutputTokens": 400}}).encode()
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + key,
        data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # keep only <p>/<strong> tags
        text = re.sub(r"</?(?!p\b|strong\b)[a-zA-Z][^>]*>", "", text)
        return text.strip()
    except Exception as e:
        print(f"  Gemini error: {e}", file=sys.stderr)
        return None


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60] or "ai-brief"


def main():
    with open(DATA) as f:
        site_data = json.load(f)
    existing_slugs = {a["slug"] for a in site_data["articles"]}
    seen = set()
    if os.path.exists(SEEN_FILE):
        seen = set(json.load(open(SEEN_FILE)))

    new_articles = []
    for source, feed_url in FEEDS:
        if len(new_articles) >= MAX_NEW:
            break
        try:
            xml_text = fetch(feed_url)
        except Exception as e:
            print(f"Feed failed [{source}]: {e}", file=sys.stderr)
            continue
        for title, link in parse_rss(xml_text):
            if len(new_articles) >= MAX_NEW:
                break
            if not ai_keywords(title):
                continue
            slug = slugify(title)
            if slug in existing_slugs or link in seen:
                continue
            seen.add(link)
            body = summarize_with_gemini(title, link, source)
            draft = body is None
            if draft:
                body = (f"<p><strong>{htmlmod.escape(title)}</strong> — reported by {htmlmod.escape(source)}. "
                        "AI summary pending review; read the full story at the source link below.</p>")
            new_articles.append({
                "slug": f"{date.today().isoformat()}-{slug}",
                "title": title[:120],
                "excerpt": f"Ady on: {title[:140]}",
                "category": "AI News",
                "date": date.today().isoformat(),
                "read_minutes": 3,
                "emoji": "📰",
                "tags": ["AI News"],
                "source_name": source,
                "source_url": link,
                "body": body,
                "draft": draft,
            })
            print(f"  + {title[:70]}")

    if new_articles:
        site_data["articles"].extend(new_articles)
        with open(DATA, "w") as f:
            json.dump(site_data, f, indent=2, ensure_ascii=False)
        print(f"Added {len(new_articles)} drafts.")
    else:
        print("No new stories.")
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen)[-2000:], f)


if __name__ == "__main__":
    main()
