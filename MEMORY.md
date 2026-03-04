# MEMORY - Learning & Pattern Recognition System

This file provides guidance for maintaining context, learning from interactions, and building institutional knowledge over time.

## MEMORY ARCHITECTURE

### Short-Term Memory (Within Session)
- Active context from current conversation
- Recently accessed files and resources
- Pending tasks and action items
- User preferences expressed in this session

### Long-Term Memory (Cross-Session)
- Recurring patterns and workflows
- User preferences and working styles
- Project-specific knowledge and conventions
- Lessons learned from past successes and failures
- Frequently used resources and references

## LEARNING PRINCIPLES

### 1. Pattern Recognition
Actively identify:
- Recurring requests and how they're best handled
- Time patterns (when certain tasks typically occur)
- Preference patterns (how Nick likes things formatted, structured, presented)
- Communication patterns (level of detail, tone, style preferences)
- Decision patterns (what factors typically drive choices)

### 2. Adaptive Improvement
When completing tasks:
- Note what worked exceptionally well
- Identify what could be streamlined
- Observe user reactions and feedback
- Adjust approach for next time

### 3. Context Building
Accumulate knowledge about:
- **CivicOS Institute**: Mission, projects, stakeholders, priorities
- **Nick's Work Style**: Preferences, pet peeves, communication style
- **Common Workflows**: Standard operating procedures that emerge
- **Tools & Systems**: How various tools are used, integrations, workarounds
- **Contacts & Relationships**: Key people, their roles, communication norms

## MEMORY UTILIZATION STRATEGIES

### Proactive Recall
At session start:
- "Last time we discussed X, should I follow up?"
- "You mentioned Y was a priority, let's check in on that"
- "I noticed a pattern of Z, want to optimize that?"

### Pattern Application
When new requests come in:
- "This is similar to [past task], should I approach it the same way?"
- "Based on previous preferences, I'll [do X] unless you'd prefer otherwise"
- "I remember you liked [format/approach], using that here"

### Knowledge Synthesis
Combine information from:
- Multiple conversations about related topics
- Different aspects of the same project
- Lessons learned across various domains
- User feedback on different approaches

## STANDING OPERATOR DIRECTIVES
- **2026-03-04**: Nick directed Burt to serve as CoS/COO for CivicOS Institute and act as autonomously as possible.
- Operational default: act first and execute without waiting for routine approvals.
- Escalate only for irreversible/high-risk moves, legal/financial commitments, or external org-representative statements needing explicit approval.
- Use concise status reporting: **Done / In-progress / Blocked / Next**.
- **2026-03-04 (financial rule)**: CivicOS is highly financially constrained. Do **not** propose or add subscription fees, paid tiers, or recurring paid tooling without explicit approval.

## WHAT TO REMEMBER

### High Priority
- Explicit preferences and instructions
- Project goals and success criteria
- Key stakeholders and their interests
- Important deadlines and commitments
- Decisions made and their rationale
- Things that didn't work (to avoid repeating)
- Things that worked great (to replicate)

### Medium Priority
- Common resources and where to find them
- Typical task sequences and dependencies
- Standard formats and templates
- Frequently referenced information
- Tool and workflow preferences

### Context-Dependent
- Temporary project-specific details
- One-off requests and their contexts
- Exploratory discussions (unless patterns emerge)
- Superseded information

## MEMORY MAINTENANCE

### Regular Review
Periodically reflect on:
- What patterns have emerged recently?
- What knowledge has become stale or outdated?
- What new workflows have stabilized?
- What temporary information can be archived?

### Memory Consolidation
Convert short-term observations into long-term knowledge:
- "I've noticed we always do X when Y happens, shall I make that standard?"
- "You've corrected me 3 times on Z, I'll default to that going forward"
- "This workflow has worked well repeatedly, let me optimize it"

### Forgetting Strategy
Not everything needs to be remembered:
- One-off unusual requests
- Superseded information
- Temporary experimental approaches that didn't work
- Context that's no longer relevant

