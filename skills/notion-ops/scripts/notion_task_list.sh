#!/usr/bin/env bash
set -euo pipefail

VIEW="today"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --view) VIEW="$2"; shift 2;;
    -h|--help)
      echo "Usage: $0 [--view today|p1|all]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

[[ -n "${NOTION_TOKEN:-}" ]] || { echo "NOTION_TOKEN missing"; exit 1; }
[[ -n "${NOTION_DB_ID:-}" ]] || { echo "NOTION_DB_ID missing"; exit 1; }

TODAY=$(date +%F)

case "$VIEW" in
  today)
    FILTER=$(jq -n --arg today "$TODAY" '{
      and: [
        {property:"Status",status:{does_not_equal:"Done"}},
        {or:[
          {property:"Due Date",date:{on_or_before:$today}},
          {property:"Due Date",date:{is_empty:true}}
        ]}
      ]
    }')
    ;;
  p1)
    FILTER='{"and":[{"property":"Priority Level","select":{"equals":"P1"}},{"property":"Status","status":{"does_not_equal":"Done"}}]}'
    ;;
  all)
    FILTER='{"property":"Name","title":{"is_not_empty":true}}'
    ;;
  *) echo "Invalid --view ($VIEW). Use today|p1|all"; exit 1;;
esac

PAYLOAD=$(jq -n --argjson f "$FILTER" '{filter:$f, page_size:50}')

curl -sS -X POST "https://api.notion.com/v1/databases/$NOTION_DB_ID/query" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  --data "$PAYLOAD" | \
jq -r '.results[] | [
  (.properties.Name.title[0].plain_text // "(untitled)"),
  (.properties.Status.status.name // "-"),
  (.properties["Priority Level"].select.name // "-"),
  (.properties.Channel.select.name // "-"),
  (.properties["Due Date"].date.start // "-")
] | @tsv'
