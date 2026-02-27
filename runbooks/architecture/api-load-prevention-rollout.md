# API Load Prevention Rollout (CivicOS OpenClaw)

## Objective
Reduce external API token usage and spend while preserving response quality for operations work.

## Targets (first 14 days)
- API token reduction: **>= 60%**
- API spend reduction: **>= 50%**
- Quality parity on sampled outputs: **>= 95%**
- Prompt-cache hit rate (eligible calls): **>= 90%**
- P95 latency (mixed workload): **<= baseline + 10%**

## Architecture Controls
1. **Tier 0 Local Route**
   - Complexity score < 0.35 => local model only
2. **Tier 1 Semantic Cache**
   - Similarity >= 0.88 and within TTL => return cached response
3. **Tier 2 API Route with Compression**
   - Compress context before API dispatch
4. **Budget Governor**
   - Hard stops and soft alerts at router level

## Hard Guardrails (No quality disruption)
- Never cache/compress high-stakes tasks (security, policy, legal-sensitive, irreversible actions)
- On low confidence from classifier/compressor: auto-escalate to full-context API path
- Cache invalidation on source changes (policy file/version hash change)
- Human review required for low-confidence high-impact outputs

## Rollout Plan

### Phase 0 — Instrumentation (Day 0-1)
Owner: Ops (Burt)
- Add per-call telemetry fields:
  - task_id, route_tier, classifier_score, cache_hit, compression_ratio, input_tokens, output_tokens, cost_usd, latency_ms, quality_flag
- Capture baseline for 24h with no routing changes

Exit criteria:
- Baseline report generated
- Telemetry completeness > 98%

### Phase 1 — Shadow Mode (Day 2-4)
Owner: Ops + QA
- Run router decisions in parallel but do not enforce
- Compare recommended route vs actual route
- Build confusion matrix for classifier

Exit criteria:
- False-low-complexity rate < 5%
- Proposed thresholds calibrated

### Phase 2 — Controlled Enforcement (Day 5-9)
Owner: Ops
- Enforce Tier 0/Tier 1 for low-risk task classes only
- Keep Tier 2 fallback always available
- Enable budget soft alerts at 80%

Exit criteria:
- Quality parity >= 95% on random sample
- API token reduction >= 40% early signal

### Phase 3 — Full Enforcement (Day 10-14)
Owner: Ops
- Extend enforcement to broader task classes
- Enable hard budget caps and queueing
- Weekly threshold tuning

Exit criteria:
- Meets target metrics in "Targets"

## Fallback Matrix
- Local model timeout/error => Tier 2 API with compressed context
- Cache retrieval error => bypass cache and continue route
- Compression failure => send minimal safe raw context bundle
- Budget hard cap reached => queue non-critical tasks; escalate critical tasks with approval

## Weekly Governance
- Review top 20 escalations and misses
- Tune classifier thresholds by +/−0.05 max per week
- Update cache TTL by task family
- Publish one-page efficiency report

