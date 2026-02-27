# WORKFLOW_V2_SPEC

Status: Active (Draft v1)
Owner: Burt Prime
Date: 2026-02-26

## Purpose
Operational standard for CivicOS workflow architecture: reliability-first, queue-governed, and promotion-gated.

## Scope
Applies to all automated workflows in this workspace, including cron jobs, queue tasks, model routing, and fallback behavior.

---

## 1) Lane Architecture (Mandatory)

### Lane A: `prod-critical`
Use for donor, grants, comms, monitoring, and decision support that affects daily operations.
- Priority: `high` or `urgent`
- Must have fallback behavior
- Must emit structured logs
- Must have rollback path

### Lane B: `experimental`
Use for pilots (e.g., llama.cpp/HF Qwen3.5), tests, and architecture experiments.
- Priority: `normal` unless explicitly promoted
- Must never block Lane A
- Must include experiment tag + success criteria

Rule: If congestion occurs, experimental tasks are deferred first.

---

## 2) Queue Contract (Mandatory)

All local model work must route through:
- `skills/ollama-agent-queue/scripts/integration_helper.py`
- or `skills/ollama-agent-queue/scripts/queue_manager.py`

Required queue payload fields:
- `agent_id`
- `calling_skill`
- `model`
- `priority`
- `system_prompt`
- `user_prompt`
- `max_tokens`
- `callback`

Prohibited:
- Direct `ollama run` from non-queue scripts
- Direct `http://localhost:11434/api/generate` outside queue manager

---

## 3) Routing Standard

### Default routing
- Local default generalist: `local/qwen-14b` (currently mapped to `qwen3:14b`)
- Local fallback: `local/mistral-small`
- Coding specialist: `local/qwen-coder-32b`
- Legacy route: `local/qwen2.5-14b`

### Cloud usage
Cloud model use is allowed only when:
1. Task class requires premium lane quality/speed, or
2. Local lane fails quality/reliability gate, or
3. Director explicitly requests.

All cloud usage should be logged with task class and reason.

---

## 4) Reliability Controls

Each workflow must define:
- Idempotency strategy (how duplicate runs are handled)
- Retry policy (count + backoff)
- Timeout policy
- Fallback path
- Output location and latest pointer
- Knowledge write artifact using `templates/WORKFLOW_KB_WRITE_TEMPLATE.md` for production-impacting changes

Minimum expected behavior:
- No silent failure
- No infinite retries
- No unbounded queue growth
- KB discipline checks pass (`scripts/workflow_kb_enforcer.py`) for active prod workflows

---

## 5) Promotion Gate (Model/Workflow Changes)

Before promoting a new model/server to default:

### Benchmark battery (required)
- 10 task set minimum across:
  - short response
  - medium synthesis
  - long planning
  - workflow-specific outputs (grants/comms/ops)

### Pass criteria
- Reliability: no regression in completion rate
- Latency: >=20% improvement OR justified parity with quality gain
- Quality: >=15% judged improvement on approved rubric
- Cost/quota: within approved envelope
- Rollback: tested and documented

If any criterion fails -> remain experimental.

---

## 6) Observability & SLOs

Track daily:
- Queue depth and wait time (p50/p95)
- Workflow success/failure by job type
- Fallback rate (local->API/cloud)
- Model latency and tokens/sec
- Cron health and missed executions

Target SLOs:
- Prod workflow success >= 98%
- Prod queue p95 wait < 30s
- Urgent task start time < 10s when queue healthy

---

## 7) Security & Governance

- Treat auth boundary findings as hardening tasks, not loopholes.
- No secrets in prompts/logs.
- External messaging must not disclose exploit paths.
- Irreversible external actions still require explicit human approval.

---

## 8) Runbook: Pause / Resume / Rollback

### Pause queue
```bash
python3 skills/ollama-agent-queue/scripts/queue_manager.py pause
```

### Resume queue
```bash
python3 skills/ollama-agent-queue/scripts/queue_manager.py resume
```

### Status
```bash
python3 skills/ollama-agent-queue/scripts/queue_manager.py status-block
```

### Rollback routing
- Revert queue manager + model matrix commit
- Validate with smoke test (`local/qwen-14b` route)

---

## 9) Immediate Implementation Plan

### Phase 1 (48h)
- Enforce lane tagging in scripts
- Keep prod priorities high/urgent
- Verify queue pause/resume and alert flow

### Phase 2 (7d)
- Add unified daily SLO report
- Add explicit fallback reason logging
- Harden top 5 workflows for idempotency/retry

### Phase 3 (14–21d)
- Pilot non-Ollama local server in experimental lane only
- Run promotion benchmark battery
- Promote only if gates pass
