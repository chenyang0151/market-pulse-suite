<p align="center">
  <img src="assets/branding/market-pulse-suite-logo.png" alt="Market Pulse Suite logo" width="220" />
</p>

# Market Pulse Suite · 市场脉冲套件

> A bilingual macro intelligence bundle that ships Market Pulse daily brief + Creator Consensus + a $100K simulation portfolio.

## Why it exists / 项目初衷

- Keep Bloomberg/YouTube/RSS macro noise in one normalized payload.
- Capture what both English + Chinese creators are obsessing over.
- Translate the narrative into positioning guidance that can be pasted straight into Telegram, Slack, or email.

## What's inside / 内容模块

| Module | Description | Docs |
| --- | --- | --- |
| `packages/market-pulse` | Scraper + brain pair that outputs the flagship bilingual brief. | [README](packages/market-pulse/README.md) |
| `packages/creator-consensus` | Turns creator signals into a bilingual consensus snapshot. | [README](packages/creator-consensus/README.md) |
| `packages/sim-portfolio-100k` | Maintains a $100K macro-aware simulation book + rebalance helper. | [README](packages/sim-portfolio-100k/README.md) |
| `docs/` | Architecture notes + weekly template. | [overview.en](docs/overview.en.md) / [overview.zh](docs/overview.zh.md) / [weekly template](docs/weekly-template.md) |
| `samples/` | Real output files you can compare against. | [README](samples/README.md) |
| `daily-updates/` | Drop zone for daily reports + portfolio snapshots. | [README](daily-updates/README.md) |

## Quick start / 快速开始

```bash
git clone https://github.com/chenyang0151/market-pulse-suite.git
cd market-pulse-suite
make market-pulse          # run the daily scraper + brain (TELEGRAM_TARGET optional)
make creator-consensus     # emit bilingual consensus brief
make sim-portfolio         # produce rebalance note from the $100K book
```

Dependencies: Python 3.10+, `uv`/`pip`, and optional OpenClaw CLI if you plan to re-use the Telegram sender.

## Demo / 示例

| Deliverable | Preview |
| --- | --- |
| Market Pulse brief | `samples/market-pulse-report-2026-03-03.md` （真实双语报告，可直接复制到 Telegram） |
| Creator Consensus | `samples/creator_consensus_sample.md` （自动化脚本输出） |
| $100K Rebalance note | `samples/rebalance-note.txt` （messaging-ready 交易建议） |
| Trade Plan (板块→结论→操作) | `daily-updates/trade-plans/2026-03-03-trade-plan.md` |

把任意一次运行的成品复制到 `daily-updates/reports/`、`daily-updates/positions/`、`daily-updates/trade-plans/`，就能形成「demo + 历史归档」；也可以使用下面的自动脚本。

## Automation toolkit / 自动化工具集

### 1. Trade plan generator

```bash
python3 tools/generate_trade_plan.py --date 2026-03-04 \
  --portfolio packages/sim-portfolio-100k/data/portfolio.json
```

- 读取 `packages/sim-portfolio-100k/data/trade_playbook.json` + 当前组合，输出 `daily-updates/trade-plans/<date>-trade-plan.md`。
- 可以在跑完 `daily.sh` 和 `rebalance.py` 后立即执行。

### 2. Auto-archive helper

```bash
python3 tools/archive_daily.py --date 2026-03-04 \
  --reports-dir ../data/market-pulse/reports \
  --portfolio-json ../data/market-pulse/portfolio.json \
  --trade-plan daily-updates/trade-plans/2026-03-04-trade-plan.md
```

- 寻找 `YYYY-MM-DD.md` 或 `market-pulse-YYYY-MM-DD.md`，复制到 `daily-updates/reports/`。
- 同时复制 portfolio（如需跳过可加 `--skip-portfolio`）与 trade plan（可选 `--trade-plan`）。

### 3. GitHub Release workflow

`/.github/workflows/daily-release.yml` 提供 `workflow_dispatch` 入口：

```
gh workflow run daily-release.yml -f date=2026-03-04
```

- 会校验 `daily-updates/` 下是否存在当日的 report / trade-plan / portfolio。
- 自动创建 `daily-<date>` tag + Release，并附上三个原始文件，方便对外分发 / SEO。

## Branding assets / 品牌素材

- Primary logo: `assets/branding/market-pulse-suite-logo.png`
- Generator prompt archives: `assets/branding/logo-set-1/`, `assets/branding/logo-set-2/`

## Roadmap / 后续打算

- [ ] Wire delivery helpers for Slack / email
- [ ] Publish structured API endpoints for Creator Consensus
- [ ] Turn the $100K simulation rules into a composable JSON schema for brokers

贡献欢迎（中英文都可）——提 Issue / PR 即可。
