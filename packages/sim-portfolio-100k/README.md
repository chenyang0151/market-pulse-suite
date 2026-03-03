# $100K Simulation Portfolio

Rules-based positioning overlay that mirrors the insights from Market Pulse + Creator Consensus.

## Data contract

`data/portfolio.json` contains:

- `as_of` — ISO timestamp
- `starting_capital`
- `positions[]` — symbol, shares, avg cost, current price/value, target allocation, thesis
- `hedges[]` — optional tail hedges or overlays
- `cash`, `pnl`

## Workflow

1. Update `data/portfolio.json` after the daily brief (manual edit or script).
2. Run `scripts/rebalance.py` to generate a messenger-ready summary.
3. Optional: `python3 ../../tools/generate_trade_plan.py --date YYYY-MM-DD` to turn the holdings into「板块→结论→操作」格式。（依赖 `data/trade_playbook.json`）

```bash
cd packages/sim-portfolio-100k
python3 scripts/rebalance.py --out ../../samples/rebalance-note.txt
```

## 中文说明

- `portfolio.json` 记录了模型投资组合的仓位、目标占比以及每条 thesis。
- `rebalance.py` 会读取 JSON，计算与目标的偏差，并输出建议的买卖指令，方便粘贴到 Telegram / Slack。
