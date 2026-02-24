#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/notion_env.sh"

usage() {
  cat <<USAGE
Usage:
  $0 --title "..." [--status "Not started"] [--priority "P2"] [--channel "Direct"] [--due YYYY-MM-DD]

Required env:
  NOTION_TOKEN
  NOTION_DB_ID
USAGE
}

TITLE=""
STATUS="Not started"
PRIORITY="P2"
CHANNEL="Direct"
DUE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE="$2"; shift 2;;
    --status) STATUS="$2"; shift 2;;
    --priority) PRIORITY="$2"; shift 2;;
    --channel) CHANNEL="$2"; shift 2;;
    --due) DUE="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

[[ -n "$TITLE" ]] || { echo "--title is required"; exit 1; }
[[ -n "${NOTION_TOKEN:-}" ]] || { echo "NOTION_TOKEN missing"; exit 1; }
[[ -n "${NOTION_DB_ID:-}" ]] || { echo "NOTION_DB_ID missing"; exit 1; }

DB_JSON=$(curl -sS -X GET "https://api.notion.com/v1/databases/$NOTION_DB_ID" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28")

if echo "$DB_JSON" | jq -e '.object=="error"' >/dev/null; then
  echo "$DB_JSON" | jq .
  exit 1
fi

prop_type() {
  local name="$1"
  echo "$DB_JSON" | jq -r --arg n "$name" '.properties[$n].type // "missing"'
}

NAME_T=$(prop_type "Name")
STATUS_T=$(prop_type "Status")
PRIORITY_T=$(prop_type "Priority Level")
CHANNEL_T=$(prop_type "Channel")
DUE_T=$(prop_type "Due Date")

if [[ "$NAME_T" != "title" ]]; then
  echo "Error: Name property must be title (found: $NAME_T)" >&2
  exit 1
fi

PROPS=$(jq -n --arg title "$TITLE" '{Name:{title:[{text:{content:$title}}]}}')

if [[ "$STATUS_T" == "status" ]]; then
  PROPS=$(echo "$PROPS" | jq --arg s "$STATUS" '. + {Status:{status:{name:$s}}}')
elif [[ "$STATUS_T" == "select" ]]; then
  PROPS=$(echo "$PROPS" | jq --arg s "$STATUS" '. + {Status:{select:{name:$s}}}')
fi

if [[ "$PRIORITY_T" == "select" ]]; then
  PROPS=$(echo "$PROPS" | jq --arg p "$PRIORITY" '. + {"Priority Level":{select:{name:$p}}}')
fi

if [[ "$CHANNEL_T" == "select" ]]; then
  PROPS=$(echo "$PROPS" | jq --arg c "$CHANNEL" '. + {Channel:{select:{name:$c}}}')
fi

if [[ -n "$DUE" && "$DUE_T" == "date" ]]; then
  PROPS=$(echo "$PROPS" | jq --arg d "$DUE" '. + {"Due Date":{date:{start:$d}}}')
fi

PAYLOAD=$(jq -n --arg db "$NOTION_DB_ID" --argjson props "$PROPS" '{parent:{database_id:$db},properties:$props}')

RESP=$(curl -sS -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  --data "$PAYLOAD")

if echo "$RESP" | jq -e '.object=="error"' >/dev/null; then
  echo "$RESP" | jq .
  exit 1
fi

echo "$RESP" | jq -r '.url'
