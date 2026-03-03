#!/usr/bin/env python3
"""Market Pulse reasoning stage."""

import argparse
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml
from dateutil import parser as dateparser
from googletrans import Translator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "market-pulse" / "raw"
REPORT_DIR = PROJECT_ROOT / "data" / "market-pulse" / "reports"

KEYWORDS = {
    "Rates & Fed": ["interest rate", "fed", "yield", "treasury", "dot plot"],
    "Inflation": ["inflation", "cpi", "ppi", "pce"],
    "Tech Earnings": ["earnings", "guidance", "ai", "nvda", "aapl", "msft", "chips"],
    "Geopolitics": ["geopolitic", "china", "taiwan", "ukraine", "middle east", "iran"],
}
ACTION_VERBS = ["buy", "adding", "add", "accumulate", "sell", "trim", "short", "hedge", "reduce"]

TICKER_ALIASES = {
    "nvda": "$NVDA",
    "nvidia": "$NVDA",
    "aapl": "$AAPL",
    "apple": "$AAPL",
    "msft": "$MSFT",
    "microsoft": "$MSFT",
    "goog": "$GOOGL",
    "googl": "$GOOGL",
    "meta": "$META",
    "tsla": "$TSLA",
    "tesla": "$TSLA",
    "amd": "$AMD",
    "amazon": "$AMZN",
    "amzn": "$AMZN",
}


@dataclass
class Item:
    source: str
    title: str
    summary: str
    published_at: Optional[datetime]
    link: Optional[str]
    origin: str  # news | youtube-channel | youtube-trending
    channel: Optional[str] = None
    language: Optional[str] = None

    def text(self) -> str:
        return " ".join(filter(None, [self.title, self.summary or ""]))


class TranslatorWrapper:
    def __init__(self) -> None:
        timeout = float(os.getenv("GOOGLETRANS_TIMEOUT", "5"))
        self.translator = Translator(timeout=timeout)

    def zh(self, text: str) -> str:
        if not text:
            return ""
        try:
            translated = self.translator.translate(text, src="en", dest="zh-cn")
            return translated.text
        except Exception:
            return f"[待翻译] {text}"


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return dateparser.parse(value)
    except Exception:
        return None


