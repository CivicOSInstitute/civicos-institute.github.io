# 6AM Proactivity & Productivity Brief (OpenClaw Environment)

Generated: 2026-02-23 00:55 EST  
Scope: improve assistant proactivity/productivity between now and morning using **current installed/local tools only** (no new third-party installs tonight).

---

## Executive Summary

The highest-leverage path is to formalize a lightweight **ops loop** around tools you already have:
1. Capture actionable Telegram messages into tasks (`scripts/auto_task_from_telegram.py`)  
2. Refresh content/news inputs (`scripts/fetch_social_feeds.py`)  
3. Build social draft queue (`scripts/social_autopilot.py`)  
4. Emit one consolidated operational brief (`scripts/ops_morning_brief.py`, added tonight)

This creates predictable momentum at low risk, reduces context-switching, and makes the assistant more proactive **without adding infrastructure**.

---

## Current State (Observed)

From local run (`generated/ops_morning_brief_2026-02-23.md`):
- Tasks total: 31
- Open overdue: 4
- Open due today: 3
- Open priority mix: High 10, Medium 10, Low 7
- Social queue for today exists
- Auto-captured Telegram tasks today: 0

Interpretation:
- The bottleneck is not idea generation; it is **daily triage + execution cadence**.
- Existing automations are useful but need one command-level orchestration and one reporting surface.

---

## Dedicated YouTube Scan (local-only via `yt-dlp`)

Method:
- Used installed `yt-dlp` flat search + local transcript tooling in `skills/youtube-summarizer/`.
- No external APIs/tools added.

### Queries scanned
- `openclaw automation workflow assistant`
- `AI executive assistant daily planning automation`
- `telegram bot task automation sqlite`
- `playwright browser automation ai agent`

### Representative videos reviewed (with transcript extraction + summary)
- OpenClaw use-cases video: `https://youtube.com/watch?v=LV6Juz0xcrY`
  - Artifacts: `generated/youtube_scan/openclaw_use_cases/*`
- OpenClaw workflow automation / cron-focused video: `https://youtube.com/watch?v=y4NBXPemAMo`
  - Artifacts: `generated/youtube_scan/openclaw_workflows/*`
- Playwright MCP browser-control video: `https://youtube.com/watch?v=2716IUeCIQo`
  - Artifacts: `generated/youtube_scan/playwright_mcp/*`

### Skill ideas extracted (adapted to current environment)
1. **Recurring ops cadence beats ad hoc prompting**
   - Reinforces daily trigger chains (capture → queue → report).
2. **Memory + explicit operating files improve agent consistency**
   - Reinforces use of structured generated briefs/checklists each morning.
3. **Browser automation should be snapshot-driven and scoped**
   - Use Playwright/canvas steps only when outcome requires web state; avoid unnecessary automation runs.
4. **Model/task routing discipline matters for cost + speed**
   - Continue using `scripts/select_model.py` + `spawn_smart.sh` patterns for heavier tasks.

---

## Top Opportunities (Prioritized)

## 1) Single-command Morning Ops Loop (Highest ROI)
**Opportunity:** eliminate manual sequencing and forgotten steps.  
**Implementation:** use one runner script to execute existing automations in order.

- Implemented tonight: `scripts/run_ops_cycle.sh`
  - Runs:
    - `python3 scripts/auto_task_from_telegram.py`
    - `python3 scripts/fetch_social_feeds.py`
    - `python3 scripts/social_autopilot.py`
    - `python3 scripts/ops_morning_brief.py`

**Expected impact:** faster startup, fewer dropped tasks, consistent daily momentum.

## 2) Operational Visibility Brief (High ROI)
**Opportunity:** make assistant proactively suggest next actions from local state.  
**Implementation:** produce one markdown briefing that fuses task load + queue readiness + local news signal.

- Implemented tonight: `scripts/ops_morning_brief.py`
- Output example: `generated/ops_morning_brief_2026-02-23.md`

**Expected impact:** better prioritization quality in first 10 minutes of day.

## 3) Tighten Telegram-to-Task Capture Rules (Medium ROI)
**Opportunity:** reduce missed actionable messages and false negatives.  
**Implementation steps:**
1. Expand actionable regex in `auto_task_from_telegram.py` for your language patterns.
2. Add optional tags by keyword (`fundraising`, `distribution`, `social`, etc.).
3. Add simple daily capture count threshold warning in morning brief.

**Expected impact:** cleaner inbox-to-execution pipeline.

## 4) Proactive Subagent Use Policy (Medium ROI)
**Opportunity:** avoid main-thread blocking for longer work.  
**Implementation steps:**
1. Define trigger rule: if task >10 minutes or multi-file analysis, spawn subagent.
2. Add standard prompt snippets for overnight research / scans.
3. Require report artifacts under `generated/` for all long runs.

**Expected impact:** better throughput with less operator waiting.

## 5) Controlled Browser Automation Queue (Selective ROI)
**Opportunity:** reserve browser automation for tasks that need authenticated or rendered state.  
**Implementation steps:**
1. Create explicit “browser-required” checklist before launching Playwright/canvas.
2. Write outcomes to `generated/` with timestamp for reproducibility.
3. Keep runs bounded (single objective per run).

**Expected impact:** lower token/time burn and fewer brittle flows.

---

## Risk & Safety Notes

1. **Over-automation risk**
   - Auto-running scripts can produce noisy drafts or stale tasks if unchecked.
   - Mitigation: morning brief includes state checks; keep human review gate before external publishing.

2. **Telegram ingestion risk**
   - False positives can create low-value tasks.
   - Mitigation: conservative regex + dedupe by `source_key` + daily review block.

3. **Operational drift risk**
   - Multiple scripts can diverge silently.
   - Mitigation: keep one runner (`run_ops_cycle.sh`) as canonical path and update it first.

4. **Security/privacy risk in automation outputs**
   - Generated summaries can include sensitive snippets.
   - Mitigation: store in workspace only; avoid auto-forwarding externally.

5. **YouTube-derived advice quality variance**
   - Creator content can be hype-heavy.
   - Mitigation: extracted only workflow primitives (cadence, memory discipline, scoped browser automation).

---

## What Was Implemented Tonight (Low-risk quick wins)

1. **New script:** `scripts/ops_morning_brief.py`
   - Aggregates local task DB + social queue + news presence
   - Produces actionable morning markdown brief

2. **New script:** `scripts/run_ops_cycle.sh`
   - One-command orchestration of existing daily automation chain

3. **Generated artifacts:**
   - `generated/ops_morning_brief_2026-02-23.md`
   - `generated/youtube_scan/openclaw_use_cases/*`
   - `generated/youtube_scan/openclaw_workflows/*`
   - `generated/youtube_scan/playwright_mcp/*`

---

## Prioritized Morning Checklist (6 AM)

1. Run:
   ```bash
   bash scripts/run_ops_cycle.sh
   ```
2. Open latest brief:
   - `generated/ops_morning_brief_YYYY-MM-DD.md`
3. Triage overdue + due-today tasks first (from brief counts).
4. Review social queue draft and publish/adjust manually.
5. If backlog remains high, spawn focused subagents for deep tasks.
6. Capture lessons learned in one short note for tomorrow’s brief tuning.

---

## Suggested Next Iteration (after morning)

- Add `--json` output mode to `ops_morning_brief.py` for machine-readable downstream automation.
- Add task-category heuristics to Telegram capture script.
- Add optional “stoplight score” (green/yellow/red) based on overdue count, due-today count, and queue readiness.
