---
name: donor-stewardship
description: Continuous donor relationship stewardship with live CRM read access and approval-gated writes. Handles gift acknowledgments, lapse prevention, major gift briefings, and portfolio health dashboarding under strict privacy controls.
---

# donor-stewardship

## Intent
Provide continuous, intelligent donor stewardship for CivicOS via live CRM integration with a strict read/intelligence vs write/action boundary.

Modes:
1. Gift acknowledgment
2. Lapse prevention
3. Major gift intelligence briefing
4. Portfolio health dashboard

## CRM access constraints (hard)
- Read access: allowed per `civicos-config.json` CRM config.
- Write access: only after explicit queue approval.
- Never hardcode credentials; read from config/env.
- Enforce API rate limit: max 60 CRM calls/hour.
- Retry failed CRM API calls up to 3 times with exponential backoff, then alert Architecture.
- Log every CRM read query to `./data/crm/query-log-YYYY-MM-DD.json`.
- Log every attempted write to `./data/crm/write-log-YYYY-MM-DD.json`.

## Privacy + security hard limits
1. Minimum-necessary-data principle per task.
2. No donor data persistence beyond task scope except minimal queue artifacts.
3. No individual donor data in Telegram bodies (first name + tier + queue ID only).
4. No individual donor records to Gemini tier (absolute prohibition).
5. Donor data processing: local models first; Codex only where explicitly assigned.
6. If a record appears to identify a minor, stop processing and escalate.
7. Read/write separation enforced where CRM supports split keys.

## Model assignment matrix
| Operation | Model | Fallback |
|---|---|---|
| CRM query construction | Mistral Small local | Qwen 14B |
| Donor record parsing/extraction | Qwen 14B local | Codex |
| Ack drafting Tier 3/4 | Qwen 14B local | Codex |
| Ack drafting Tier 1/2 | Qwen 14B local | Codex |
| Lapse prevention drafts | Qwen 14B local | Codex |
| Major gift briefing | Codex | Qwen 14B |
| Portfolio dashboard aggregation | Qwen 14B local | Codex |
| CRM write-back formatting | Mistral Small local | Qwen 14B |

## Mode 1 — Gift acknowledgment
Trigger:
- Poll every 30 min (or webhook preferred), detect new gifts where:
  - `acknowledgment_sent = false`
  - `gift_date >= today - 3 days`

Steps:
1. Pull minimal donor fields + relevant giving/interaction history.
2. Pull gift fields: amount/date/campaign/type/note.
3. Classify gift tier:
   - Tier 1: first-ever gift
   - Tier 2: upgrade gift (higher than prior max)
   - Tier 3: loyal renewal (2+ consecutive years)
   - Tier 4: standard recurring/installment/mid-level renewal
4. Any gift > $500: escalate to major-gift treatment priority.
5. Draft letter rules:
   - Preferred name fallback to first_name
   - Include amount/date
   - Include concrete impact tied to config programs
   - Ban phrases:
     - "Your generous donation"
     - "Thank you for your generous support"
     - "We couldn't do it without you"
   - Length: Tier 3/4 <=200 words; Tier 1/2 <=300 words
   - Signature from config staff roster
6. Write queue artifact to `./data/queue/pending/ack-[donor_id]-[YYYY-MM-DD].md` with YAML schema in references.
7. Notify Burt direct with queue ID + first name + amount + tier only.
8. On explicit approval, send and write back to CRM:
   - `acknowledgment_sent=true`
   - `acknowledgment_date=today`
   - `last_contact_date=today`

## Mode 2 — Lapse prevention
Trigger:
- Daily at 07:00

Find donors matching:
- 9–11 months since last gift and gave prior year
- 11–13 months since last gift (imminent)
- 6–8 months for major donor (lifetime >$1,000 OR any gift >$500)
- recurring installment overdue >14 days

Actions:
- 9–11 mo: gentle reconnection draft (no hard ask)
- 11–13 mo: personalized re-engagement with soft ask
- recurring overdue: payment-update assistance draft
- major-donor imminent risk: escalate Burt direct

Push summary block for morning brief:
- acknowledgment queue pending
- lapse imminent
- lapse 60-90 day window
- recurring payment issues
- major donor attention needed

## Mode 3 — Major gift intelligence briefing
Trigger:
- On-demand request by donor name

Output (Burt direct only):
1. Relationship snapshot
2. What they care about
3. The conversation plan (ask range + talking points + avoid list)
4. Action after call

No group-channel delivery.

## Mode 4 — Portfolio health dashboard
Trigger:
- Monday 07:45

Output aggregated metrics only (no individual records):
- acquisition, retention, revenue, major donor counts, recurring, acknowledgment queue, pipeline
- leadership-only delivery to Burt direct

Auto-council trigger:
- retention <55% OR YTD revenue <60% of budget at midyear
- trigger council framing with portfolio data

## Integrations
- ops-daily-brief: include stewardship summary block
- performance-reporter: include stewardship metrics without individual records
- council-of-advisors: trigger on defined deterioration conditions
- knowledge-indexer (future): index PII-stripped briefing patterns

## Approval queue + command handling
Acknowledge queue schema and commands are defined in `references/templates.md`.
Approval commands:
- `APPROVE ack-[id]`
- `EDIT ack-[id] [instruction]`
- `HOLD ack-[id]`
- `REJECT ack-[id] [reason]`

## Non-trigger guardrails
Do not trigger this skill for grants, governance scheduling, social posting, cron debugging, or non-donor program analytics.

## References
- Templates + YAML schema: `references/templates.md`
- Test/eval suite: `references/test-cases.md`
