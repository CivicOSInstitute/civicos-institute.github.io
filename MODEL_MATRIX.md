# Model Selection Matrix (Local-First Practical Policy)

Status: **Active**
Owner: Burt Prime
Updated: 2026-02-26

## Policy Goal
Use **local models as much as practical** while preserving execution quality and speed for high-impact tasks.

## API Gate (Active)
Budget-conservation mode is active.
- API usage requires explicit approval token: `APPROVE API [task-id]`
- Non-critical tasks are local-only.
- Emergency reserve policy: 8% emergency + 8% planned critical ops.
- See: `generated/API_GATE_POLICY_ACTIVE.md`

## Current Constraints
- Kimi tokens are constrained this week → do **not** use by default.
- Use API models only when local models are likely to fail task quality/speed requirements.

## Routing Rules

### Tier 1 — Local First (default)
Use local by default for:
- Drafting, summarization, brainstorming
- Routine analysis
- Low-risk formatting/transforms
- Background tasks

Preferred:
1. **Qwen3-14B** (`local/qwen-14b` alias → `qwen3:14b`) — default local generalist
2. **Mistral** (`local/mistral-small`) — local fallback / second-opinion style
3. **Qwen-Coder** (`local/qwen-coder-32b`) — coding-heavy local, off-peak preferred
4. **Qwen2.5-14B** (`local/qwen2.5-14b`) — legacy fallback only

### Tier 2 — API Escalation (when needed)
Escalate from local when task is high-stakes or local quality is insufficient:
- Critical code changes, debugging blockers
- External-facing final copy with high consequences
- Complex reasoning requiring stronger model consistency

Preferred:
1. **Codex** (`Codex`) — technical execution + debugging
2. **GPT-4o** (`GPT-4o`) — polished writing/comms
3. **Gemini** (`Gemini`) — broad research/synthesis

### Tier 3 — Constrained/Explicit-Only
- **Kimi** (`Kimi`) — use only if explicitly requested until recharge

## Safety Overrides
Always require explicit human confirmation for:
- Financial commitments
- Irreversible external operations
- Public statements representing organization policy

## Sub-Agent Model Defaults
- `artifact architect`, `coding`, `automation`, `debug`, `infra` → **Codex**
- `research`, `scan`, `summarize` → **Qwen3-14B** first, escalate to **Gemini** if weak
- `email`, `inbox`, `simple tasks` → **Qwen3-14B** (local) by default
- `draft`, `announcement` → **Qwen3-14B** first, escalate to **GPT-4o** for final polish
- `bulk/background` → **Qwen3-14B** / **Mistral**

## Escalation Trigger Checklist
Escalate from local if any true:
- Output quality fails once after revision prompt
- Task requires deep repo-wide bug root cause under time pressure
- User requests final production-grade polish immediately
- Context pressure exceeds practical local performance

## Operator Note
When spawning sub-agents, pass `model` explicitly to enforce this matrix.

## Empirical Local Profiles (2026-02-26)
Benchmarked local Ollama models for speed + quality taste checks:
- `qwen3:14b` (via `local/qwen-14b`): new default; ~2x faster average vs qwen2.5 in current 3-case benchmark set
- `qwen2.5:14b` (via `local/qwen2.5-14b`): retained as legacy fallback route
- `mistral-small3.2:24b-instruct-2506-q4_K_M`: style-diverse fallback / second-opinion lane
- `qwen2.5-coder:32b-instruct-q3_K_L`: coding specialist, slower but useful for hard code tasks

Artifacts:
- `/tmp/qwen_benchmark_results_2026-02-26.json`
- `generated/subagent_assignment_matrix_2026-02-23.md` (superseded guidance in progress)

### Smart spawn helper
Use:
```bash
~/.openclaw/workspace/scripts/spawn_smart.sh "<task description>" [low|normal|high] [run|session]
```

Examples:
```bash
~/.openclaw/workspace/scripts/spawn_smart.sh "debug stripe api sync" high run
~/.openclaw/workspace/scripts/spawn_smart.sh "summarize inbox for today" normal session
```
