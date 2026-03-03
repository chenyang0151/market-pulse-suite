# Market Pulse Suite — 系统概览

整套方案每天（太平洋时间早晨）产出三份可直接投递到 Telegram / 邮件的内容：

1. **Market Pulse 日报**：宏观 + Creator Pulse + 共识/热点 + 交易想法，支持中英文双语。
2. **Creator Consensus**：跟踪 50+ 中英文创作者的情绪与提及方向，生成可复制的 briefing。
3. **10 万美元模拟盘**：根据前两份内容给出仓位分布、调仓逻辑与风险对冲建议。

## 架构

```text
YouTube + RSS + 新闻提要
          │
          ▼
skills/market-pulse-scraper (Python)
          │ 标准化 JSON
          ▼
skills/market-pulse-brain (Python)
          │ Markdown 报告
          ├──→ creator-consensus/generate_consensus.py（共识摘要）
          └──→ sim-portfolio-100k/rules（仓位 JSON）
```

调度脚本 `packages/market-pulse/scripts/daily.sh` 负责：

1. 初始化/刷新 Python venv。
2. 安装 scraper + brain 依赖。
3. 调用 `market_pulse_scraper.py collect-all` 收集数据。
4. 用 `market_pulse_brain.py synthesize` 生成双语报告。
5. （可选）把 Markdown 作为附件推送 Telegram，或接入自定义投递通道。

## 数据产物

| 路径 | 说明 |
| --- | --- |
| `data/market-pulse/raw/*.json` | 统一的抓取原始数据。 |
| `data/market-pulse/reports/*.md` | 最终发布用的 Markdown 报告。 |
| `packages/creator-consensus/creator_consensus.md` | 创作者共识概要。 |
| `packages/sim-portfolio-100k/data/portfolio.json` | 模拟盘实时仓位与策略。

## 延展方式

- 把 `daily.sh` 接入 cron / GitHub Actions，保证每天 07:30 PT 前出稿。
- 替换 Telegram 推送逻辑，改为 Slack、Email 或内部 CMS。
- 用自定义的 LLM 摘要 / 搜索索引刷新 `creator_signals.json`，覆盖更多平台源。
