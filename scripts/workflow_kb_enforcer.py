#!/usr/bin/env python3
"""Enforce KB write discipline for production workflows.
Fails when no KB write exists for today's production changes.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

WS = Path('/Users/AI-OPS/.openclaw/workspace')
GEN = WS / 'generated'
KB_DIR = GEN / 'kb_writes'
KB_DIR.mkdir(parents=True, exist_ok=True)

# Production workflows requiring KB write when activity is present
WORKFLOWS = [
    'run_ops_cycle',
    'grant_daily_local_scan',
    'ops_morning_brief',
    'workflow_slo_rollup',
]


def has_activity_today(day: str) -> dict[str, bool]:
    activity = {w: False for w in WORKFLOWS}

    if (GEN / 'automation_health.json').exists():
        activity['run_ops_cycle'] = True
    if (GEN / 'grants' / 'grant-scan-latest.md').exists():
        activity['grant_daily_local_scan'] = True
    if (GEN / f'ops_morning_brief_{day}.md').exists() or (GEN / 'ops_morning_brief_latest.md').exists():
        activity['ops_morning_brief'] = True
    if (GEN / 'workflow_slo_rollup_latest.json').exists():
        activity['workflow_slo_rollup'] = True

    return activity


def main() -> int:
    day = datetime.now().strftime('%Y-%m-%d')
    activity = has_activity_today(day)

    missing = []
    for wf, active in activity.items():
        if not active:
            continue
        files = list(KB_DIR.glob(f'{day}_{wf}_*.md'))
        if not files:
            missing.append(wf)

    report = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'workflow': 'workflow_kb_enforcer',
        'lane': 'prod-critical',
        'date': day,
        'active_workflows': [w for w, a in activity.items() if a],
        'missing_kb_writes': missing,
        'pass': len(missing) == 0,
    }

    out = GEN / f'workflow_kb_enforcer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    out.write_text(json.dumps(report, indent=2))
    latest = GEN / 'workflow_kb_enforcer_latest.json'
    tmp = GEN / 'workflow_kb_enforcer_latest.tmp.json'
    tmp.write_text(json.dumps(report, indent=2))
    tmp.replace(latest)

    if missing:
        print('KB_ENFORCER_FAIL:', ','.join(missing))
        return 2

    print('KB_ENFORCER_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
