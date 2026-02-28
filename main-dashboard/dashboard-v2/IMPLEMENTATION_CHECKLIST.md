# Implementation Checklist

## Phase 1 — Scaffold
- [ ] Add `/v2` route in `main-dashboard/app.py`
- [ ] Add template `templates/dashboard_v2.html`
- [ ] Add style section for card grid + status chips

## Phase 2 — Data wiring
- [ ] Build loader that normalizes local sources into v2 JSON payload
- [ ] Add parser for `ops_morning_brief_latest.md`
- [ ] Add parser for automation health + cron summary

## Phase 3 — Alert logic
- [ ] Red/yellow/green risk resolver
- [ ] Missing owner/ETA detector
- [ ] Deadline urgency scoring (48h, 7d, 14d)

## Phase 4 — QA gates
- [ ] Module timestamps visible
- [ ] Empty/error states verified
- [ ] Mobile stack layout checked
- [ ] Compare v2 output to morning brief consistency

## Definition of done
- [ ] Top 3 actions visible immediately on load
- [ ] Red blockers always include owner + ETA
- [ ] Overnight failures show first actionable cause
