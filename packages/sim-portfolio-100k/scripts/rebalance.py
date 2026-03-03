#!/usr/bin/env python3
"""Utility to summarize the $100K simulation book and derive rebalance orders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def load_portfolio(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def calc_equity(portfolio: dict) -> float:
    equity = portfolio.get("cash", 0.0)
    for pos in portfolio.get("positions", []):
        equity += pos.get("market_value", pos.get("shares", 0) * pos.get("market_price", 0))
    return equity


def derive_orders(portfolio: dict) -> list[dict]:
    equity = calc_equity(portfolio)
    orders: list[dict] = []
    for pos in portfolio.get("positions", []):
        target_value = equity * pos.get("target_allocation", 0)
        delta_value = target_value - pos.get("market_value", 0)
        if abs(delta_value) < 50:  # ignore tiny drifts
            continue
        direction = "BUY" if delta_value > 0 else "SELL"
        shares = round(delta_value / pos.get("market_price", 1), 2)
        orders.append(
            {
                "symbol": pos["symbol"],
                "direction": direction,
                "shares": shares,
                "delta_value": round(delta_value, 2),
                "thesis": pos.get("thesis", "")
            }
        )
    return orders


def summarize(portfolio: dict, orders: Iterable[dict]) -> str:
    equity = calc_equity(portfolio)
    lines = [f"Book equity: ${equity:,.2f}", f"Cash: ${portfolio.get('cash', 0):,.2f}"]
    lines.append("\nTarget vs. Actual (top 5 weights):")
    sorted_positions = sorted(portfolio.get("positions", []), key=lambda p: p.get("target_allocation", 0), reverse=True)
    for pos in sorted_positions[:5]:
        actual = pos.get("market_value", 0) / equity
        target = pos.get("target_allocation", 0)
        drift = actual - target
        lines.append(
            f"- {pos['symbol']}: actual {actual:.1%} vs target {target:.1%} (drift {drift:+.1%})"
        )
    if orders:
        lines.append("\nSuggested orders:")
        for order in orders:
            lines.append(
                f"- {order['direction']} {order['shares']} {order['symbol']} (~${order['delta_value']:,.0f}) — {order['thesis']}"
            )
    else:
        lines.append("\nPortfolio is within tolerance; no orders suggested.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize and rebalance the $100K simulation book.")
    parser.add_argument("--portfolio", default="data/portfolio.json", help="Path to portfolio JSON")
    parser.add_argument("--out", default="rebalance-note.txt", help="Where to write the summary")
    args = parser.parse_args()

    portfolio = load_portfolio(Path(args.portfolio))
    orders = derive_orders(portfolio)
    report = summarize(portfolio, orders)
    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
