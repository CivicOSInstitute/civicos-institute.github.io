#!/usr/bin/env bash
set -euo pipefail

cd /Users/AI-OPS/.openclaw/workspace

START_TS=$(date +%s)
TODAY=$(date +%F)
OUT_DIR="generated"
mkdir -p "$OUT_DIR"
HEALTH_JSON="$OUT_DIR/automation_health.json"
RUN_LOG="$OUT_DIR/ops_cycle_${TODAY}.log"

# macOS-compatible ISO timestamp
now_iso() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

declare -a STEP_NAMES=()
declare -a STEP_CMDS=()
declare -a STEP_STATUS=()
declare -a STEP_SEC=()

run_step() {
  local name="$1"
  shift
  local cmd=("$@")

  local t0=$(date +%s)
  echo "[$(now_iso)] START $name :: ${cmd[*]}" | tee -a "$RUN_LOG"

  if "${cmd[@]}" >>"$RUN_LOG" 2>&1; then
    local st="ok"
  else
    local st="error"
  fi

  local t1=$(date +%s)
  local dt=$((t1 - t0))
  echo "[$(now_iso)] END   $name :: status=$st duration=${dt}s" | tee -a "$RUN_LOG"

  STEP_NAMES+=("$name")
  STEP_CMDS+=("${cmd[*]}")
  STEP_STATUS+=("$st")
  STEP_SEC+=("$dt")
}

: > "$RUN_LOG"

echo "[$(now_iso)] OPS CYCLE BEGIN" | tee -a "$RUN_LOG"

run_step "auto_task_from_telegram" python3 scripts/auto_task_from_telegram.py
run_step "fetch_social_feeds" python3 scripts/fetch_social_feeds.py
run_step "social_autopilot" python3 scripts/social_autopilot.py
run_step "ops_morning_brief" python3 scripts/ops_morning_brief.py

END_TS=$(date +%s)
TOTAL_SEC=$((END_TS - START_TS))

# Emit JSON health summary
{
  echo "{"
  echo "  \"generated_at\": \"$(now_iso)\"," 
  echo "  \"date\": \"$TODAY\"," 
  echo "  \"total_seconds\": $TOTAL_SEC," 
  echo "  \"steps\": ["
  for i in "${!STEP_NAMES[@]}"; do
    comma=","
    if [ "$i" -eq "$((${#STEP_NAMES[@]} - 1))" ]; then comma=""; fi
    printf '    {"name":"%s","command":"%s","status":"%s","seconds":%s}%s\n' \
      "${STEP_NAMES[$i]}" "${STEP_CMDS[$i]}" "${STEP_STATUS[$i]}" "${STEP_SEC[$i]}" "$comma"
  done
  echo "  ]"
  echo "}"
} > "$HEALTH_JSON"

echo "[$(now_iso)] OPS CYCLE END :: total=${TOTAL_SEC}s" | tee -a "$RUN_LOG"
echo "$HEALTH_JSON"
