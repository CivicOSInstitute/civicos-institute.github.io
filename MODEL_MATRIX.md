# Model Selection Matrix (Local-First Practical Policy)

Status: **Active**
Owner: Burt Prime
Updated: 2026-02-22

## Policy Goal
Use **local models as much as practical** while preserving execution quality and speed for high-impact tasks.

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
1. **Qwen** (`Qwen`) — default local generalist
2. **Mistral** (`Mistral`) — local fallback
3. **Qwen-Coder** (`Qwen-Coder`) — coding-heavy local, off-peak preferred

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
- `coding`, `automation`, `debug`, `infra` → **Codex**
- `research`, `scan`, `summarize` → **Qwen** first, escalate to **Gemini** if weak
- `draft`, `email`, `announcement` → **Qwen** first, escalate to **GPT-4o** for final polish
- `bulk/background` → **Qwen** / **Mistral**

## Escalation Trigger Checklist
Escalate from local if any true:
- Output quality fails once after revision prompt
- Task requires deep repo-wide bug root cause under time pressure
- User requests final production-grade polish immediately
- Context pressure exceeds practical local performance

## Operator Note
When spawning sub-agents, pass `model` explicitly to enforce this matrix.
