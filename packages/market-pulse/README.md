# Market Pulse Automation

This package wires together the Market Pulse scraper + brain to ship a bilingual macro brief.

## Components

- `skills/market-pulse-scraper` — pulls YouTube metadata + macro feeds into normalized JSON payloads.
- `skills/market-pulse-brain` — synthesizes bilingual Markdown reports with sections for Macro, Creator Pulse, Consensus Watch, 中文热点, and positioning ideas.
- `scripts/daily.sh` — orchestrates deps, collection, synthesis, and optional Telegram delivery.
- `config/channels.yaml` — canonical watch list for Creator Pulse.

## Running locally

```bash
cd packages/market-pulse
bash scripts/daily.sh
```

Environment variables:

| Name | Purpose |
| --- | --- |
| `TELEGRAM_TARGET` | Optional chat id / username for delivery (requires `openclaw message send`). |

The script builds a venv under `.venv/market-pulse`, installs both skills' requirements, and writes:

- raw scrape → `data/market-pulse/raw/market-pulse-<timestamp>.json`
- Markdown report → `data/market-pulse/reports/market-pulse-YYYY-MM-DD.md`
- logs → `data/market-pulse/logs/<timestamp>.log`

## Sample output

See `../../samples/market-pulse-report-2026-03-03.md` for a real report that triggered the packaging request.
