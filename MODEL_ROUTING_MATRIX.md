# MODEL_ROUTING_MATRIX.md

CivicOS Institute — AI Infrastructure Policy  
Version: 1.1  
Last updated: 2026-02-27

---

## Tier Definitions

| Tier | Label | Condition |
|------|-------|-----------|
| T0 | Local only | complexity < 0.35 |
| T1 | Cache return | similarity ≥ 0.88 and TTL valid |
| T2 | API path | complexity > 0.65 OR high-stakes class |
| T2 Hard Override | Forced API | security, legal-sensitive, irreversible actions, governance-critical outputs |

> Note: Complexity scoring thresholds (0.35 / 0.65) require a complexity classifier.  
> Status: **[TBD: complexity classifier]** — treat as heuristic until implemented.

---

## Router Rules (applied first)

- T0: complexity < 0.35 → local only
- T1: similarity ≥ 0.88 and TTL valid → cache return
- T2: complexity > 0.65 or high-stakes class → API path
- Hard override to T2: security, legal-sensitive, irreversible actions, governance-critical outputs

---

## Model Routing Matrix

| Task Type | Default Route | Primary Model | Fallback 1 | Fallback 2 | Quality Gate |
|-----------|--------------|---------------|------------|------------|--------------|
| Formatting, templating, extraction | Tier 0 (local) | qwen3:14b | qwen2.5:14b | Codex | schema/format validation |
| Code scaffolding, scripts, refactors (routine) | Tier 0 (local) | qwen2.5-coder:32b-instruct-q3_K_L | qwen3:14b | Codex | lint/tests pass |
| Policy lookup / repeated Q&A | Tier 1 (cache) | semantic cache hit | qwen3:14b regenerate | Codex | freshness + similarity threshold |
| Multi-file architecture decisions | Tier 2 (API + compression) | Codex (gpt-5.3-codex) | Kimi | Gemini | decision completeness checklist |
| Security/compliance review | Tier 2 (API, minimal compression) | Codex | GPT-4o | Gemini | high-stakes review required |
| Governance drafting (board/policy language) | Tier 2 (API + compression) | Codex | GPT-4o | Kimi | legal/policy rubric score |
| Fast summarization (internal) | Tier 0 (local) | mistral-small3.2:24b | qwen3:14b | Codex | factual spot-check |
| Cross-agent synthesis | Tier 2 (API + compression) | Codex | Kimi | GPT-4o | synthesis rubric + contradiction scan |
| Council seats (Magnus/Vera/etc.) | Local queue serialized | see Council Seat Map below | seat fallback per skill | Codex (seat-specific) | disagreement + risk surfaced |
| Time-sensitive low-risk ops reply | Tier 0 (local) | qwen3:14b | mistral-small3.2:24b | Codex | latency SLA + no critical risk |

---

## Budget / Quality Controls

- Auto-escalate to higher tier on:
  - low confidence
  - failed validation
  - stale cache
  - high-impact task class
- Never allow cache-only answer for high-stakes classes.
- Session log field required: record tier and model actually used per task for empirical threshold tuning.

---

## Council Seat Model Map

> Companion to the routing matrix row for Council sessions.  
> Seat 7 (Burt) always receives full prior six outputs — no compression.

| Seat | Persona | Primary Model | Fallback |
|------|---------|---------------|----------|
| 1 | Magnus | qwen2.5-coder:32b-instruct-q3_K_L | Codex |
| 2 | Vera | qwen3:14b (via local/qwen-14b route) | Codex |
| 3 | Dante | mistral-small3.2:24b-instruct-2506-q4_K_M | qwen3:14b |
| 4 | Eleanor | qwen3:14b (via local/qwen-14b route) | Codex |
| 5 | Ray | mistral-small3.2:24b-instruct-2506-q4_K_M | qwen3:14b |
| 6 | Mira | mistral-small3.2:24b-instruct-2506-q4_K_M | qwen3:14b |
| 7 | Burt (synthesis authority) | Orchestrator seat (no fixed model mandate) | N/A |
