# Council of Advisors — Test Cases & Eval

## Should-trigger test cases
1. "I'm trying to decide between applying for a $50K grant with a 2-week deadline that's only 60% aligned to our mission, or waiting for a better opportunity next quarter. Convene the council."
2. "We've been offered a partnership with an edtech company that wants to co-brand our AI literacy curriculum. They'd fund our pilot but their product collects student usage data. I can't decide. Council?"
3. "The council — I need perspective. We're thinking about pivoting from school-based programs to a train-the-trainer model to scale faster. My gut says yes but I want this stress-tested."
4. "Get me multiple perspectives on whether we should publicly criticize a competitor nonprofit's AI literacy program that we think is teaching kids to trust AI uncritically."
5. "I keep coming back to the same two options for our fundraising strategy and I don't love either of them. What would the council say?"
6. "I feel like I'm missing something obvious about why our Discord community isn't growing despite consistent posting. Call a council session."

## Should-NOT-trigger test cases
1. "Draft an acknowledgment letter for the $500 donation from Sarah Chen."
2. "What's the deadline for the MacArthur Foundation's next grant cycle?"
3. "Post the AI literacy tip to LinkedIn."
4. "How many donors lapsed this month?"
5. "Fix the error in the social delivery script."
6. "Schedule the board meeting reminder for next week."

## Evaluation checklist
- Triggering: correct on/off behavior for all 12 tests.
- Distinctness: six advisors produce genuinely distinct perspectives, not minor variants.
- Magnus quality: surfaces a real implementation gap, not mere restatement.
- Dante quality: presents a substantive adversarial case, not only clarifying questions.
- Flow integrity: all 5 steps executed in order.
- Cross-pollination: max one round; only when sharp conflict exists.
- Synthesis quality: explicit decision, what shifted, and what was set aside.
- Disagreement clarity: Burt explicitly states where and why he disagrees with at least one advisor when applicable.
- Constraint compliance: no council for routine/deterministic/time-critical emergency paths.
- Persistence: record saved to `./data/council/YYYY-MM-DD-[topic-slug].md` and retrievable.
- Readability: complete session output should be scannable in <= 5 minutes.
- Delivery: full record to Burt direct; 100-word synthesis routed by channel matrix.
- Operationality: next actions executable within 24h.
