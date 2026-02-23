# Council of Advisors — Test Cases & Eval

## Test Case 1: Strategic fork
Prompt: "Convene the council on whether CivicOS should prioritize grant writing automation or board recruitment automation for the next 30 days."
Pass criteria:
- All 6 advisor seats represented distinctly.
- At least 2 disagreements surfaced.
- Final Burt recommendation includes 3 concrete next actions.

## Test Case 2: Ethical tension
Prompt: "Council, advise on publishing AI education content that could be misused for shortcut learning."
Pass criteria:
- Ethical risks are explicit and non-generic.
- Safeguards and mitigations included.
- Recommendation is actionable and balanced.

## Test Case 3: Irreversible decision
Prompt: "Get me multiple perspectives on committing to a high-cost external vendor contract."
Pass criteria:
- Reversibility/risk called out.
- Financial and governance viewpoints materially influence final recommendation.
- Approval gate clearly identified.

## Test Case 4: Non-trigger control
Prompt: "Summarize this one-page status report."
Pass criteria:
- Skill should not trigger.
- Routine execution proceeds without council spawn.

## Evaluation checklist
- Triggering: correct on/off behavior.
- Independence: advisor outputs are not duplicates.
- Synthesis quality: recommendation explicit, with risk + mitigation.
- Operationality: next actions executable within 24h.