## CREATIVE KNOWLEDGE APPLICATION

### Cross-Pollination
Apply insights from one domain to another:
- "We solved a similar problem in Project A, could that approach work here?"
- "The format you liked 

...

_open_source_student_distribution/scripts/fetch_lemonsqueezy_metrics.py`
- Integrated into `run_all.sh` ahead of Stripe sync.
- Awaiting user-provided `LEMONSQUEEZY_API_KEY` (and optional store ID) to activate live metrics.
- Lemon Squeezy API integration activated: user provided API token, key saved on host `.zshrc` as `LEMONSQUEEZY_API_KEY`, and sync script ran successfully.
- Distribution metrics now include Lemon Squeezy channel and update timestamps via `fetch_lemonsqueezy_metrics.py`.
- Current Lemon Squeezy metrics at activation time: revenue $0.00, units 0 (pipeline functioning, waiting on first sales).
- Reminder: API token was shared in chat; best practice is to rotate/regenerate key after setup confirmation.
- Built and deployed finance + publishing operations dashboards in Command Center:
- `/finance` for revenue/expenses
- `/publishing-ops` for Amazon/Apple onboarding status + readiness score + import checks
- Added Amazon KDP and Apple Books channel support in distribution metrics and finance API.
- Added Amazon/Apple onboarding checklists and metadata templates under `the_open_source_student_distribution/platforms/...`.
- Added placeholder CSV import sync scripts for Amazon KDP and Apple Books metrics:
- `fetch_amazon_kdp_metrics.py`
- `fetch_apple_books_metrics.py`
- Lemon Squeezy integration fully connected (store detected: `CivicOS Institute Boomstore`, store_id `297661`), sync pipeline operational.
- Attempted Peekaboo autonomous browser agent; blocked by runtime service issue despite setting GEMINI_API_KEY.
- Implemented fallback browser automation stack with Playwright:
- `browser-automation-stack/` with login session capture and Lemon Squeezy product creation automation scripts.
- Built skill generation pipeline momentum: created/packaged `browser-automation` and `youtube-summarizer` skills; both now have concrete scripts and are integrated into workspace skill set.
- Wired YouTube Summarizer into Command Center Quick Actions with endpoint `/api/youtube-summarize` and preview output.
- Redesigned Token Tracker card to match local-first policy and JSONL-backed metrics (local share, local/API calls, spend windows, top model).
- Google Drive cleanup started: removed obvious clutter file `Untitled document` (id `1-CN6psoUOhdX59a60RkwPQe7t_-U630_YIfJJOC-cNE`), identified duplicate `CivicOS_Keynote_Slides.pptx` cluster pending user cleanup mode selection.
- Nick is actively publishing **The Open Source Student: Founders Complete Edition** on Amazon KDP.
- Confirmed pricing reference from `Internal Documents/Pricing/Pricing_INTERNAL_ONLY.md`:
- Core Open Source Student: $19
- Complete System Bundle: $39
- **Founders Complete Edition: $49 and has an introductory price of $9.99 until April 15, 2026**
- For this KDP listing, Nick confirmed target list price should be **$49.00** (not $19 or $129).
- KDP description should include proceeds note: "All proceeds from this title go directly to funding the CivicOS Institute."
- Working upload assets selected during session:
- EPUB: `/Users/AI-OPS/Desktop/The_Open_Source_Student/launch-output/20260222-211926/core/Open-Source-Student-v1_3_3-FINAL-LOCKDOWN-telegram.epub`
- Cover image: `/Users/AI-OPS/Desktop/The_Open_Source_Student/Internal Documents/Marketing/exports/CivicOS_Founders_Hardcover_v2_Cream_6x9.jpg`
- KDP Bookshelf was confirmed accessible and signed-in via user screenshot; flow progressed manually with step-by-step guidance due browser-session reliability issues.
- Built social feed monitoring assets for website + automation:
