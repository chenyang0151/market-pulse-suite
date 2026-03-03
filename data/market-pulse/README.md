# Data Directory

Runtime artifacts land here when you run `packages/market-pulse/scripts/daily.sh`:

- `raw/` — timestamped JSON payloads from the scraper.
- `reports/` — Markdown briefs.
- `logs/` — orchestrator logs.

The folders ship empty (`.gitkeep`) so you can mount them to S3 or keep them local without polluting git history.
