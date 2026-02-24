#!/usr/bin/env bash
set -euo pipefail

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

if [[ -n "$DUE" ]]; then
  DUE_JSON=$(jq -n --arg d "$DUE" '{date:{start:$d}}')
else
  DUE_JSON='{"date":null}'
fi

PAYLOAD=$(jq -n \
  --arg db "$NOTION_DB_ID" \
  --arg title "$TITLE" \
  --arg status "$STATUS" \
  --arg priority "$PRIORITY" \
  --arg channel "$CHANNEL" \
  --argjson due "$DUE_JSON" '
{
  parent: {database_id: $db},
  properties: {
    Name: {title: [{text: {content: $title}}]},
    Status: {status: {name: $status}},
    "Priority Level": {select: {name: $priority}},
    Channel: {select: {name: $channel}},
    "Due Date": $due.date
  }
}')

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
