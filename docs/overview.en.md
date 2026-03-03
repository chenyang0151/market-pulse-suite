# Market Pulse Suite — System Overview

Market Pulse Suite bundles three deliverables that ship to Telegram/email each morning (PT):

1. **Market Pulse** — bilingual macro + creator rundown + trade ideas.
2. **Creator Consensus** — structured sentiment snapshots across 35 EN/15 ZH creators.
3. **$100K Simulation Portfolio** — rules-based positioning derived from #1 and #2.

## Architecture

```text
YouTube + RSS + News APIs
          │
          ▼
skills/market-pulse-scraper (Python)
          │ normalized JSON
          ▼
skills/market-pulse-brain (Python)
          │ markdown brief
          ├──→ creator-consensus/generate_consensus.py (Markdown summary)
          └──→ sim-portfolio-100k/rules (Position sizing JSON)
```

Automation is coordinated through `packages/market-pulse/scripts/daily.sh` which:

1. Spins up/refreshes a Python venv.
2. Installs scraper + brain dependencies.
3. Collects feeds via `market_pulse_scraper.py collect-all`.
4. Synthesizes reports with `market_pulse_brain.py synthesize`.
5. Ships optional delivery (Telegram attachment or your own transport).

## Data outputs

| Path | Description |
| --- | --- |
| `data/market-pulse/raw/*.json` | Unified scrape payload (YouTube metadata + RSS + macro wires). |
| `data/market-pulse/reports/*.md` | Markdown-ready bilingual brief. |
| `packages/creator-consensus/creator_consensus.md` | Optional consensus summary (bilingual). |
| `packages/sim-portfolio-100k/data/portfolio.json` | Current simulated book with target weights + theses. |

## Extending

- Wire `scripts/daily.sh` into cron / GitHub Actions for consistent delivery windows.
- Replace Telegram with Slack/email by editing the delivery block.
- Feed `creator_signals.json` from your own LLM summarizer or search index to expand beyond YouTube.
