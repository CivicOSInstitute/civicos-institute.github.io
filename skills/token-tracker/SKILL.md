---
name: token-tracker
description: Router-centric efficiency tracker for API-load prevention. Tracks tier routing (T0/T1/T2), cache hit rate, compression ratio, quality pass rate, token budgets, and projected monthly usage from local telemetry JSONL.
---

# Token Tracker (Reconfigured)

This skill now tracks **router efficiency** instead of legacy provider-by-provider token logs.

Primary telemetry file:
- `/Users/AI-OPS/.openclaw/workspace/data/telemetry/router_telemetry.jsonl`

## Commands

### Log a routed task
```bash
token-tracker log \
  --task-id task-001 --tier T2 --classifier-score 0.76 --cache-hit false \
  --compression-ratio 0.18 --input-tokens 3200 --output-tokens 640 \
  --cost-usd 0.0081 --latency-ms 1430 --quality-flag pass
```

### Status (rolling window)
```bash
token-tracker status --hours 24
```

### Efficiency report
```bash
token-tracker report --days 14
token-tracker report --days 14 --json
```

### Budget caps
```bash
token-tracker budget --set-daily-cap 1000000 --set-monthly-cap 30000000 --set-alert-at 80
token-tracker budget --show
```

### Forecast
```bash
token-tracker forecast --days 14
```

## Tracked Metrics
- Tier distribution (T0/T1/T2)
- Cache hit rate
- Compression ratio
- Quality pass rate
- Token totals (input/output/combined)
- Effective API cost
- Latency average
- Budget utilization and threshold alerts

## Notes
- Legacy provider quota/rate-limit tracking is deprecated for this workflow.
- Use router telemetry + budget governance as the primary operational control plane.
