#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/data/market-pulse/logs"
TIMESTAMP="$(python3 -c 'import datetime as dt; print(dt.datetime.now().isoformat())')"
LOG_FILE="$LOG_DIR/${TIMESTAMP}.log"
mkdir -p "$LOG_DIR"

VENV_DIR="$PROJECT_ROOT/.venv/market-pulse"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null

{
  echo "[${TIMESTAMP}] Market Pulse daily run start"
  echo "Installing scraper deps..."
  pip install -q -r "$PROJECT_ROOT/skills/market-pulse-scraper/requirements.txt"
  echo "Installing brain deps..."
  pip install -q -r "$PROJECT_ROOT/skills/market-pulse-brain/requirements.txt"

  echo "Collecting web data..."
  python "$PROJECT_ROOT/skills/market-pulse-scraper/market_pulse_scraper.py" collect-all

  echo "Synthesizing report..."
  python "$PROJECT_ROOT/skills/market-pulse-brain/market_pulse_brain.py" synthesize

  REPORT_PATH="$PROJECT_ROOT/data/market-pulse/reports/$(date +%F).md"
  ALT_REPORT_PATH="$PROJECT_ROOT/data/market-pulse/reports/market-pulse-$(date +%F).md"
  if [ ! -f "$REPORT_PATH" ] && [ -f "$ALT_REPORT_PATH" ]; then
    REPORT_PATH="$ALT_REPORT_PATH"
  fi
  if [ ! -f "$REPORT_PATH" ]; then
    echo "Report not found: $REPORT_PATH" >&2
    exit 1
  fi

  if [ -n "${TELEGRAM_TARGET:-}" ]; then
    echo "Sending Telegram delivery..."
    REPORT_DATE="$(date +%Y-%m-%d)"
    CAPTION="Market Pulse (${REPORT_DATE}) — full report attached as markdown."
    openclaw message send --channel telegram --target "$TELEGRAM_TARGET" --message "$CAPTION" --media "$REPORT_PATH"
    echo "Delivery complete"
  else
    echo "Delivery skipped (set TELEGRAM_TARGET to push via Telegram)."
  fi
  echo "[${TIMESTAMP}] Market Pulse daily run complete"
} | tee "$LOG_FILE"
