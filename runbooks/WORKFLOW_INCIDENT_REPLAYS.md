# Workflow Incident Replays (Monthly Fire Drill)

## Scenarios
1. Queue congestion (p95 wait > 120s)
2. Provider outage (local queue unavailable)
3. Auth failure (cloud unauthorized)
4. Cron drift/missed runs

## Drill format
- Trigger condition
- Detection source
- Immediate response (first 10 min)
- Fallback path
- Recovery verification
- Postmortem note

## Scenario 1: Queue congestion
- Trigger: SLO alert shows p95 wait >= 120s
- Immediate: pause experimental workloads; keep prod-critical high/urgent only
- Verify: p95 < 30s for 3 consecutive checks

## Scenario 2: Local provider outage
- Trigger: queue status errors for local model route
- Immediate: activate approved API fallback for critical classes
- Verify: >=98% success restored

## Scenario 3: Cloud auth failure
- Trigger: unauthorized errors on cloud lane
- Immediate: route premium tasks to local fallback and log impact
- Verify: cloud lane recovery test passes

## Scenario 4: Cron drift
- Trigger: missing daily outputs by expected windows
- Immediate: run critical scripts manually, inspect crontab and logs
- Verify: next scheduled cycle passes
