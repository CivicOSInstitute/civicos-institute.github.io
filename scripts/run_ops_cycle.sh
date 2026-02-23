#!/usr/bin/env bash
set -euo pipefail

cd /Users/AI-OPS/.openclaw/workspace

python3 scripts/auto_task_from_telegram.py || true
python3 scripts/fetch_social_feeds.py || true
python3 scripts/social_autopilot.py || true
python3 scripts/ops_morning_brief.py
