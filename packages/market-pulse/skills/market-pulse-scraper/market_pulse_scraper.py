#!/usr/bin/env python3
"""Market Pulse data collector."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import feedparser
import requests
import yaml
from dateutil import parser as dateparser
from yt_dlp import YoutubeDL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHANNELS = PROJECT_ROOT / "data" / "market-pulse" / "channels.yaml"
DEFAULT_CONFIG = Path(__file__).resolve().with_name("config.yaml")
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "market-pulse" / "raw"


class ScraperError(Exception):
    pass


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_channels(path: Path) -> List[Dict[str, Any]]:
    data = _load_yaml(path)
    channels = data.get("channels", [])
    if not isinstance(channels, list):
        raise ScraperError(f"Invalid channel schema in {path}")
    return channels


def build_ydl(max_entries: int) -> YoutubeDL:
    opts = {
        "quiet": True,
        "noplaylist": True,
        "skip_download": True,
        "extract_flat": True,
        "lazy_playlist": True,
        "playlistend": max_entries,
    }
    return YoutubeDL(opts)


def normalize_timestamp(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    try:
        return dateparser.parse(str(value)).astimezone(timezone.utc).isoformat()
    except Exception:
        return str(value)


def collect_channel_videos(channel: Dict[str, Any], max_videos: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    videos: List[Dict[str, Any]] = []
    ydl = build_ydl(max_videos)
    url = channel.get("handle_or_url")
    if not url:
        return videos, [f"Channel {channel.get('name')} missing handle_or_url"]
    try:
        info = ydl.extract_info(url, download=False)
    except Exception as exc:  # pragma: no cover - yt-dlp errors vary
        errors.append(f"{channel.get('name')}: {exc}")
        return videos, errors

    entries = info.get("entries") or []
    for entry in entries[:max_videos]:
        video_url = entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        videos.append(
            {
                "channel": channel.get("name"),
                "language": channel.get("language"),
                "region": channel.get("region"),
                "focus": channel.get("focus"),
                "title": entry.get("title"),
                "description": (entry.get("description") or "")[:800],
                "published_at": normalize_timestamp(entry.get("release_timestamp") or entry.get("timestamp")),
                "duration": entry.get("duration"),
                "view_count": entry.get("view_count"),
                "like_count": entry.get("like_count"),
                "webpage_url": video_url,
                "comments": [],
            }
        )
    return videos, errors


def collect_trending(searches: List[str], max_results: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    ydl = build_ydl(max_results)
    for query in searches:
        try:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        except Exception as exc:  # pragma: no cover
            errors.append(f"Trending '{query}': {exc}")
            continue
        entries = info.get("entries") or []
        for entry in entries[:max_results]:
            results.append(
                {
                    "query": query,
                    "title": entry.get("title"),
                    "channel": entry.get("channel"),
                    "published_at": normalize_timestamp(entry.get("timestamp")),
                    "webpage_url": entry.get("url"),
                    "description": (entry.get("description") or "")[:600],
                }
            )
    return results, errors


def fetch_rss(url: str) -> feedparser.FeedParserDict:
    return feedparser.parse(url)


def fetch_google_news(keyword: str) -> feedparser.FeedParserDict:
    from urllib.parse import quote

    query = quote(f"{keyword} when:1d")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    return fetch_rss(url)


def matches_focus(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(key.lower() in lowered for key in keywords)


def collect_news(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    focus_keywords = config["news"].get("focus_keywords", [])
    records: List[Dict[str, Any]] = []
    errors: List[str] = []

    for keyword in config["news"].get("google_keywords", []):
        feed = fetch_google_news(keyword)
        for entry in feed.entries:
            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            if focus_keywords and not matches_focus(text, focus_keywords):
                continue
            records.append(
                {
                    "source": "google-news",
                    "keyword": keyword,
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "published_at": normalize_timestamp(entry.get("published")),
                    "link": entry.get("link"),
                }
            )

    for feed_cfg in config["news"].get("rss_feeds", []):
        url = feed_cfg.get("url")
        if not url:
            continue
        feed = fetch_rss(url)
        for entry in feed.entries:
            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            if focus_keywords and not matches_focus(text, focus_keywords):
                continue
            records.append(
                {
                    "source": feed_cfg.get("id", url),
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "published_at": normalize_timestamp(entry.get("published")),
                    "link": entry.get("link"),
                }
            )
    return records, errors


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def dedupe_recent(records: List[Dict[str, Any]], window_hours: int, key_fields: List[str]) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for rec in records:
        published = rec.get("published_at")
        try:
            dt = dateparser.parse(published).astimezone(timezone.utc) if published else None
        except Exception:
            dt = None
        if dt and dt < cutoff:
            continue
        key = tuple(rec.get(field) for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)
    return deduped


def run_collect_youtube(args: argparse.Namespace) -> Dict[str, Any]:
    config = _load_yaml(args.config)
    channels = load_channels(args.channels_file)
    max_videos = config["youtube"].get("max_videos_per_channel", 2)
    trending_searches = config["youtube"].get("trending_searches", [])
    max_trending = config["youtube"].get("max_trending_results", 5)

    all_videos: List[Dict[str, Any]] = []
    errors: List[str] = []
    for channel in channels:
        vids, errs = collect_channel_videos(channel, max_videos)
        all_videos.extend(vids)
        errors.extend(errs)

    trending, trending_errors = collect_trending(trending_searches, max_trending)
    errors.extend(trending_errors)

    return {
        "channels": all_videos,
        "trending": trending,
        "errors": errors,
    }


def run_collect_news(args: argparse.Namespace) -> Dict[str, Any]:
    config = _load_yaml(args.config)
    news_records, news_errors = collect_news(config)
    dedupe_window = config.get("output", {}).get("dedupe_window_hours", 24)
    news_records = dedupe_recent(news_records, dedupe_window, ["title", "link"])
    return {
        "items": news_records,
        "errors": news_errors,
    }


def save_payload(payload: Dict[str, Any], output_dir: Path) -> Path:
    ensure_output_dir(output_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"market-pulse-{timestamp}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return path


def collect_all(args: argparse.Namespace) -> Path:
    yt_payload = run_collect_youtube(args)
    news_payload = run_collect_news(args)
    payload = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "youtube": yt_payload,
        "news": news_payload,
        "meta": {
            "channels_file": str(args.channels_file),
            "config": str(args.config),
        },
    }
    return save_payload(payload, args.output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market Pulse scraper")
    parser.add_argument("command", choices=["collect-youtube", "collect-news", "collect-all"], help="Scraper mode")
    parser.add_argument("--channels-file", dest="channels_file", default=DEFAULT_CHANNELS, type=Path)
    parser.add_argument("--config", dest="config", default=DEFAULT_CONFIG, type=Path)
    parser.add_argument("--output", dest="output", default=DEFAULT_OUTPUT, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.channels_file.exists():
        raise SystemExit(f"Channel file not found: {args.channels_file}")
    if not args.config.exists():
        raise SystemExit(f"Config file not found: {args.config}")

    if args.command == "collect-youtube":
        payload = run_collect_youtube(args)
        path = save_payload(
            {
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "youtube": payload,
                "news": {},
                "meta": {
                    "channels_file": str(args.channels_file),
                    "config": str(args.config),
                },
            },
            args.output,
        )
    elif args.command == "collect-news":
        payload = run_collect_news(args)
        path = save_payload(
            {
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "youtube": {},
                "news": payload,
                "meta": {
                    "channels_file": str(args.channels_file),
                    "config": str(args.config),
                },
            },
            args.output,
        )
    else:
        path = collect_all(args)

    print(f"Saved payload → {path}")


if __name__ == "__main__":
    main()
