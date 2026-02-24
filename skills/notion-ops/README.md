# notion-ops

Notion operations helper skill for CivicOS.

## Persistent env setup

Scripts auto-load `~/.openclaw/.env.notion`.

```bash
cat > ~/.openclaw/.env.notion <<'EOF'
NOTION_DB_ID_VALUE='3115b8ec110b80e8ab32c9c4c00475e2'
NOTION_TOKEN_VALUE='YOUR_NOTION_INTERNAL_TOKEN'
EOF
chmod 600 ~/.openclaw/.env.notion
```

## Commands

Create task:

```bash
./scripts/notion_task_create.sh \
  --title "Set weekly ops review cadence" \
  --status "Not started" \
  --priority "P1" \
  --channel "Architecture" \
  --due "2026-02-28"
```

List tasks:

```bash
./scripts/notion_task_list.sh --view today
./scripts/notion_task_list.sh --view p1
./scripts/notion_task_list.sh --view all
```

Reconcile dashboard tasks to Notion:

```bash
./scripts/notion_phase2_reconcile.sh
```
