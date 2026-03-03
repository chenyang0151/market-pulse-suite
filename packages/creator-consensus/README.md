# Creator Consensus Module / 创作者共识模块

This package turns multi-language creator coverage into a bilingual consensus brief.

## What it does

- normalizes channel metadata (`config/channels.yaml`)
- ingests structured sentiment + buzz metrics (`data-samples/creator_signals.json`)
- ships a bilingual Markdown brief via `generate_consensus.py`

## Quick start

```bash
cd packages/creator-consensus
python3 generate_consensus.py --out creator_consensus.md
```

Outputs live at `creator_consensus.md` and can be piped into Telegram, email, or a CMS.

## 输入结构（中文）
- `channels.yaml`：YouTube/播客清单（语言、频率、关注点）
- `creator_signals.json`：模型提取的热度、情绪、提及的股票

## Extending
- swap in your own signal extractor by keeping the JSON schema constant
- add new languages by templating `build_report` in `generate_consensus.py`
