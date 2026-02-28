#!/usr/bin/env bash
set -euo pipefail

# Smart sub-agent spawner using local-first model matrix
# Usage:
#   spawn_smart.sh "task description" [priority] [mode]
# Example:
#   spawn_smart.sh "debug stripe sync script" high run

TASK="${1:-}"
PRIORITY="${2:-normal}"
MODE="${3:-run}"

if [[ -z "$TASK" ]]; then
  echo "Usage: $(basename "$0") \"task description\" [low|normal|high] [run|session]"
  exit 1
fi

if [[ "$PRIORITY" != "low" && "$PRIORITY" != "normal" && "$PRIORITY" != "high" ]]; then
  echo "Invalid priority: $PRIORITY (expected low|normal|high)"
  exit 1
fi

if [[ "$MODE" != "run" && "$MODE" != "session" ]]; then
  echo "Invalid mode: $MODE (expected run|session)"
  exit 1
fi

ROOT="$HOME/.openclaw/workspace"
SELECTOR="$ROOT/scripts/select_model.py"
QUEUE_GUARD="$ROOT/scripts/local_queue_guard.py"

if [[ ! -f "$QUEUE_GUARD" ]]; then
  echo "Queue guard not found: $QUEUE_GUARD"
  exit 1
fi

# Pre-execution enforcement: block direct local model command payloads at launch time.
set +e
python3 "$QUEUE_GUARD" --context "spawn_smart" --command "$TASK" >/dev/null
CODE=$?
set -e
if [[ $CODE -ne 0 ]]; then
  if [[ $CODE -eq 42 ]]; then
    echo "Blocked by queue policy (exit 42): task contains direct local-model invocation."
    echo "Use queue path only: skills/ollama-agent-queue/scripts/integration_helper.py"
    exit 42
  fi
  echo "Queue guard check failed with exit code: $CODE"
  exit $CODE
fi

if [[ ! -f "$SELECTOR" ]]; then
  echo "Model selector not found: $SELECTOR"
  exit 1
fi

MODEL=$(python3 "$SELECTOR" "$TASK" --priority "$PRIORITY")

echo "Selected model: $MODEL"
echo "Task: $TASK"
echo "Mode: $MODE"

# Requires OpenClaw CLI on host
if ! command -v openclaw >/dev/null 2>&1; then
  echo "openclaw CLI not found in PATH."
  echo "Run this manually in OpenClaw chat instead:"
  echo "sessions_spawn(task=\"$TASK\", model=\"$MODEL\", mode=\"$MODE\")"
  exit 2
fi

# Use OpenClaw CLI if available
openclaw sessions spawn \
  --task "$TASK" \
  --model "$MODEL" \
  --mode "$MODE" \
  --cleanup keep
