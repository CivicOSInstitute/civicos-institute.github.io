# Workflow Control Planes

Status: Active
Date: 2026-02-26

Each production workflow must have a control plane entry.

## 1) grant_daily_local_scan
- Owner: Grants Ops
- Lane: prod-critical
- Inputs: web source snapshots
- Output: `generated/grants/grant-scan-*.md`
- Idempotency: timestamped outputs + atomic latest pointer
- Retry/Fallback: local queue -> API fallback
- Escalation: queue failures >1 day => architecture alert

## 2) donor_stewardship_runner
- Owner: Donor Ops
- Lane: prod-critical
- Inputs: CRM/mock donor data
- Output: generated JSON + queue markdown artifacts
- Idempotency: deterministic IDs by donor/date
- Retry/Fallback: safe-mode dry-run by default
- Escalation: unresolved donor queue >24h

## 3) ops_morning_brief
- Owner: Ops
- Lane: prod-critical
- Inputs: task DB + automation health + social queue
- Output: `generated/ops_morning_brief_*.md`
- Idempotency: daily timestamp + atomic latest pointer
- Retry/Fallback: N/A (non-model)
- Escalation: missing output by 07:00 local

## 4) local_model_toolcall_probe
- Owner: Platform Ops
- Lane: prod-critical
- Inputs: model route list
- Output: probe JSON latest
- Idempotency: timestamped outputs + latest pointer
- Retry/Fallback: local queue -> API fallback
- Escalation: schema pass <95%

## 5) workflow_slo_rollup / workflow_slo_alert / weekly_digest
- Owner: Platform Ops
- Lane: prod-critical
- Inputs: queue logs + generated artifacts
- Output: SLO reports + alerts
- Idempotency: timestamped outputs + latest pointers
- Retry/Fallback: best-effort (non-model)
- Escalation: two consecutive days target fail
