# Daily Updates Hub

Use this folder to drop each day's published artifacts so they live alongside the automation code:

- `reports/` — final Market Pulse briefs (Markdown/PDF).
- `positions/` — daily snapshots of the $100K simulation book (JSON/CSV) or rebalance notes.
- `trade-plans/` — 板块 → 结论 → 操作 的决策卡片，用于 Telegram/邮件分发。

Suggested naming:

```
reports/
  2026-03-03-market-pulse.md
positions/
  2026-03-03-portfolio.json
  2026-03-03-rebalance.txt
trade-plans/
  2026-03-03-trade-plan.md
```

生成方式建议：

1. 跑完 `packages/market-pulse/scripts/daily.sh` 与 `packages/sim-portfolio-100k/scripts/rebalance.py`。
2. `python3 tools/generate_trade_plan.py --date <YYYY-MM-DD>` 生成当日 trade plan。
3. `python3 tools/archive_daily.py --date <YYYY-MM-DD> --trade-plan daily-updates/trade-plans/<date>-trade-plan.md`，把所有文件拷到该目录后提交。

These subfolders ship empty (`.gitkeep`) so you can version control the structure without checking in sensitive data.
