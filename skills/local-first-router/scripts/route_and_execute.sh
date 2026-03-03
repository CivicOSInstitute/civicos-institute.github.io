#!/bin/bash
# 100% Local-First Router Integration
# This script wraps ALL task execution to enforce local-first policy

TASK="$1"
if [ -z "$TASK" ]; then
    echo '{"error": "No task provided"}'
    exit 1
fi

# Run classification
RESULT=$(python3 ~/.openclaw/workspace/skills/local-first-router/scripts/local_router.py "$TASK")

# Extract routing decision
ROUTE=$(echo "$RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("route","local"))')
MODEL=$(echo "$RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("model","llama3.1:8b"))')

if [ "$ROUTE" = "escalate" ]; then
    echo "⚠️  API ESCALATION REQUIRED"
    echo "$RESULT" | python3 -m json.tool
    echo ""
    echo "To proceed with API, explicitly say: 'use API for this task'"
    exit 1
else
    # Execute with local model
    echo "🖥️  LOCAL EXECUTION: $MODEL"
    echo "$RESULT" | python3 -m json.tool
    echo ""
    echo "Executing with local model..."
    ollama run "$MODEL" "$TASK"
fi
