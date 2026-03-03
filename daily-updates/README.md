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

These subfolders ship empty (`.gitkeep`) so you can version control the structure without checking in sensitive data.
