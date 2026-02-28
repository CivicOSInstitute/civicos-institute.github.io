# Data Schema + Source Mapping

## Normalized dashboard payload (proposed)
```json
{
  "generated_at": "ISO-8601",
  "risk_level": "red|yellow|green",
  "top_actions": [{"title":"","owner":"","eta":"","priority":""}],
  "snapshot": {
    "foundation": {},
    "funding": {},
    "communications": {},
    "operations": {},
    "pipeline": {},
    "reliability": {}
  },
  "deadlines": {
    "next_7_days": [],
    "next_14_days": []
  },
  "overnight": {
    "completed": [],
    "failed": []
  },
  "critical_path_30d": [],
  "pipeline_detail": {
    "board": [],
    "grants": [],
    "pilots": []
  }
}
```

## Current local source files
- `generated/ops_morning_brief_latest.md`
- `dashboard.md`
- `generated/automation_health.json`
- `main-dashboard/static/data/current_cron_jobs.csv`
- `generated/signals/phase3_signals_latest.md`

## Mapping notes
- Top actions: parse from morning brief section
- Overnight failures: cron/automation health + logs
- Deadlines: task tracker + brief extracted deadlines
- Reliability: cron success ratio + latest failure count
