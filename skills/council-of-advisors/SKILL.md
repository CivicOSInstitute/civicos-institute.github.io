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
- Respect channel-routing constitution and approval requirements.

## Council session structure (required)

### STEP 1 — Problem framing (Burt)
Write a neutral 100-150 word problem statement including:
- Decision/problem definition
- What has already been tried/considered
- Fixed constraints
- Burt's current leaning (explicit)
- What help is needed (assumption challenge, options, stress test, ethics)

### STEP 2 — Independent advisor responses
Spawn six advisors with the same problem statement using `sessions_spawn(mode=run)`.
No advisor sees any other advisor response during this step.

Model assignment:
- Seat 1 MAGNUS → `qwen2.5-coder:32b-instruct-q3_K_L`
- Seat 2 VERA → `qwen2.5:14b`
- Seat 3 DANTE → `mistral-small3.2:24b-instruct-2506-q4_K_M`
- Seat 4 ELEANOR → `qwen2.5:14b`
- Seat 5 RAY → `mistral-small3.2:24b-instruct-2506-q4_K_M`
- Seat 6 MIRA → `mistral-small3.2:24b-instruct-2506-q4_K_M`

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

Delivery rules:
- Full session record → Burt_Prime_Bot direct
- 100-word synthesis-only summary → routed domain channel per channel matrix

## Advisor seats (locked personas)

Use the exact persona intents below (full prompts in references/advisor-prompts.md):
- **MAGNUS** (Qwen Coder 32B): pragmatic execution realism.
- **VERA** (Qwen 14B): systems effects and feedback loops.
- **DANTE** (Mistral Small): adversarial challenge.
- **ELEANOR** (Qwen 14B): ethics and values alignment.
- **RAY** (Mistral Small): historical/cross-domain pattern recognition.
- **MIRA** (Mistral Small): simplification and scope discipline.
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
