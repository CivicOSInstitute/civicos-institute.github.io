#!/bin/bash
set -euo pipefail

WORKDIR="/Users/AI-OPS/.openclaw/workspace/mission-control"
LOGDIR="$WORKDIR/logs"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/watchdog.log"

check_once() {
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  if curl -fsS --max-time 5 http://127.0.0.1:8765/ >/dev/null \
     && curl -fsS --max-time 5 http://127.0.0.1:8765/data/router-status.json >/dev/null; then
    echo "[$ts] OK" >> "$LOGFILE"
    return 0
  fi

  echo "[$ts] DOWN -> restarting" >> "$LOGFILE"
  cd "$WORKDIR"
  nohup python3 api_server.py >> "$LOGDIR/api_server.out.log" 2>&1 &
  sleep 4

  if curl -fsS --max-time 5 http://127.0.0.1:8765/ >/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RESTART_OK" >> "$LOGFILE"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RESTART_FAILED" >> "$LOGFILE"
  fi
}

# Run for ~3 hours (36 checks x 5 minutes)
for _ in $(seq 1 36); do
  check_once
  sleep 300
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Watchdog complete" >> "$LOGFILE"
