# CivicOS Architecture — Working Context

Last updated: 2026-02-27
Owner: Burt Prime
Channel: Telegram `-5268730316`

## Mission
Maintain decision continuity and prevent context loss in high-volume architecture discussions.

## Current Priorities
1. Stabilize workflow compaction discipline in channel operations.
2. Keep architecture decisions discoverable and durable.
3. Reduce ambiguity between decisions vs discussion.

## Decision Log
### 2026-02-27
- Adopt message prefixes in channel operations: `DECISION:`, `ACTION:`, `BLOCKER:`, `FYI:`.
- Adopt rolling state snapshots every ~25–40 messages.
- Adopt durable write-back of finalized decisions into this file/memory.

## Open Questions
- Should we split architecture into topic threads by subsystem (routing, queue, observability, integrations)?
- Desired cadence for formal summary post: hourly vs milestone-based?

## Active Actions
- [ ] Post protocol message to channel and pin it.
- [ ] Start rolling summary format in-channel.
- [ ] Add nightly summary automation (optional, pending approval).

## Rolling Snapshot Template
### State Snapshot
- **Decisions (new):**
- **Open questions:**
- **Blockers:**
- **Next 3 actions:**
  1)
  2)
  3)
- **Owner + ETA:**

## Change Discipline
- Final decisions must be recorded here same day.
- Summaries should link back to this file path:
  `/Users/AI-OPS/.openclaw/workspace/runbooks/civicos-architecture-context.md`
