---
name: market-pulse-scraper
description: Collect daily macro inputs for Market Pulse (YouTube metadata, trending finance clips, and macro news feeds) and persist normalized JSON for downstream synthesis. Use when the agent must refresh video/news data before running the Market Pulse brain.
---

# Market Pulse Scraper

Use this skill to gather raw inputs for the Market Pulse pipeline. It wraps a Python CLI (`market_pulse_scraper.py`) that pulls YouTube metadata from the curated channel list and scrapes finance news feeds (Google News keywords, Reuters Business, Bloomberg Markets). Output is saved under `data/market-pulse/raw/` with timestamps so the brain stage can build summaries.

## Layout

```
skills/market-pulse-scraper/
├── SKILL.md
├── config.yaml              # Scraper tuning knobs (feeds, keyword filters)
├── market_pulse_scraper.py  # Entry point (argparse CLI)
├── requirements.txt         # Python deps (yt-dlp, feedparser, PyYAML, etc.)
```

Channel metadata lives in `data/market-pulse/channels.yaml` at the workspace root (shared with other components).

## Commands

```
python skills/market-pulse-scraper/market_pulse_scraper.py collect-youtube
python skills/market-pulse-scraper/market_pulse_scraper.py collect-news
python skills/market-pulse-scraper/market_pulse_scraper.py collect-all
```

All commands share the same optional flags:

- `--channels-file`: override path to `channels.yaml` (default `data/market-pulse/channels.yaml`).
- `--config`: override scraper config (default `skills/market-pulse-scraper/config.yaml`).
- `--output`: override raw data output directory (default `data/market-pulse/raw`).

### YouTube collection

- Uses `yt-dlp` in metadata-only mode (`skip_download=True`) to grab the latest `max_videos_per_channel` entries per channel.
- For each video it records: title, description snippet, publish time, duration, view count, like count (when present), and canonical URL.
- Trending finance clips are fetched via keyword searches defined in `config.yaml` (e.g., "finance news today", "Federal Reserve").
- Comment harvesting is stubbed with `comments: []` for now; extend later via the YouTube Data API or yt-dlp comment extraction (set `extractor_args.youtube.max_comments`).

### News collection

- Pulls Google News RSS for each keyword (see `news.google_keywords`).
- Adds Reuters Business (`https://feeds.reuters.com/reuters/businessNews`) and Bloomberg Markets (`https://feeds.bloomberg.com/markets/news.rss`).
- Filters items whose title + summary mention at least one of the configured `focus_keywords` (Interest rates, inflation, tech earnings, geopolitical risk, AI megacaps by ticker).

### Output structure

Each run writes `data/market-pulse/raw/<timestamp>.json` with:

```jsonc
{
  "captured_at": "2026-03-03T04:55:00Z",
  "youtube": {
    "channels": [ { ... } ],
    "trending": [ { ... } ]
  },
  "news": [ { ... } ],
  "meta": {
    "channels_file": "data/market-pulse/channels.yaml",
    "filters": { ... }
  }
}
```

`meta.last_cursor` keeps per-channel ISO timestamps so the brain can diff later.

## Firecrawl / Anti-bot fallback

If a `FIRECRAWL_API_KEY` environment variable is present, the scraper will call Firecrawl's `/v1/scrape` endpoint for individual URLs where raw HTML is required (currently only used for RSS fallback). Without the key, it relies on public RSS feeds and yt-dlp.

## Extending / Debugging

- To add/remove channels, edit `data/market-pulse/channels.yaml` (see existing schema for language, cadence, notes).
- To adjust keywords or trending searches, edit `skills/market-pulse-scraper/config.yaml`.
- Logs are written to stdout; the heartbeat script pipes them into `data/market-pulse/logs/`.

## Testing

Run a local dry run and inspect the latest JSON:

```
python skills/market-pulse-scraper/market_pulse_scraper.py collect-all
ls data/market-pulse/raw | tail -n 1
jq '.' data/market-pulse/raw/<latest>.json | head
```

If yt-dlp throttles, set `YTDLP_PROXY` or `http_proxy` env vars before running.
