# CivicOS Dashboard v2 — Spec

## Goal
Single-screen executive triage + daily operational depth.

## Core Layout (Top to Bottom)
1. **Global Alert Bar (R/Y/G)**
   - Red: deadlines <48h with no owner, cron failures, or board-critical blockers
   - Yellow: overdue tasks >0, partial automation degradation
   - Green: no critical blockers

2. **Executive Snapshot Row (6 cards)**
   - Foundation Status
   - Funding Pipeline
   - Communications Throughput
   - Operations Health
   - Board/Grant/Pilot Pulse
   - System Reliability

3. **Today Focus Panel**
   - Top 3 actions
   - Owner + ETA
   - “Do now” command links

4. **Deadlines Panel (7-day + 14-day tabs)**
   - Sorted by urgency
   - Missing owner highlighted

5. **Overnight Activity Feed**
   - Completed jobs
   - Failed jobs with first error + affected workflow

6. **Critical Path (30-day)**
   - Checklist with status chips: Not Started / In Progress / Blocked / Done

7. **Pipeline Pulse**
   - Board recruitment
   - Grants pipeline
   - Pilot conversations

## Design Rules
- Decision-first: action blocks above diagnostics
- One glance for risk level
- Every red item must map to owner + ETA
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
