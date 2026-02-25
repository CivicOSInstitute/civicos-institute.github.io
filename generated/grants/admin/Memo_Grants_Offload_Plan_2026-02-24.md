# Memo: Grants Workflow Offload Plan (Ollama-First)
**Date:** 2026-02-24  
**From:** Burt Prime  
**To:** Nick Cerbone / CivicOS Grants

## Objective
Offload most grant operations to local Ollama-based sub-agents to reduce cloud dependency, increase throughput, and maintain daily momentum.

## Scope (Immediate)
1. Daily grant sourcing and scraping
2. Opportunity qualification + fit scoring
3. Drafting first-pass LOIs/narratives/checklists
4. Deadline and next-action reporting

## Architecture
- **Primary local model:** `qwen2.5:14b`
- **Fallback local model:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
- **Controller:** main agent delegates repeatable work to local sub-agents
- **Output paths:** `Desktop/Grants/` + `workspace/generated/grants/`

## Workstreams
### A) Intake + Discovery
- Run daily source pulls (federal/state/foundation/local)
- Normalize outputs into opportunity cards
- Store in `01_Opportunities/`

### B) Qualification
- Rank by: mission fit, eligibility, award size, complexity, deadline urgency
- Label: `Pursue / Watch / Drop`
- Save score sheets in `01_Opportunities/`

### C) Draft Production
- Generate first drafts for shortlisted grants:
  - Problem statement
  - Program narrative
  - Outcomes/metrics
  - Budget assumptions
- Store active work in `02_Applications/`

### D) Reporting
- Daily summary report with:
  - New opportunities
  - Priority applications
  - Deadlines in next 30 days
  - 24-hour action plan
- Save to `04_Reports/`

## Timeline
- **Tonight:** baseline structure + sub-agent spawned + first production run
- **Within 24h:** first full daily report + prioritized queue
- **Within 72h:** reusable templates + stable local-agent routing

## Success Criteria
- >=80% grants workflow executed by local models
- Daily report generated automatically
- Shortlist always current with deadlines and next actions
- At least 2 high-fit applications in active draft pipeline

## Risks / Controls
- **Risk:** source fetch failures -> **Control:** retry + error logging + alternate sources
- **Risk:** hallucinated details -> **Control:** source citation required in outputs
- **Risk:** quality variance -> **Control:** fallback model + review checklist
