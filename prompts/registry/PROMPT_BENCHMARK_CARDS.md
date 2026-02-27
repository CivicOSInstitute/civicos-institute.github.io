# Prompt Benchmark Cards

Use one card per prompt version change before promotion.

## Card Template
- Prompt ID:
- Workflow:
- Old Version:
- New Version:
- Date:
- Owner:
- Test Set (>=10 tasks):
- Metrics:
  - Parseability pass rate:
  - Output quality score:
  - Latency median/p95:
  - Failure rate:
- Result: PASS / FAIL
- Decision: Promote / Keep Experimental / Rollback
- Rollback Version:
- Notes:

---

## Initial Card — PRM-GRANT-DAILY-SCAN v1.0
- Prompt ID: PRM-GRANT-DAILY-SCAN
- Workflow: grant_daily_local_scan
- Old Version: v0 (inline)
- New Version: v1.0 (registry-managed)
- Date: 2026-02-26
- Owner: Ops/Grants
- Test Set (>=10 tasks): pending execution
- Metrics:
  - Parseability pass rate: pending
  - Output quality score: pending
  - Latency median/p95: pending
  - Failure rate: pending
- Result: PENDING
- Decision: Keep Experimental until card complete
- Rollback Version: v0
- Notes: card created as mandatory gate artifact.
