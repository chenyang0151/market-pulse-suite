#!/usr/bin/env python3
"""Build a bilingual creator-consensus brief from structured signals + channel metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent

import yaml


def load_channels(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("channels", [])


def load_signals(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_topic_block(topic: dict) -> str:
    tickers = ", ".join(topic.get("tickers", [])) or "N/A"
    creators = "\n".join(
        [f"    - {c['name']}: {c['clip']} ({c['sentiment']})" for c in topic.get("creators", [])]
    )
    return dedent(
        f"""
        ### {topic.get('theme')} ({tickers})
        - Buzz score: {topic.get('buzz_score', 0):.0%}
        - Creators:\n{creators}
        """
    ).strip()


def format_topic_block_cn(topic: dict) -> str:
    tickers = "、".join(topic.get("tickers", [])) or "无"
    creators = "\n".join(
        [f"    - {c['name']}：{c['clip']}（情绪：{c['sentiment']}）" for c in topic.get("creators", [])]
    )
    return dedent(
        f"""
        ### {topic.get('theme')}（{tickers}）
        - 热度得分：{topic.get('buzz_score', 0):.0%}
        - 重点创作者：\n{creators}
        """
    ).strip()


def build_report(channels: list[dict], signals: dict) -> str:
    topic_blocks = "\n\n".join(format_topic_block(t) for t in signals.get("topics", []))
    topic_blocks_cn = "\n\n".join(format_topic_block_cn(t) for t in signals.get("topics", []))
    alerts = "\n".join(f"- {a['description']} (severity: {a.get('severity', 'n/a')})" for a in signals.get("alerts", []))
    alerts_cn = "\n".join(f"- {a['description']}（风险：{a.get('severity', 'n/a')}）" for a in signals.get("alerts", []))
    total_creators = len(channels)
    zh_creators = sum(1 for c in channels if c.get("language") == "zh")
    en_creators = sum(1 for c in channels if c.get("language") == "en")

    return dedent(
        f"""
        # Creator Consensus Brief — {signals.get('as_of')}

        ## Snapshot
        - Covered creators: {total_creators} ({en_creators} EN / {zh_creators} ZH)
        - Topics tracked: {len(signals.get('topics', []))}
        - Alerts: {len(signals.get('alerts', []))}

        ## Themes
        {topic_blocks}

        ## Alerts
        {alerts or 'No active alerts.'}

        ---

        # 创作者共识快照 — {signals.get('as_of')}

        ## 摘要
        - 监测创作者：{total_creators}（英文 {en_creators} / 中文 {zh_creators}）
        - 跟踪主题：{len(signals.get('topics', []))}
        - 风险提醒：{len(signals.get('alerts', []))}

        ## 主题洞察
        {topic_blocks_cn}

        ## 风险提醒
        {alerts_cn or '暂无风险提醒。'}
        """
    ).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a bilingual creator consensus brief.")
    parser.add_argument("--channels", default="config/channels.yaml", help="Path to channel metadata YAML")
    parser.add_argument("--signals", default="data-samples/creator_signals.json", help="Path to structured signal JSON")
    parser.add_argument("--out", default="creator_consensus.md", help="Output markdown path")
    args = parser.parse_args()

    channels = load_channels(Path(args.channels))
    signals = load_signals(Path(args.signals))
    report = build_report(channels, signals)
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
