#!/usr/bin/env python3
"""Copy the latest Market Pulse outputs into daily-updates/ for versioning."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path


def detect_report(date: dt.date, reports_dir: Path) -> Path | None:
    candidates = [
        reports_dir / f"{date:%Y-%m-%d}.md",
        reports_dir / f"market-pulse-{date:%Y-%m-%d}.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def copy_with_naming(src: Path, dest_dir: Path, prefix: str, suffix: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{prefix}-{suffix}{src.suffix}"
    shutil.copy2(src, dest)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive Market Pulse outputs into daily-updates/")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date (default: today)")
    parser.add_argument("--reports-dir", default="../data/market-pulse/reports", help="Source reports directory")
    parser.add_argument("--portfolio-json", default="../data/market-pulse/portfolio.json", help="Source portfolio snapshot")
    parser.add_argument("--updates-dir", default="daily-updates", help="Target base directory")
    parser.add_argument("--skip-portfolio", action="store_true", help="Only archive the report")
    args = parser.parse_args()

    target_date = dt.date.fromisoformat(args.date)
    reports_dir = Path(args.reports_dir).expanduser().resolve()
    portfolio_path = Path(args.portfolio_json).expanduser().resolve()
    updates_dir = Path(args.updates_dir).resolve()

    report_src = detect_report(target_date, reports_dir)
    if not report_src:
        raise SystemExit(f"No report found for {target_date} under {reports_dir}")

    report_dest = copy_with_naming(
        report_src, updates_dir / "reports", f"{target_date:%Y-%m-%d}", "market-pulse"
    )
    print(f"Copied report → {report_dest}")

    if not args.skip_portfolio:
        if not portfolio_path.exists():
            raise SystemExit(f"Portfolio JSON missing: {portfolio_path}")
        portfolio_dest = copy_with_naming(
            portfolio_path,
            updates_dir / "positions",
            f"{target_date:%Y-%m-%d}",
            "portfolio",
        )
        print(f"Copied portfolio → {portfolio_dest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
