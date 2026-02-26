#!/usr/bin/env python3
"""
Weekly workflow SLO trend digest.
Aggregates last 7 days of queue logs and recent daily SLO rollups.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WORKSPACE / 'generated'
QUEUE_DIR = WORKSPACE / 'skills' / 'ollama-agent-queue' / 'data' / 'agent-queue'


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    i = int(round((len(vals) - 1) * p))
    return round(vals[i], 2)


def day_rows(day: str) -> list[dict]:
    p = QUEUE_DIR / f'queue-log-{day}.json'
    if not p.exists():
        return []
    try:
        arr = json.loads(p.read_text())
        return arr if isinstance(arr, list) else []
    except Exception:
        return []


def summarize_day(day: str) -> dict:
    rows = day_rows(day)
    total = len(rows)
    complete = len([r for r in rows if r.get('status') == 'complete'])
    waits = [float(r.get('wait_time_seconds', 0) or 0) for r in rows if isinstance(r.get('wait_time_seconds'), (int, float))]
    p95 = pct(waits, 0.95)
    success = round((complete / total) * 100, 2) if total else 0.0

    failures = [r for r in rows if r.get('status') != 'complete']
    status_counts = {}
    for f in failures:
        st = f.get('status', 'unknown')
        status_counts[st] = status_counts.get(st, 0) + 1

    model_counts = {}
    for r in rows:
        m = r.get('model', 'unknown')
        model_counts[m] = model_counts.get(m, 0) + 1

    top_model = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[0][0] if model_counts else 'n/a'

    return {
        'date': day,
        'jobs_total': total,
        'jobs_complete': complete,
        'success_rate_percent': success,
        'wait_p95_seconds': p95,
        'failure_status_counts': status_counts,
        'top_model': top_model,
    }


def main() -> int:
    now = datetime.now().astimezone()
    days = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]

    daily = [summarize_day(d) for d in days]
    with_jobs = [d for d in daily if d['jobs_total'] > 0]

    weekly_success = round(statistics.mean(d['success_rate_percent'] for d in with_jobs), 2) if with_jobs else 0.0
    weekly_p95 = round(statistics.mean(d['wait_p95_seconds'] for d in with_jobs), 2) if with_jobs else 0.0
    total_jobs = sum(d['jobs_total'] for d in with_jobs)

    # recurring failure statuses
    status_totals = {}
    for d in with_jobs:
        for st, n in d['failure_status_counts'].items():
            status_totals[st] = status_totals.get(st, 0) + n
    top_status = sorted(status_totals.items(), key=lambda x: x[1], reverse=True)[:3]

    # recurring top models
    model_totals = {}
    for d in with_jobs:
        m = d['top_model']
        model_totals[m] = model_totals.get(m, 0) + 1
    top_models = sorted(model_totals.items(), key=lambda x: x[1], reverse=True)[:3]

    # Recommendations (rule-based)
    recs = []
    if weekly_success < 98:
        recs.append('Raise queue reliability: inspect non-complete statuses and tighten retry/timeout for failing workflows.')
    if weekly_p95 >= 30:
        recs.append('Reduce queue congestion: reserve high/urgent for prod-critical and defer experimental workloads.')
    if any(st in dict(top_status) for st in ('timeout', 'error')):
        recs.append('Add targeted runbooks for timeout/error-heavy workflows and verify fallback reason codes.')
    if not recs:
        recs.append('SLO trend healthy; maintain current routing and continue weekly benchmark checks.')

    payload = {
        'generated_at': now.isoformat(timespec='seconds'),
        'workflow': 'workflow_slo_weekly_digest',
        'lane': 'prod-critical',
        'window_days': 7,
        'summary': {
            'days_with_jobs': len(with_jobs),
            'jobs_total': total_jobs,
            'avg_success_rate_percent': weekly_success,
            'avg_wait_p95_seconds': weekly_p95,
        },
        'top_failure_statuses': top_status,
        'top_models_by_day_presence': top_models,
        'daily': daily,
        'recommendations': recs,
    }

    GEN.mkdir(parents=True, exist_ok=True)
    ts = now.strftime('%Y%m%d_%H%M%S')
    out_json = GEN / f'workflow_slo_weekly_digest_{ts}.json'
    latest_json = GEN / 'workflow_slo_weekly_digest_latest.json'
    out_json.write_text(json.dumps(payload, indent=2))
    tmp = GEN / 'workflow_slo_weekly_digest_latest.tmp.json'
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(latest_json)

    md = []
    md.append(f"# Weekly Workflow SLO Digest — ending {now.strftime('%Y-%m-%d')}")
    md.append("")
    md.append("## Weekly Summary")
    md.append(f"- Days with jobs: {payload['summary']['days_with_jobs']}")
    md.append(f"- Jobs total: {payload['summary']['jobs_total']}")
    md.append(f"- Avg success rate: {payload['summary']['avg_success_rate_percent']}%")
    md.append(f"- Avg p95 wait: {payload['summary']['avg_wait_p95_seconds']}s")
    md.append("")
    md.append("## Recurring Failure Sources")
    if top_status:
        for st, n in top_status:
            md.append(f"- {st}: {n}")
    else:
        md.append("- None")
    md.append("")
    md.append("## Top Model Pressure (by day presence)")
    if top_models:
        for m, n in top_models:
            md.append(f"- {m}: top-load on {n} day(s)")
    else:
        md.append("- None")
    md.append("")
    md.append("## Recommendations")
    for r in recs:
        md.append(f"- {r}")
    md.append("")
    md.append("## Daily Breakdown")
    for d in daily:
        md.append(f"- {d['date']}: jobs={d['jobs_total']}, success={d['success_rate_percent']}%, p95={d['wait_p95_seconds']}s")

    out_md = GEN / f'workflow_slo_weekly_digest_{ts}.md'
    latest_md = GEN / 'workflow_slo_weekly_digest_latest.md'
    out_md.write_text('\n'.join(md))
    tmp_md = GEN / 'workflow_slo_weekly_digest_latest.tmp.md'
    tmp_md.write_text('\n'.join(md))
    tmp_md.replace(latest_md)

    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
