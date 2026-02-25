#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <calling_skill> <agent_id> <model> <priority> <system_prompt> <user_prompt> [max_tokens]"
  exit 1
fi

CALLING_SKILL="$1"
AGENT_ID="$2"
MODEL="$3"
PRIORITY="$4"
SYSTEM_PROMPT="$5"
USER_PROMPT="$6"
MAX_TOKENS="${7:-500}"

DIR="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$DIR/scripts/queue_manager.py" enqueue --payload-json "$(cat <<JSON
{
  \"calling_skill\": \"$CALLING_SKILL\",
  \"agent_id\": \"$AGENT_ID\",
  \"model\": \"$MODEL\",
  \"system_prompt\": \"$SYSTEM_PROMPT\",
  \"user_prompt\": \"$USER_PROMPT\",
  \"max_tokens\": $MAX_TOKENS,
  \"priority\": \"$PRIORITY\"
}
JSON
)"
