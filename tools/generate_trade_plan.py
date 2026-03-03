#!/usr/bin/env python3
"""Generate trade-plan markdown from the simulation portfolio + playbook."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict


def load_portfolio(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_playbook(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_action(symbol: str, template: str, position: Dict[str, Any]) -> str:
    target_pct = position.get("target_allocation", 0) * 100
    price = position.get("market_price", 0)
    thesis = position.get("thesis", "")
    return template.format(symbol=symbol, target_pct=target_pct, price=price, thesis=thesis)


def build_section(module: Dict[str, Any], positions: Dict[str, Dict[str, Any]]) -> str:
    lines = [f"## 板块：{module['name']}", f"- **结论**：{module.get('conclusion', '待补充')}" , "- **Actions**"]
    actions = []
    for idx, entry in enumerate(module.get("tickers", []), start=1):
        symbol = entry["symbol"].upper()
        template = entry.get("template", "{thesis}")
        position = positions.get(symbol, {})
        details = format_action(symbol, template, position)
        actions.append(f"  {idx}. **{symbol}** — {details}")
    if module.get("hedges"):
        actions.append("  - **Hedges**")
        for hedge in module["hedges"]:
            actions.append(f"    - {hedge.get('name')}: {hedge.get('detail')}")
    lines.extend(actions or ["  - (暂无动作)"])
    return "\n".join(lines) + "\n"


def build_report(playbook: Dict[str, Any], portfolio: Dict[str, Any], target_date: dt.date) -> str:
    positions = {pos["symbol"].upper(): pos for pos in portfolio.get("positions", [])}
    sections = [f"# Trade Plan — {target_date.isoformat()}\n"]
    for module in playbook.get("modules", []):
        sections.append(build_section(module, positions))
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate trade-plan markdown")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date for output filename")
    parser.add_argument("--playbook", default="packages/sim-portfolio-100k/data/trade_playbook.json")
    parser.add_argument("--portfolio", default="packages/sim-portfolio-100k/data/portfolio.json")
    parser.add_argument("--out-dir", default="daily-updates/trade-plans")
    args = parser.parse_args()

    target_date = dt.date.fromisoformat(args.date)
    playbook = load_playbook(Path(args.playbook))
    portfolio = load_portfolio(Path(args.portfolio))
    report = build_report(playbook, portfolio, target_date)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{target_date.isoformat()}-trade-plan.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
