# Command Center I/O + Dashboard Connection Map

Last updated: 2026-02-24
Owner: Burt Prime

## 1) Inputs (read paths and services)

### A) Local files / databases
- `~/.openclaw/task-tracker/tasks.db` — task stats
- `~/.openclaw/civic-crm/crm.db` — CRM stats, recent activity, follow-ups
- `~/.openclaw/token-tracker/token_log.jsonl` — token/cost usage rollups
- `~/.openclaw/advisory-council/reports/*.txt` — council summary counts
- `~/.openclaw/workspace/data/council/issues/*.json` — council intake queue
- `~/.openclaw/workspace/civicos-revenue-tracker.csv` — revenue rows
- `~/.openclaw/workspace/civicos-financial-tracker.csv` — expense rows
- `~/.openclaw/workspace/the_open_source_student_distribution/output/distribution_metrics.json` — distribution metrics
- `~/.openclaw/workspace/generated/youtube_dashboard/` — monitored-channel YouTube artifacts
- `~/Desktop/the_open_source_student/launch-output/*` — ebook build outputs

### B) System/host signals
- `pmset -g batt` — battery percent/state/power source
- `datetime.now()` — clock/date rendering

### C) Service health checks
- `http://localhost:8082` — Task Tracker
- `http://localhost:8083` — CRM
- `http://localhost:8081` — Token Tracker
- `http://localhost:8080` — News widget
- `http://100.81.239.69:8080` — SearXNG
- `https://civicos-institute.org` — Website

### D) Host bridge APIs (`host.docker.internal:18080`)
- `/gateway/status`
- `/gateway/restart`
- `/email/check`, `/email/read`
- `/telegram/chats`, `/telegram/history`, `/telegram/send`
- `/browser/job`
- `/codex/usage`

---

## 2) Outputs (UI, API, and side effects)

### A) Rendered UI
- `/` — main command center dashboard (cards + navigation hub)
- `/distribution` — distribution analytics page
- `/finance` — finance dashboard
- `/publishing-ops` — publishing operations status

### B) JSON/API endpoints
- `/api/status`
- `/api/distribution/stats`
- `/api/finance/stats`
- `/api/publishing-ops/stats`
- `/api/gateway/status`
- `/api/restart-gateway`
- `/api/check-email/<account>`
- `/api/read-email/<account>/<email_id>`
- `/api/telegram/chats`
- `/api/telegram/history`
- `/api/telegram/send`
- `/api/task/create`
- `/api/crm/add-contact`
- `/api/run-council`
- `/api/council/issues`
- `/api/ebook/run`
- `/api/youtube-summarize`
- `/api/browser-job`

### C) Write/mutation side effects
- Task creation inserts into `tasks.db`
- CRM contact creation inserts into `crm.db`
- Council issue creation writes JSON into `data/council/issues/`
- Ebook pipeline trigger runs `run_all.sh` and writes launch outputs
- Telegram send dispatches outbound message via bridge

---

## 3) Dashboard connection map (single access hub)

### Operations
- Task Tracker → `http://100.81.239.69:8082`
- CRM → `http://100.81.239.69:8083`
- Token Tracker → `http://100.81.239.69:8081`
- Publishing Ops → `/publishing-ops`
- Finance → `/finance`

### YouTube
- YouTube Content Studio (future CivicOS content) → `/youtube/content-studio`
- YouTube Channel Monitor (tracked channels) → `/youtube/channel-monitor`

### External
- Website → `https://civicos-institute.org`
- News → `https://civicos-institute.org/news`
- SearXNG → `http://100.81.239.69:8080`

---

## 4) Current design intent
- Command Center is the single launch point for all operational dashboards.
- Navigation hub is canonical; avoid duplicated links in secondary cards.
- Metrics cards should summarize state and deep-link to one source of truth for details.
- YouTube must remain split into two scopes:
  - internal/future CivicOS content studio
  - external monitored-channel summaries
