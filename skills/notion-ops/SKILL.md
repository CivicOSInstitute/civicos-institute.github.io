---
name: notion-ops
description: Operate CivicOS Notion task database from terminal: create, list, and route ops tasks with consistent fields.
---

# notion-ops

Use this skill when you need to create or query CivicOS operations tasks in Notion.

## Required environment

- `NOTION_TOKEN` (internal integration token)
- `NOTION_DB_ID` (Tasks database id)

## Scripts

- `scripts/notion_task_create.sh`
- `scripts/notion_task_list.sh`
- `scripts/notion_phase2_sync.py`
- `scripts/notion_phase2_reconcile.sh`

## Workflow

1. Confirm env vars are set.
2. Create tasks with standardized properties:
   - Name
   - Status
   - Priority Level
   - Channel
   - Due Date
3. Query action queues (`today`, `p1`, `all`) for execution planning.

## Commands

Create task:

```bash
./scripts/notion_task_create.sh \
  --title "Follow up with Brent in 2–3 weeks" \
  --status "Not started" \
  --priority "P1" \
  --channel "Direct" \
  --due "2026-03-10"
```

List today queue:

```bash
./scripts/notion_task_list.sh --view today
```

Run Phase 2 sync (task dashboard -> Notion create/update):

```bash
./scripts/notion_phase2_reconcile.sh
```

## Edge cases

- If Notion returns `validation_error`, inspect property names via:

```bash
curl -s -X GET "https://api.notion.com/v1/databases/$NOTION_DB_ID" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" | jq '.properties | keys'
```

- If token leak occurs, rotate token and update env var immediately.
