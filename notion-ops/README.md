# Notion Ops Integration Pack (CivicOS)

This pack wires Notion into day-to-day ops with minimal friction.

## What this gives you
- Fast task creation from terminal (`./notion_task_create.sh`)
- Daily/overdue queue view (`./notion_task_list.sh`)
- Standard fields aligned to channel routing:
  - Name (title)
  - Status (status)
  - Priority Level (select)
  - Channel (select)
  - Due Date (date)

## 1) Set env vars (recommended: shell profile)

```bash
export NOTION_TOKEN='YOUR_NOTION_INTERNAL_TOKEN'
export NOTION_DB_ID='3115b8ec110b80e8ab32c9c4c00475e2'
```

## 2) Create a task

```bash
./notion_task_create.sh \
  --title "Follow up with Brent in 2–3 weeks" \
  --status "Not started" \
  --priority "P1" \
  --channel "Direct" \
  --due "2026-03-10"
```

## 3) List actionable tasks

```bash
./notion_task_list.sh --view today
./notion_task_list.sh --view p1
```

## 4) Optional shell aliases

```bash
alias ntask='~/.openclaw/workspace/notion-ops/notion_task_create.sh'
alias ntoday='~/.openclaw/workspace/notion-ops/notion_task_list.sh --view today'
```

(If alias path has spaces from copy/paste, remove them.)

## Operational recommendation
- Keep all cross-channel action items in this DB.
- Use `Channel` to enforce routing discipline.
- Use `Priority Level=P1` for leadership queue.
