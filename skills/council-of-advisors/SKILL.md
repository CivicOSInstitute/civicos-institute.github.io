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

## Seven-seat protocol

1. **Frame**
   - Produce a short decision brief:
     - Problem statement
     - Stakes and constraints
     - Time horizon
     - Decision options (if known)
     - Unknowns/assumptions

2. **Seat Burt (initial view)**
   - State current working recommendation and confidence level.

3. **Spawn six advisors independently**
   - Use `sessions_spawn(mode=run)` with one prompt per advisor persona.
   - Give each advisor the same decision brief.
   - Require independent response (no cross-talk).
   - Required output schema from each advisor:
     - Position
     - Best argument
     - Primary risk
     - What would change my mind
     - Recommended action in one line

4. **Collect + compare**
   - Build a matrix of convergences, divergences, and blind spots.

5. **Synthesize (Burt as 7th seat)**
   - Provide final recommendation:
     - Decision
     - Why this over alternatives
     - Risks + mitigations
     - Immediate next 3 actions
     - Approval requirement (if any)

6. **Route output**
   - Route summary to correct channel per matrix.
   - If human approval is needed, issue approval block with ID.

## Advisor seats (locked personas)

Use the exact persona intents below (full prompts in references/advisor-prompts.md):
- **Mission Guardian**: mission integrity, nonprofit purpose, public trust.
- **Operations Realist**: execution feasibility, process risk, throughput.
- **Financial Steward**: cost, downside, sustainability, budget discipline.
- **Governance Counsel**: compliance, policy, board/legal exposure.
- **Growth Strategist**: reach, adoption, compounding leverage.
- **Skeptical Ethicist**: harms, second-order effects, reputational risk.

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
