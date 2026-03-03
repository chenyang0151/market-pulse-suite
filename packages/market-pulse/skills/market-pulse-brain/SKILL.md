---
name: market-pulse-brain
description: Turn Market Pulse raw scrape files into bilingual (EN/ZH) macro summaries with impact analysis, consensus tracking, and actionable ticker callouts. Use after running market-pulse-scraper to prepare the Telegram-ready report.
---

# Market Pulse Brain

This skill consumes the JSON payloads produced by `skills/market-pulse-scraper` and synthesizes a Markdown briefing suitable for Telegram delivery. It:

1. Scores each news/video mention for focus keywords (rates, inflation, AI/tech earnings, geopolitics).
2. Detects overlapping tickers/topics across YouTube + news.
3. Surfaces explicit buy/sell language from creators.
4. Emits both English and Chinese (Simplified) summaries for hot topics.

## Layout

```
skills/market-pulse-brain/
├── SKILL.md
├── market_pulse_brain.py    # CLI entry point
├── requirements.txt         # pandas, numpy, googletrans, etc.
```

Reports are saved to `data/market-pulse/reports/YYYY-MM-DD.md` unless overridden via CLI flags.

## CLI

```
python skills/market-pulse-brain/market_pulse_brain.py synthesize \
  --raw-dir data/market-pulse/raw \
  --output-dir data/market-pulse/reports
```

Options:
- `--raw-file`: process a specific JSON file (defaults to latest timestamp in `raw-dir`).
- `--top-n`: number of bullet points per section (default 5).

## Output format

```
# Market Pulse – 2026-03-03

## Overnight Macro (EN)
- **Rates:** …

## Creator Pulse (EN)
- …

## 中文热点摘要
- …

## Trade & Positioning Ideas
- …

## Delivery
```

Each ticker mention is bolded (`**$NVDA**`). Sections automatically collapse when there are no qualifying items.

## Translation fallback

`googletrans==4.0.0-rc1` is used for CN snippets. If Google blocks requests, the script falls back to a naive template (`[ZH translation pending] <English>`). Set `GOOGLETRANS_TIMEOUT` to tune latency.

## Extending logic

- Phrase/keyword rules live in `KEYWORDS` inside the script.
- Sentiment scoring is currently heuristic (counts keyword hits). Replace `score_topic()` with NLP/LLM calls if desired.
- Trade ideas rely on regex scanning for verbs (`buy`, `sell`, `trim`, `short`). Expand `ACTION_VERBS` to support more nuanced language.
