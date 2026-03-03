#!/bin/bash
# AI Router - Route all requests through Llama 3.1 8B first
# Usage: ai-route "your prompt here"
# Or: echo "prompt" | ai-route

PROMPT="${1:-$(cat)}"

if [ -z "$PROMPT" ]; then
    echo "Usage: ai-route 'your prompt'"
    echo "   or: echo 'prompt' | ai-route"
    exit 1
fi

# Route through classifier
RESULT=$(python3 ~/.openclaw/workspace/skills/model-router/scripts/ai-router.py "$PROMPT")
export RESULT_JSON="$RESULT"

# Parse result
ROUTE=$(echo "$RESULT" | grep '"route"' | cut -d'"' -f4)
MODEL=$(echo "$RESULT" | grep '"model"' | cut -d'"' -f4)
REASON=$(echo "$RESULT" | grep '"reason"' | cut -d'"' -f4)
COST=$(echo "$RESULT" | grep '"cost"' | cut -d'"' -f4)

echo "=== AI Router Decision ==="
echo "Route: $ROUTE"
echo "Model: $MODEL"
echo "Reason: $REASON"
echo "Cost: $COST"
echo ""

if [ "$ROUTE" = "local" ]; then
    echo "=== Local Execution ($MODEL) ==="
    # Avoid double-running the local model: ai-router.py already executed and returned output.
    python3 - <<'PY'
import json, os
result = json.loads(os.environ.get('RESULT_JSON', '{}'))
print((result.get('output') or '').strip())
PY
else
    echo "=== API ESCALATION REQUIRED ==="
    echo "Model: $MODEL"
    echo ""
    echo "To execute with API:"
    echo "  openclaw message send --channel telegram --target 8334496229 --message 'ESCALATE: $MODEL | $PROMPT'"
fi
