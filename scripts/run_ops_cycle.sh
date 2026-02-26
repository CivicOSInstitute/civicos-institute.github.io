#!/usr/bin/env bash
set -euo pipefail

cd /Users/AI-OPS/.openclaw/workspace

START_TS=$(date +%s)
TODAY=$(date +%F)
OUT_DIR="generated"
mkdir -p "$OUT_DIR"
HEALTH_JSON="$OUT_DIR/automation_health.json"
RUN_LOG="$OUT_DIR/ops_cycle_${TODAY}.log"
STAMP=$(date +%Y%m%d_%H%M%S)
HEALTH_SNAPSHOT="$OUT_DIR/automation_health_${STAMP}.json"
LOCK_FILE="$OUT_DIR/ops_cycle.lock"
LANE="prod-critical"

# Idempotency/overlap guard: skip if another run is active.
if [[ -f "$LOCK_FILE" ]]; then
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SKIP ops cycle: lock exists ($LOCK_FILE)"
  exit 0
fi
trap 'rm -f "$LOCK_FILE"' EXIT
printf "%s\n" "$$" > "$LOCK_FILE"

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

echo "[$(now_iso)] OPS CYCLE BEGIN :: lane=$LANE" | tee -a "$RUN_LOG"

run_step "auto_task_from_telegram" python3 scripts/auto_task_from_telegram.py
run_step "fetch_social_feeds" python3 scripts/fetch_social_feeds.py
run_step "social_autopilot" python3 scripts/social_autopilot.py
run_step "ops_morning_brief" python3 scripts/ops_morning_brief.py
run_step "sync_grants_deadline_csv" python3 scripts/sync_grants_deadline_csv.py

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
cp "$HEALTH_JSON" "$HEALTH_SNAPSHOT"

echo "[$(now_iso)] OPS CYCLE END :: total=${TOTAL_SEC}s" | tee -a "$RUN_LOG"
echo "$HEALTH_JSON"
