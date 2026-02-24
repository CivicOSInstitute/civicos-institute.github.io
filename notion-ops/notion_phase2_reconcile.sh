#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/notion_env.sh"

WORKSPACE="${WORKSPACE:-/Users/AI-OPS/.openclaw/workspace}"
OUT_DIR="$WORKSPACE/generated"
mkdir -p "$OUT_DIR"

STAMP=$(date +%Y%m%d_%H%M%S)
OUT_JSON="$OUT_DIR/notion_phase2_sync_${STAMP}.json"
OUT_MD="$OUT_DIR/notion_phase2_reconcile_${STAMP}.md"
OUT_LATEST="$OUT_DIR/notion_phase2_reconcile_latest.md"

python3 "$WORKSPACE/skills/notion-ops/scripts/notion_phase2_sync.py" | tee "$OUT_JSON"

CREATED=$(jq -r '.created' "$OUT_JSON")
UPDATED=$(jq -r '.updated' "$OUT_JSON")
TOTAL=$(jq -r '.total_tasks' "$OUT_JSON")
LINKED=$(jq -r '.linked' "$OUT_JSON")
TASK_DB=$(jq -r '.task_db' "$OUT_JSON")

cat > "$OUT_MD" <<EOF
# Notion Phase 2 Reconciliation

- Timestamp: $(date)
- Task DB: $TASK_DB
- Total tasks scanned: $TOTAL
- New Notion tasks created: $CREATED
- Existing links updated: $UPDATED
- Total linked tasks: $LINKED

## Result
Phase 2 sync completed successfully.
EOF

cp "$OUT_MD" "$OUT_LATEST"
echo "$OUT_MD"
