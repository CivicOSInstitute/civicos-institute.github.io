# Subagent Assignment Matrix (Empirical Local Bench)

Updated: 2026-02-23  
Source benchmark: `generated/model_profiles_2026-02-23.json`

## Speed Summary (lower is better)
- **qwen2.5:14b** avg: **13.32s** (fastest)
- **mistral-small3.2:24b-instruct-2506-q4_K_M** avg: **24.78s**
- **qwen2.5-coder:32b-instruct-q3_K_L** avg: **36.36s**

## Routing Policy (Local-first + Codex 5.3 for critical tasks)

Hard rule:
- Any local-model task must route through `skills/ollama-agent-queue` (never direct `ollama run` in task scripts).
- If local queue fails/timeouts, escalate to API fallback.

### Default model for most subagents
- **qwen2.5:14b**
- Use for: operations, summaries, drafting, monitoring, report generation, first-pass analysis

### Coding-heavy / high-complexity code
- **qwen2.5-coder:32b-instruct-q3_K_L**
- Use for: root-cause debugging, non-trivial refactors, architecture/code-level reasoning
- Guardrail: only invoke when task is explicitly code-heavy or qwen14b fails first pass

### Quality second-opinion / rewrite pass
- **mistral-small3.2:24b-instruct-2506-q4_K_M**
- Use for: alternative framing, concise rewrite, consistency check

## Practical Assignment Matrix

| Task Type | Primary | Fallback 1 | Fallback 2 | Notes |
|---|---|---|---|---|
| Daily brief / ops summary | qwen2.5:14b (via queue) | mistral-small3.2:24b (via queue) | Codex 5.3 (Plus/API) | Optimize for speed |
| Research scan + synthesis | qwen2.5:14b (via queue) | mistral-small3.2:24b (via queue) | Codex 5.3 (Plus/API) | Escalate for strategic depth |
| Social copy draft batch | qwen2.5:14b (via queue) | mistral-small3.2:24b (via queue) | gpt-4o (API) | Use API for final polish |
| Browser automation planning | qwen2.5:14b (via queue) | qwen-coder:32b (via queue) | Codex 5.3 (Plus/API) | Coding model when selectors/scripts complex |
| Script writing / bugfix | qwen-coder:32b (via queue) | qwen2.5:14b (via queue) | Codex 5.3 (Plus/API) | Prefer coder model for non-trivial logic |
| Fast triage / inbox classification | qwen2.5:14b (via queue) | mistral-small3.2:24b (via queue) | — | Throughput-first |
| Financial/compliance messaging | qwen2.5:14b (via queue) | Codex 5.3 (Plus/API) | gpt-4o (API) | Human confirmation still required |
| High-stakes strategy / external commitments | Codex 5.3 (Plus/API) | GPT-4o (API) | Gemini (API) | Director review required before send |

## Subagent Spawn Defaults
- `research-*`, `brief-*`, `monitor-*` → `qwen2.5:14b`
- `code-*`, `debug-*`, `automation-*` → `qwen2.5-coder:32b-instruct-q3_K_L`
- `rewrite-*`, `second-pass-*` → `mistral-small3.2:24b-instruct-2506-q4_K_M`

## Escalation Triggers
Escalate from local to API model only if one or more are true:
1. Local output fails quality after one revision loop.
2. Time-critical blocker where local latency compounds delay.
3. High-stakes external-facing deliverable requiring top polish.

## Immediate Operational Change
For spawned subagents, set model explicitly per task type instead of defaulting every task to one model.
