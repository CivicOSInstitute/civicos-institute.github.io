# Memo: Production Execution Plan (Immediate)
**Date:** 2026-02-24  
**Owner:** Burt Prime

## Directive
Immediately run local-model sub-agent production for grants pipeline outputs.

## Deliverables Requested from Sub-Agent
1. `04_Reports/` daily grants report (top opportunities + watchlist + actions)
2. `01_Opportunities/` prioritized opportunity table with fit score and deadlines
3. `02_Applications/` draft packet stubs for top 3 opportunities
4. `00_Admin/` operating checklist for daily execution

## Model Policy
- Primary: `qwen2.5:14b` (Ollama)
- Fallback: `mistral-small3.2:24b-instruct-2506-q4_K_M` (Ollama)
- No cloud model unless explicitly authorized

## Output Quality Standard
- Ground every opportunity in a source URL
- Flag unknown deadlines as `unknown`
- Keep recommendations actionable and ranked by urgency/fit

## Completion Signal
Sub-agent returns:
- File manifest (created/updated)
- Short execution summary
- Next 24-hour actions
