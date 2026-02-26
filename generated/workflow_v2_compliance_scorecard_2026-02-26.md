# Workflow V2 Compliance Scorecard (Top 5 Production Workflows)

Date: 2026-02-26
Evaluator: Burt Prime
Spec: `WORKFLOW_V2_SPEC.md`

## Workflows Reviewed
1. `scripts/run_ops_cycle.sh`
2. `scripts/grant_daily_local_scan.py`
3. `scripts/local_model_toolcall_probe.py`
4. `scripts/ops_morning_brief.py`
5. `scripts/donor_stewardship_runner.py`

## Summary
- **Compliant/Improved:** 5/5
- **Fully aligned with lane tagging:** 5/5
- **Atomic latest-pointer writes:** 2/2 applicable workflows updated
- **Overlap/idempotency guard added:** run_ops_cycle implemented lockfile guard

## Detailed Assessment

### 1) run_ops_cycle.sh
- Lane declared: ✅ (`prod-critical`)
- Overlap guard: ✅ (`generated/ops_cycle.lock`)
- Structured run logging: ✅
- Remaining gap: supervised persistent worker migration (outside this script)

### 2) grant_daily_local_scan.py
- Lane/workflow metadata in raw snapshot: ✅
- Queue local-first with fallback: ✅
- Atomic latest write: ✅
- Remaining gap: explicit retry/backoff counters per source fetch (future enhancement)

### 3) local_model_toolcall_probe.py
- Lane/workflow metadata in output: ✅
- Queue-first and API fallback: ✅
- Remaining gap: explicit budget tag on fallback route (future enhancement)

### 4) ops_morning_brief.py
- Lane/workflow metadata in generated brief: ✅
- Atomic latest pointer file: ✅
- Remaining gap: none critical

### 5) donor_stewardship_runner.py
- Lane/workflow metadata added: ✅
- Queue artifacts include workflow/lane metadata: ✅
- Remaining gap: optional idempotency key file for rerun dedupe in non-dry mode (future enhancement)

## Priority Next Actions
1. Add fallback reason taxonomy (`quality_fail`, `timeout`, `provider_unavailable`, `budget_guard`) to all API fallback paths.
2. Add retry/backoff policy object to grant/source fetch workflows.
3. Move queue processing from cron-only to supervised persistent worker + cron watchdog.
4. Add daily SLO rollup script (queue p95 wait, success rate, fallback rate).
