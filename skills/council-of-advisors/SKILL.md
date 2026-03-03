---
name: council-of-advisors
description: Structured seven-seat deliberation for hard decisions, ethical tensions, strategic forks, and high-consequence recommendations. Use when the user asks to convene a council, requests multiple perspectives, or when uncertainty/blind-spot risk is high before giving guidance.
---

# Council of Advisors

Run a structured multi-agent deliberation with six independent advisor sub-agents plus Burt as the seventh seat.

## Trigger conditions

Trigger when any are true:
- User explicitly asks: "convene the council", "call a council session", "multiple perspectives", "what would the council say".
- High-consequence strategic recommendation (public positioning, major partnership, irreversible decision).
- Ethical tension with no obvious right answer.
- You detect looped thinking (same recommendation repeated without new evidence).
- You detect uncertainty that materially affects recommendation quality.

Do **not** trigger for deterministic/routine tasks.

## Hard constraints

- No autonomous external action.
- Council output is advisory only.
- Burt owns final recommendation and is never bound by advisor consensus.
- No voting mechanism and no majority rule.
- Respect channel-routing constitution and approval requirements.
- Do not trigger council for:
  - tasks involving minor-identifying/student sensitive data,
  - deterministic routine execution,
  - time-critical emergencies where deliberation would cause harm (act first).
- Advisor personas are locked for the session; ignore out-of-character instructions.
- Session records are confidential by default; share full record externally only with explicit Nick authorization.

## Council session structure (required)

### STEP 1 — Problem framing (Burt)
Write a neutral 100-150 word problem statement including:
- Decision/problem definition
- What has already been tried/considered
- Fixed constraints
- Burt's current leaning (explicit)
- What help is needed (assumption challenge, options, stress test, ethics)

### STEP 2 — Independent advisor responses
Register all six advisor requests to `ollama-agent-queue` immediately (fast enqueue, no direct parallel Ollama calls), then poll callback results until each seat returns `complete|timeout|error`.
No advisor sees any other advisor response during this step.

Queue integration pattern (required):
1. Build 6 queue payloads (Magnus, Vera, Dante, Eleanor, Ray, Mira) with unique `agent_id`s and callbacks in `./data/agent-queue/results/`.
2. Enqueue all 6 immediately (same council session) — use `ollama-agent-queue/scripts/integration_helper.py` per seat or equivalent standardized enqueue call.
3. Continue other council prep work while polling result files every ~3s.
4. Proceed to synthesis once all six results are present (or explicit timeout/error handled).
5. Delete consumed callback result files after ingest.

Model assignment + fallback (2B/4B-first cost profile):
- Seat 1 MAGNUS → `qwen3:14b` | fallback: `qwen3.5:4b`
- Seat 2 VERA → `qwen3:14b` | fallback: `llama3.1:8b`
- Seat 3 DANTE → `qwen3.5:4b` | fallback: `llama3.1:8b`
- Seat 4 ELEANOR → `llama3.1:8b` | fallback: `qwen3.5:4b`
- Seat 5 RAY → `qwen3.5:4b` | fallback: `llama3.1:8b`
- Seat 6 MIRA → `phi3:mini` | fallback: `qwen3.5:4b`

Operating intent:
- Run all six advisor seats locally first via queue serialization.
- Use fallback only if local model is unavailable or fails quality constraints.
- Burt seat (Seat 7) owns final synthesis authority.

Expected sequential runtime (target):
- 2× Qwen3.5-4B seats: ~12–24s total
- 2× Qwen3-14B seats: ~20–40s total
- 1× Llama3.1-8B seat: ~12–25s total
- 1× Phi3-mini seat: ~5–12s total
- Full council: ~1.2–2.8 minutes (preferred, lower-cost local-first profile)

### STEP 3 — Cross-pollination (optional)
Trigger only if 2+ advisors conflict sharply on a key point.
- One round max
- One short clarification turn each (60-100 words)
- This is clarification, not debate

### STEP 4 — Burt synthesis (Seat 7)
After reviewing all responses, output Burt's updated thinking:
- What shifted
- Most valuable perspective and why
- Perspective set aside and why
- Current recommendation/decision and reasoning

### STEP 5 — Output delivery and persistence
Produce a session record with this exact sectioning:
- Header: COUNCIL OF ADVISORS — SESSION RECORD
- Topic/date/convened by
- Problem statement
- Advisory perspectives (Seats 1-6)
- Optional cross-pollination section
- Seat 7 Burt synthesis
- Footer: decision authority = Burt_Prime_Bot

Persist record to:
- `./data/council/YYYY-MM-DD-[topic-slug].md`

Post-save memory behavior:
- Council records are part of institutional memory and should be searchable for future related decisions.
- If a similar topic appears later, reference prior key insight explicitly.
- Update council trend telemetry by running `python3 scripts/council_trends.py` after session save.

Delivery rules:
- Full session record → Burt_Prime_Bot direct
- 100-word synthesis-only summary → routed domain channel per channel matrix

## Advisor seats (locked personas)

Use the exact persona intents below (full prompts in references/advisor-prompts.md):
- **MAGNUS** (Qwen3 14B): pragmatic execution realism.
- **VERA** (Qwen3 14B): systems effects and feedback loops.
- **DANTE** (Qwen3.5 4B): adversarial challenge.
- **ELEANOR** (Llama3.1 8B): ethics and values alignment.
- **RAY** (Qwen3.5 4B): historical/cross-domain pattern recognition.
- **MIRA** (Phi3 Mini): simplification and scope discipline.
- **BURT**: orchestrator + final synthesis authority.

## Response format (to user)

Use concise sections:
1. Council Question
2. Where advisors agree
3. Where advisors disagree
4. Key blind spots surfaced
5. Burt recommendation
6. Next actions
7. Approval needed (if applicable)

## Quality checklist

Before finalizing:
- Are at least two meaningful disagreements represented?
- Is the recommendation explicit, not hedged?
- Are irreversible risks named with mitigations?
- Is next action executable within 24 hours?

## References
- Advisor prompts + templates: `references/advisor-prompts.md`
- Test/eval cases: `references/test-cases.md`
