# AI Brief — AI news & tools, explained simply

Static news site. Built by `scripts/build.py` from `data/articles.json`.

## Local dev
```bash
python3 scripts/build.py
python3 -m http.server -d . 8000
```

## News pipeline
`.github/workflows/news-pipeline.yml` runs every 8 hours:
1. `scripts/fetch_news.py` — RSS fetch + dedupe + Gemini summaries (needs `GEMINI_API_KEY` repo secret; without it, writes review drafts)
2. `scripts/build.py` — regenerates HTML + sitemaps
3. Auto-commits

## Monetization
Halal ad policy: block gambling, alcohol, dating, interest-based financial products, indecent content in AdSense.