def load_raw(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def latest_raw_file(raw_dir: Path) -> Path:
    files = sorted(raw_dir.glob("market-pulse-*.json"))
    if not files:
        raise FileNotFoundError("No raw files found. Run the scraper first.")
    return files[-1]


def flatten_items(data: Dict) -> List[Item]:
    items: List[Item] = []
    youtube = data.get("youtube") or {}
    for channel_entry in youtube.get("channels", []):
        items.append(
            Item(
                source=channel_entry.get("channel", "unknown"),
                title=channel_entry.get("title", ""),
                summary=channel_entry.get("description", ""),
                published_at=parse_datetime(channel_entry.get("published_at")),
                link=channel_entry.get("webpage_url"),
                origin="youtube-channel",
                channel=channel_entry.get("channel"),
                language=channel_entry.get("language"),
            )
        )
    for trend in youtube.get("trending", []):
        items.append(
            Item(
                source=trend.get("query", "trending"),
                title=trend.get("title", ""),
                summary=trend.get("description", ""),
                published_at=parse_datetime(trend.get("published_at")),
                link=trend.get("webpage_url"),
                origin="youtube-trending",
                channel=trend.get("channel"),
            )
        )

    news = data.get("news") or {}
    for article in news.get("items", []):
        items.append(
            Item(
                source=article.get("source", "news"),
                title=article.get("title", ""),
                summary=article.get("summary", ""),
                published_at=parse_datetime(article.get("published_at")),
                link=article.get("link"),
                origin="news",
            )
        )
    return items


def match_topics(text: str) -> List[str]:
    lowered = text.lower()
    hits = []
    for topic, needles in KEYWORDS.items():
        if any(needle in lowered for needle in needles):
            hits.append(topic)
    return hits


def extract_tickers(text: str) -> List[str]:
    tickers = set()
    for raw in re.findall(r"\$[A-Z]{1,5}", text):
        tickers.add(raw.upper())
    lowered = text.lower()
    for key, ticker in TICKER_ALIASES.items():
        if key in lowered:
            tickers.add(ticker)
    return sorted(tickers)


def detect_actions(item: Item) -> Optional[str]:
    text = item.text().lower()
    if not any(verb in text for verb in ACTION_VERBS):
        return None
    tickers = extract_tickers(item.text())
    ticker_label = ", ".join(tickers) if tickers else "(no ticker)"
    return f"**{ticker_label}** – {item.title}".strip()


def build_sections(items: List[Item], top_n: int) -> Dict[str, List[str]]:
    news_items = [i for i in items if i.origin == "news"]
    yt_items = [i for i in items if i.origin.startswith("youtube")]

    news_sorted = sorted(news_items, key=lambda i: i.published_at or datetime.min, reverse=True)[:top_n]
    youtube_sorted = sorted(yt_items, key=lambda i: i.published_at or datetime.min, reverse=True)[:top_n]

    sections: Dict[str, List[str]] = {
        "macro": [format_bullet(item) for item in news_sorted],
        "creators": [format_bullet(item) for item in youtube_sorted],
    }

    consensus = aggregate_consensus(news_items, yt_items)
    if consensus:
        sections["consensus"] = consensus

    trades = [detect_actions(item) for item in yt_items + news_items]
    trades = [t for t in trades if t]
    if trades:
        sections["trades"] = trades[:top_n]

    return sections


def format_bullet(item: Item) -> str:
    tickers = extract_tickers(item.text())
    ticker_str = f" {' '.join(tickers)}" if tickers else ""
    link = f" ({item.link})" if item.link else ""
    return f"- **{item.title.strip()}**{ticker_str}{link}"


def aggregate_consensus(news_items: List[Item], yt_items: List[Item]) -> List[str]:
    news_topics = defaultdict(list)
    yt_topics = defaultdict(list)
    for item in news_items:
        for topic in match_topics(item.text()):
            news_topics[topic].append(item)
    for item in yt_items:
        for topic in match_topics(item.text()):
            yt_topics[topic].append(item)

    bullets: List[str] = []
    for topic, news_hits in news_topics.items():
        if topic not in yt_topics:
            continue
        yt_hits = yt_topics[topic]
        latest_news = news_hits[0]
        latest_yt = yt_hits[0]
        bullets.append(
            f"- **{topic}** – News: {latest_news.title.strip()} | Creators: {latest_yt.title.strip()}"
        )
    return bullets[:5]


def build_chinese_section(sections: Dict[str, List[str]], translator: TranslatorWrapper, top_n: int) -> List[str]:
    zh_bullets: List[str] = []
    combined = (sections.get("macro") or []) + (sections.get("creators") or [])
    for bullet in combined[:top_n]:
        zh_bullets.append(f"- {translator.zh(bullet)}")
    return zh_bullets


def render_report(sections: Dict[str, List[str]], report_date: datetime) -> str:
    translator = TranslatorWrapper()
    zh_section = build_chinese_section(sections, translator, top_n=5)

    parts = [f"# Market Pulse — {report_date.strftime('%Y-%m-%d')}\n"]
    if sections.get("macro"):
        parts.append("## Overnight Macro\n" + "\n".join(sections["macro"]))
    if sections.get("creators"):
        parts.append("\n## Creator Pulse\n" + "\n".join(sections["creators"]))
    if sections.get("consensus"):
        parts.append("\n## Consensus Watch\n" + "\n".join(sections["consensus"]))
    if zh_section:
        parts.append("\n## 中文热点摘要\n" + "\n".join(zh_section))
    if sections.get("trades"):
        parts.append("\n## Trade & Positioning Ideas\n" + "\n".join(sections["trades"]))
    return "\n\n".join(parts) + "\n"


def determine_output_path(output_dir: Path, report_date: datetime) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"market-pulse-{report_date.strftime('%Y-%m-%d')}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market Pulse brain")
    sub = parser.add_subparsers(dest="command", required=True)
    synth = sub.add_parser("synthesize", help="Generate Markdown report")
    synth.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    synth.add_argument("--raw-file", type=Path)
    synth.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    synth.add_argument("--top-n", type=int, default=5)
    return parser.parse_args()


def command_synthesize(args: argparse.Namespace) -> Path:
    if args.raw_file:
        raw_path = args.raw_file
    else:
        raw_path = latest_raw_file(args.raw_dir)
    data = load_raw(raw_path)
    items = flatten_items(data)
    sections = build_sections(items, args.top_n)
    report_date = datetime.utcnow()
    report_text = render_report(sections, report_date)
    output_path = determine_output_path(args.output_dir, report_date)
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(report_text)
    print(f"Report saved → {output_path}")
    return output_path


def main() -> None:
    args = parse_args()
    if args.command == "synthesize":
        command_synthesize(args)
    else:
        raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()
