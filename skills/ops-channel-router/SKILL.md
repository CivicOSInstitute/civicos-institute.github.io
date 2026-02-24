---
name: ops-channel-router
description: Route operational updates to the correct CivicOS Telegram channels and create linked Notion tasks for follow-through.
---

# ops-channel-router

Use this skill for channel routing decisions and execution for CivicOS ops updates.

## Routing map

- Direct: `8334496229`
- Social Media: `-5225875596`
- Financial Ops: `-1003789422388`
- Architecture: `-5268730316`
- Grants: `-5217384569`
- YouTube: `-5232457391`
- Fundraising: `-1003756065473`
- Governance: `-5095027055`

## Workflow

1. Classify message domain (direct/social/finance/architecture/grants/youtube/fundraising/governance).
2. Send concise channel-specific message.
3. If action required, create linked Notion task via `notion-ops` script.
4. Report destination + task URL.

## Command pattern (manual fallback)

```bash
openclaw message send --channel telegram --target <chat_id> --message "..."
```

## Escalation rules

- Financial failure/variance >15%: route to Financial Ops + Direct.
- Grant deadline <7 days not submitted: route to Grants + Direct.
- Compliance past due: route to Governance + Direct.
- System failures persisting 2+ runs: route to Architecture + Direct.
