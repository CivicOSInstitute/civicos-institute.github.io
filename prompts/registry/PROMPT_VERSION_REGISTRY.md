# Prompt Version Registry

Status: Active
Owner: Burt Prime

## Purpose
Canonical registry for production prompts with versioning, changelog, and rollback references.

## Required fields per prompt
- Prompt ID
- Workflow
- Current Version
- Owner
- Effective Date
- Success Metric(s)
- Last Benchmark Result
- Rollback Version

## Registry

### PRM-GRANT-DAILY-SCAN
- Workflow: `grant_daily_local_scan`
- Current Version: `v1.0`
- Owner: Ops/Grants
- Effective Date: 2026-02-26
- Success Metrics: parseability, relevance, deadline extraction confidence
- Last Benchmark Result: pending formal benchmark card
- Rollback Version: `v0` (pre-registry inline prompt)

### PRM-TOOLCALL-PROBE
- Workflow: `local_model_toolcall_probe`
- Current Version: `v1.0`
- Owner: Ops/Platform
- Effective Date: 2026-02-26
- Success Metrics: strict JSON validity, schema pass rate, exec test pass
- Last Benchmark Result: active daily rollup
- Rollback Version: `v0` (pre-registry inline prompt)

## Change log template
- Date:
- Prompt ID:
- Old Version -> New Version:
- Why changed:
- Measured effect:
- Rollback needed? (Y/N):
