# CivicOS Dashboard v2 — Spec

## Goal
Implement the settled **2-layer dashboard scaffold**:
1. **Executive Snapshot (single-screen)** for immediate strategic triage
2. **Morning Ops Brief (daily operational layer)** for execution depth

## Core Layout (Top to Bottom)
1. **Global Alert Bar (R/Y/G)**
   - Red: deadlines <48h with no owner, cron failures, or board-critical blockers
   - Yellow: overdue tasks >0, partial automation degradation
   - Green: no critical blockers

2. **Executive Snapshot Row (6 cards)**
   - Foundation Status (board seats, 501c3 status, fiscal sponsor)
   - Funding Pipeline (urgent deadlines, active/submitted apps, revenue)
   - Communications (Discord/Facebook/X automation status)
   - Operations Health (open/overdue tasks, cron health, backups)
   - Critical Path summary (next 30 days)
   - Health Check banner status (top blocking risk)

3. **Today Focus Panel**
   - Top 3 actions
   - Owner + ETA
   - “Do now” command links

4. **Morning Ops Brief Layer**
   - Deadlines <7 days (lead section)
   - Today’s priorities (critical path + top 3 actions)
   - Upcoming 14-day deadlines
   - Overnight activity summary (completions + failures)
   - Today’s schedule / cron windows
   - Pipeline status pulse (board, grants, pilots)

5. **Critical Path (30-day)**
   - Checklist with status chips: Not Started / In Progress / Blocked / Done

## Design Principles (settled)
- Top-down triage: red/yellow/green first, details second
- Decision-first layout: “What needs action now?” at top
- Owner + ETA orientation: every critical item maps to an owner
- Reliability visibility: automation failures surfaced beside strategic work
- Show source timestamp on each module

## Refresh Behavior
- Header cards: every 60–120s
- Deadline + pipeline modules: every 5–15m
- Manual refresh always available

## Initial Route Plan
- Add dedicated route in main dashboard app: `/v2`
- Keep v1 untouched until parity signoff

## Success Criteria
- User can identify top 3 actions in <20 seconds
- No blocker appears without owner/ETA field
- Morning brief and dashboard show same risk state
